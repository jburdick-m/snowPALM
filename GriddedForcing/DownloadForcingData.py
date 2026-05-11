"""
DownloadForcingData.py
======================

Downloads PRISM (monthly precip + mean temperature) and NLDAS-2 (hourly
forcing) data that SnowPALM needs, using the current (post-2024) endpoints:

- PRISM: services.nacse.org/prism/data/get/us/4km/<var>/<yyyymm>?format=bil
         (the old ftp.prism.oregonstate.edu URLs were retired 2025-09-30)
- NLDAS-2: NLDAS_FORA0125_H.2.0 NetCDF-4 files
           (GRIB-1 distribution stopped 2024-08-01)

NLDAS authentication uses an Earthdata Bearer Token (set EARTHDATA_TOKEN env
var). Generate one at https://urs.earthdata.nasa.gov -> User Tokens.
Username/password Basic Auth is still supported as a fallback for legacy use.

Resumable: existing non-empty files are skipped; zero-byte leftovers are
deleted and retried. NLDAS downloads run on a 16-thread pool.

PRISM has a hard rate limit: same file twice per IP per 24 hours. The script
spaces PRISM requests by ~2 seconds.

The folder layout produced next to this script:

    GriddedForcing/
        PRISM/
            ppt/   <year>/   prism_ppt_us_25m_<yyyymm>.zip
            tmean/ <year>/   prism_tmean_us_25m_<yyyymm>.zip
        NLDAS/
            <year>/<doy>/    NLDAS_FORA0125_H.A<yyyymmdd>.<hh>00.020.nc

ONE-TIME SETUP
--------------
1. Earthdata account at https://urs.earthdata.nasa.gov, with the
   "NASA GESDISC DATA ARCHIVE" application authorized.

2. Generate an Earthdata User Token (sign in -> User Tokens -> Generate).
   Set it in the same shell you launch python from:

       set EARTHDATA_TOKEN=<your-long-token-string>          (Windows cmd)
       $env:EARTHDATA_TOKEN = "<your-long-token-string>"     (PowerShell)

USAGE
-----
       conda activate snowpalm
       cd path\\to\\GriddedForcing
       python DownloadForcingData.py
"""

import os
import time
import concurrent.futures
from datetime import date, timedelta
from pathlib import Path

import requests

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# -------------------- User configuration --------------------

# Water Year 2025 = Oct 2024 -> Sep 2025
START_YEAR, START_MONTH = 2024, 10
END_YEAR,   END_MONTH   = 2024, 10

PRISM_BASE = "https://services.nacse.org/prism/data/get/us/4km"
NLDAS_BASE = "https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/NLDAS_FORA0125_H.2.0"

EARTHDATA_TOKEN    = os.environ.get("EARTHDATA_TOKEN", "eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6ImpidXJkaWNrIiwiZXhwIjoxNzgzNzE2NjM2LCJpYXQiOjE3Nzg1MzI2MzYsImlzcyI6Imh0dHBzOi8vdXJzLmVhcnRoZGF0YS5uYXNhLmdvdiIsImlkZW50aXR5X3Byb3ZpZGVyIjoiZWRsX29wcyIsImFjciI6ImVkbCIsImFzc3VyYW5jZV9sZXZlbCI6M30.UwHWhTLJMiKjZis0bCc1TRPmGySAuCQd1BZcT0I-AhT27sCcH0No_uUoN39OQ8PHFLHdzcqB61ztnJv5KqoC9VldolltZzzUg8zOTNNbMEp-FbnjKywK_lKrGNsO5xEooY8P4etKw0PhiCChozkewaQ3WYr5W5CT9vOG9hWzQ94VwEKZa6S0Mi2qnbZQCNfjGKbse-0Isbvdsf6dlSVkBvqeY7S4HWNCTqCSIIZ5lbT--iSwpy4Pll-SXCr3oFG8PwmZHTY6dwC_vUspMdmfEVlFn3VsMJDkbj9N-XVoFvNB5vyIFrTnrqQdFTsHwW18diwxhjDejd1tU6evjM2YbA")
EARTHDATA_USERNAME = os.environ.get("EARTHDATA_USERNAME", "")
EARTHDATA_PASSWORD = os.environ.get("EARTHDATA_PASSWORD", "")

MAX_WORKERS    = 16    # NLDAS parallel downloads
PRISM_SLEEP_SEC = 2.0   # NACSE rate-limit cushion

# -------------------- Earthdata session helpers --------------------

class _EarthdataSession(requests.Session):
    """Session that keeps auth alive across the urs.earthdata.nasa.gov redirect chain."""
    AUTH_HOST = "urs.earthdata.nasa.gov"

    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        if "Authorization" in headers:
            original   = requests.utils.urlparse(response.request.url).hostname
            redirected = requests.utils.urlparse(prepared_request.url).hostname
            if (original != redirected
                    and redirected != self.AUTH_HOST
                    and original   != self.AUTH_HOST):
                del headers["Authorization"]
        return


def _make_nldas_session():
    s = _EarthdataSession()
    if EARTHDATA_TOKEN:
        s.headers.update({"Authorization": f"Bearer {EARTHDATA_TOKEN}"})
    elif EARTHDATA_USERNAME and EARTHDATA_PASSWORD:
        s.auth = (EARTHDATA_USERNAME, EARTHDATA_PASSWORD)
    else:
        raise SystemExit(
            "Set EARTHDATA_TOKEN (preferred) or EARTHDATA_USERNAME+EARTHDATA_PASSWORD "
            "as environment variables before running."
        )
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=MAX_WORKERS, pool_maxsize=MAX_WORKERS)
    s.mount("https://", adapter)
    return s


