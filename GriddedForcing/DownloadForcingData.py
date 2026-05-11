"""
DownloadForcingData.py
======================

Downloads PRISM (monthly precip + mean temperature) and NLDAS-2 (hourly
forcing) data that SnowPALM needs.

Standalone parallel downloader. NLDAS hourly downloads run on a thread pool
(16 workers by default), so a full water year finishes in ~5-10 minutes on a
decent connection instead of ~3 hours sequential.

Resumable: existing non-empty files are skipped; zero-byte leftovers are
deleted and retried.

The folder layout produced next to this script:

    GriddedForcing/
        PRISM/
            ppt/   <year>/   PRISM_ppt_*_4kmM*_<yyyymm>_bil.zip
            tmean/ <year>/   PRISM_tmean_*_4kmM*_<yyyymm>_bil.zip
        NLDAS/
            <year>/<doy>/    NLDAS_FORA0125_H.A<yyyymmdd>.<hh>00.002.grb

ONE-TIME SETUP
--------------
1. Earthdata account at https://urs.earthdata.nasa.gov, with
   "NASA GESDISC DATA ARCHIVE" approved under Applications -> Authorized Apps.

2. Set credentials in the SAME shell you launch python from. Windows cmd:
       set EARTHDATA_USERNAME=yourname
       set EARTHDATA_PASSWORD=yourpassword

USAGE
-----
       conda activate snowpalm
       cd path\\to\\GriddedForcing
       python DownloadForcingData.py
"""

import os
import sys
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
END_YEAR,   END_MONTH   = 2025, 9

PRISM_PPT_VERSION   = 3
PRISM_TMEAN_VERSION = 3

PRISM_BASE = "https://ftp.prism.oregonstate.edu/monthly"
NLDAS_BASE = "https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/NLDAS_FORA0125_H.002"

NLDAS_USERNAME = os.environ.get("EARTHDATA_USERNAME", "REPLACE_ME")
NLDAS_PASSWORD = os.environ.get("EARTHDATA_PASSWORD", "REPLACE_ME")

MAX_WORKERS = 16   # NLDAS parallel downloads. Reduce if you hit rate limits.

# -------------------- Earthdata-aware session --------------------

class _EarthdataSession(requests.Session):
    """Keeps Basic Auth alive across the urs.earthdata.nasa.gov redirect dance."""
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


def _make_session(user=None, pwd=None):
    s = _EarthdataSession()
    if user:
        s.auth = (user, pwd)
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=MAX_WORKERS, pool_maxsize=MAX_WORKERS)
    s.mount("https://", adapter)
    return s


# -------------------- Helpers --------------------

def _last_day_of_month(d):
    nxt = d.replace(day=28) + timedelta(days=4)
    return nxt - timedelta(days=nxt.day)


def _download_one(session, url, outfile):
    """Returns (url, status). 'ok' on success, 'skip' if already present."""
    outfile = Path(outfile)

    if outfile.exists():
        if outfile.stat().st_size > 0:
            return (url, "skip")
        outfile.unlink()

    outfile.parent.mkdir(parents=True, exist_ok=True)

    try:
        r = session.get(url, stream=True, timeout=60)
    except Exception as e:
        return (url, f"network error: {e}")

    if r.status_code == 404:
        return (url, "404")
    if r.status_code != 200:
        return (url, f"HTTP {r.status_code}")

    ctype = r.headers.get("Content-Type", "").lower()
    if "text/html" in ctype:
        return (url, "HTML returned (Earthdata auth or GESDISC app authorization?)")

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
    """Yield (url, outfile) for every NLDAS hour from start_d through end_d inclusive."""
    cur = start_d
    while cur <= end_d:
        yyyy = f"{cur.year:04d}"
        mm   = f"{cur.month:02d}"
        dd   = f"{cur.day:02d}"
        doy  = (cur - date(cur.year, 1, 1)).days + 1
        ddd  = f"{doy:03d}"
        for hour in range(24):
            hh = f"{hour:02d}"
            fname = f"NLDAS_FORA0125_H.A{yyyy}{mm}{dd}.{hh}00.002.grb"
            url   = f"{NLDAS_BASE}/{yyyy}/{ddd}/{fname}"
            of    = Path("NLDAS") / yyyy / ddd / fname
            yield (url, str(of))
        cur += timedelta(days=1)