def _make_prism_session():
    # PRISM is open access; no auth.
    s = requests.Session()
    s.headers.update({"User-Agent": "SnowPALM-downloader/1.0"})
    return s


# -------------------- Helpers --------------------

def _last_day_of_month(d):
    nxt = d.replace(day=28) + timedelta(days=4)
    return nxt - timedelta(days=nxt.day)


def _download_to(session, url, outfile):
    """Returns (url, status). 'ok' on success, 'skip' if already present."""
    outfile = Path(outfile)
    if outfile.exists():
        if outfile.stat().st_size > 0:
            return (url, "skip")
        outfile.unlink()

    outfile.parent.mkdir(parents=True, exist_ok=True)

    try:
        r = session.get(url, stream=True, timeout=120)
    except Exception as e:
        return (url, f"network error: {e}")

    if r.status_code == 404:
        return (url, "404")
    if r.status_code == 401:
        return (url, "401 (token expired or not authorized for GESDISC app)")
    if r.status_code == 429:
        return (url, "429 rate limit")
    if r.status_code != 200:
        return (url, f"HTTP {r.status_code}")

    ctype = r.headers.get("Content-Type", "").lower()
    if "text/html" in ctype:
        return (url, "HTML response (auth flow likely broke)")

    tmp = outfile.with_suffix(outfile.suffix + ".part")
    try:
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(64 * 1024):
                if chunk:
                    f.write(chunk)
        tmp.replace(outfile)
    except Exception as e:
        if tmp.exists():
            tmp.unlink()
        return (url, f"write error: {e}")

    return (url, "ok")


# -------------------- URL planners --------------------

def _plan_nldas(start_d, end_d):
    cur = start_d
    while cur <= end_d:
        yyyy = f"{cur.year:04d}"
        mm   = f"{cur.month:02d}"
        dd   = f"{cur.day:02d}"
        doy  = (cur - date(cur.year, 1, 1)).days + 1
        ddd  = f"{doy:03d}"
        for hour in range(24):
            hh = f"{hour:02d}"
            fname = f"NLDAS_FORA0125_H.A{yyyy}{mm}{dd}.{hh}00.020.nc"
            url   = f"{NLDAS_BASE}/{yyyy}/{ddd}/{fname}"
            of    = Path("NLDAS") / yyyy / ddd / fname
            yield (url, str(of))
        cur += timedelta(days=1)


def _plan_prism_months(start_d, end_d):
    y, m = start_d.year, start_d.month
    while (y, m) <= (end_d.year, end_d.month):
        yield (y, m)
        m += 1
        if m == 13:
            m, y = 1, y + 1


# -------------------- Drivers --------------------

def download_prism(session):
    print(">>> PRISM")
    start_d = date(START_YEAR, START_MONTH, 1)
    end_d   = date(END_YEAR,   END_MONTH,   1)

    for var in ("ppt", "tmean"):
        for yy, mm in _plan_prism_months(start_d, end_d):
            yyyymm = f"{yy:04d}{mm:02d}"
            outfile = Path("PRISM") / var / f"{yy:04d}" / f"prism_{var}_us_25m_{yyyymm}.zip"
            if outfile.exists() and outfile.stat().st_size > 0:
                continue

            url = f"{PRISM_BASE}/{var}/{yyyymm}?format=bil"
            _, status = _download_to(session, url, outfile)
            if status == "ok":
                print(f"  ok    {outfile.name}")
            elif status == "skip":
                pass
            else:
                print(f"  FAIL  {var} {yyyymm}: {status}")
            time.sleep(PRISM_SLEEP_SEC)


def download_nldas(session):
    print(f">>> NLDAS  (parallel, {MAX_WORKERS} workers)")
    start_d = date(START_YEAR, START_MONTH, 1)
    end_d   = _last_day_of_month(date(END_YEAR, END_MONTH, 1)) + timedelta(days=2)
    tasks = list(_plan_nldas(start_d, end_d))

    ok = skips = 0
    errors = []

    iter_factory = (lambda it, total: tqdm(it, total=total, desc="NLDAS", unit="file")) \
                   if tqdm else (lambda it, total: it)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(_download_to, session, url, of) for (url, of) in tasks]
        for fut in iter_factory(concurrent.futures.as_completed(futures), len(futures)):
            url, status = fut.result()
            if status == "ok":      ok += 1
            elif status == "skip":  skips += 1
            else:                   errors.append((url, status))

    print(f"  ok={ok}  skipped={skips}  failed={len(errors)}")
    if errors:
        print("  First 10 failures:")
        for url, status in errors[:10]:
            print(f"    [{status}] {url}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more")


# -------------------- Main --------------------

def main():
    os.chdir(Path(__file__).resolve().parent)
    print(f"PRISM + NLDAS download for {START_YEAR}-{START_MONTH:02d} "
          f"through {END_YEAR}-{END_MONTH:02d}")
    print(f"Writing into: {os.getcwd()}")
    if tqdm is None:
        print("(install 'tqdm' for a progress bar:  pip install tqdm)")

    t0 = time.time()

    download_prism(_make_prism_session())
    download_nldas(_make_nldas_session())

    print(f"Done in {time.time() - t0:.0f} s.")


if __name__ == "__main__":
    main()