def _plan_prism_months(start_d, end_d):
    """Yield (yyyy, mm) for every month from start_d.month through end_d.month inclusive."""
    y, m = start_d.year, start_d.month
    while (y, m) <= (end_d.year, end_d.month):
        yield (y, m)
        m += 1
        if m == 13:
            m, y = 1, y + 1


# -------------------- Drivers --------------------

def download_prism(session):
    """Sequential -- only ~24 files for a water year. Tries 'stable' then 'provisional'."""
    print(">>> PRISM")
    start_d = date(START_YEAR, START_MONTH, 1)
    end_d   = date(END_YEAR,   END_MONTH,   1)

    for var, version in (("ppt", PRISM_PPT_VERSION), ("tmean", PRISM_TMEAN_VERSION)):
        for yy, mm in _plan_prism_months(start_d, end_d):
            stem_fmt = f"PRISM_{var}_%s_4kmM{version}_{yy:04d}{mm:02d}_bil.zip"
            target_dir = Path("PRISM") / var / f"{yy:04d}"
            of_stable = target_dir / (stem_fmt % "stable")
            of_prov   = target_dir / (stem_fmt % "provisional")

            # Already have one or the other? skip.
            if (of_stable.exists() and of_stable.stat().st_size > 0) or \
               (of_prov.exists()   and of_prov.stat().st_size   > 0):
                continue

            url_stable = f"{PRISM_BASE}/{var}/{yy:04d}/{stem_fmt % 'stable'}"
            _, status = _download_one(session, url_stable, of_stable)
            if status == "ok":
                print(f"  ok    {of_stable.name}")
                continue
            if status == "skip":
                continue

            url_prov = f"{PRISM_BASE}/{var}/{yy:04d}/{stem_fmt % 'provisional'}"
            _, status2 = _download_one(session, url_prov, of_prov)
            if status2 == "ok":
                print(f"  ok    {of_prov.name} (provisional)")
            else:
                print(f"  FAIL  {var} {yy}-{mm:02d}: stable={status}  provisional={status2}")


def download_nldas(session):
    """Parallel -- ~8,800 files for a water year (+2 days for UTC offset padding)."""
    print(f">>> NLDAS  (parallel, {MAX_WORKERS} workers)")
    start_d = date(START_YEAR, START_MONTH, 1)
    end_d   = _last_day_of_month(date(END_YEAR, END_MONTH, 1)) + timedelta(days=2)

    tasks = list(_plan_nldas(start_d, end_d))

    ok = skips = 0
    errors = []
    iter_factory = (lambda it, total: tqdm(it, total=total, desc="NLDAS", unit="file")) \
                   if tqdm else (lambda it, total: it)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(_download_one, session, url, of) for (url, of) in tasks]
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
    if NLDAS_USERNAME == "REPLACE_ME" or NLDAS_PASSWORD == "REPLACE_ME":
        raise SystemExit(
            "Set EARTHDATA_USERNAME and EARTHDATA_PASSWORD as environment variables "
            "before running this script."
        )

    os.chdir(Path(__file__).resolve().parent)
    print(f"PRISM + NLDAS download for {START_YEAR}-{START_MONTH:02d} "
          f"through {END_YEAR}-{END_MONTH:02d}")
    print(f"Writing into: {os.getcwd()}")
    if tqdm is None:
        print("(install 'tqdm' for a progress bar:  pip install tqdm)")

    t0 = time.time()

    prism_session = _make_session()
    nldas_session = _make_session(NLDAS_USERNAME, NLDAS_PASSWORD)

    download_prism(prism_session)
    download_nldas(nldas_session)

    print(f"Done in {time.time() - t0:.0f} s.")


if __name__ == "__main__":
    main()
