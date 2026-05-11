"""
DownloadForcingData.py
======================

Downloads PRISM (monthly precip + mean temperature) and NLDAS-2 (hourly
forcing) data that SnowPALM needs, by wrapping the DownloadGriddedForcingData()
function in SnowPALM_model/Forcing.py.

This version uses Python's `requests` library instead of `wget`, so no extra
system tools are required. It monkey-patches Forcing.exec_cmd at import time
so the downloads go through Python; the repo's Forcing.py is not modified.

The file/folder layout it produces, next to this script:

    GriddedForcing/
        DownloadForcingData.py   <-- this file
        PRISM/
            ppt/   <year>/   PRISM_ppt_*_4kmM*_<yyyymm>_bil.zip
            tmean/ <year>/   PRISM_tmean_*_4kmM*_<yyyymm>_bil.zip
        NLDAS/
            <year>/<doy>/    NLDAS_FORA0125_H.A<yyyymmdd>.<hh>00.002.grb

ONE-TIME SETUP
--------------
1. NASA Earthdata account at https://urs.earthdata.nasa.gov
   After signing in, go to Applications -> Authorized Apps and approve
   "NASA GESDISC DATA ARCHIVE". Without that step NLDAS responses come back
   as HTML login pages instead of real .grb files.

2. Make credentials available to the script. Recommended: set environment
   variables in the SAME shell you launch python from, e.g. in Windows cmd:
       set EARTHDATA_USERNAME=yourname
       set EARTHDATA_PASSWORD=yourpassword
   (Or PowerShell:  $env:EARTHDATA_USERNAME = "yourname" )
   Avoid pasting credentials into the script and committing them.

3. Point SNOWPALM_REPO below at your local snowPALM clone.

USAGE
-----
From an activated snowpalm env, with this script's folder as the working dir:
    python DownloadForcingData.py

It is currently set up for Water Year 2025 (Oct 2024 through Sep 2025).
"""

import os
import sys
import shlex
import subprocess
from pathlib import Path

import requests

# -------- 1. Locate the snowPALM repo and import the downloader --------
SNOWPALM_REPO = Path(r"D:\path\to\snowPALM")   # <-- edit this on Windows

forcing_module_dir = SNOWPALM_REPO / "Model_Package" / "data" / "contents" / "SnowPALM_model"
if not forcing_module_dir.is_dir():
    raise FileNotFoundError(
        f"Cannot find {forcing_module_dir}.\n"
        "Edit SNOWPALM_REPO at the top of this script."
    )
sys.path.insert(0, str(forcing_module_dir))
import Forcing  # noqa: E402

# -------- 2. Replace the wget-based exec_cmd with a requests-based one --------

class _EarthdataSession(requests.Session):
    """requests.Session that keeps Basic Auth across NASA Earthdata redirects."""
    AUTH_HOST = "urs.earthdata.nasa.gov"

    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        if "Authorization" in headers:
            original = requests.utils.urlparse(response.request.url).hostname
            redirected = requests.utils.urlparse(prepared_request.url).hostname
            if (original != redirected
                    and redirected != self.AUTH_HOST
                    and original != self.AUTH_HOST):
                del headers["Authorization"]
        return


_session_cache = {}

def _get_session(user, pwd):
    key = (user, pwd)
    if key not in _session_cache:
        s = _EarthdataSession()
        if user:
            s.auth = (user, pwd)
        _session_cache[key] = s
    return _session_cache[key]


def _python_exec_cmd(cmd, Verbose):
    """Replacement for Forcing.exec_cmd. Routes wget commands through
    Python `requests`; passes everything else to the shell unchanged."""
    if not cmd.lstrip().startswith("wget"):
        if Verbose:
            print("Executing command (passthrough): " + cmd)
            subprocess.call(cmd, shell=True)
        else:
            subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return

    # Parse a wget-style command
    parts = shlex.split(cmd, posix=False)
    # shlex on Windows-style strings leaves outer quotes intact; strip them
    parts = [p[1:-1] if len(p) >= 2 and p[0] == p[-1] == '"' else p for p in parts]

    user = pwd = url = outfile = None
    i = 1  # skip 'wget'
    while i < len(parts):
        p = parts[i]
        if p == "--user":
            user, i = parts[i + 1], i + 2
        elif p == "--password":
            pwd, i = parts[i + 1], i + 2
        elif p == "-O":
            outfile, i = parts[i + 1], i + 2
        elif p.startswith("-"):
            i += 1
        else:
            url = p
            i += 1

    if url is None or outfile is None:
        print(f"  Could not parse wget command: {cmd}")
        return

    if Verbose:
        safe = f"GET {url} -> {outfile}"
        if user:
            safe += f" (auth as {user})"
        print(safe)

    sess = _get_session(user, pwd)
    try:
        r = sess.get(url, stream=True, timeout=60)
    except Exception as e:
        print(f"  Network error for {url}: {e}")
        return

    if r.status_code == 404:
        # Stable PRISM file may not exist yet -- caller will try the provisional URL
        return
    if r.status_code != 200:
        print(f"  HTTP {r.status_code} for {url}")
        return

    ctype = r.headers.get("Content-Type", "").lower()
    if "text/html" in ctype:
        print(f"  Server returned HTML for {url}; auth likely failed "
              f"or GESDISC app not authorized in your Earthdata profile.")
        return

    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    with open(outfile, "wb") as f:
        for chunk in r.iter_content(64 * 1024):
            if chunk:
                f.write(chunk)


Forcing.exec_cmd = _python_exec_cmd

# -------- 3. Work out of this script's folder --------
os.chdir(Path(__file__).resolve().parent)

# -------- 4. Parameters --------
pars = {}

pars["Verbose"] = True

# Water Year 2025 = Oct 2024 -> Sep 2025
pars["StartYear"]  = 2024
pars["StartMonth"] = 10
pars["EndYear"]    = 2025
pars["EndMonth"]   = 9

# PRISM monthly data
pars["PRISMDataLoc"]        = "https://ftp.prism.oregonstate.edu/monthly"
pars["prism_ppt_version"]   = 3
pars["prism_tmean_version"] = 3

# NLDAS-2 hourly primary forcing (NASA GES DISC)
pars["NLDASDataLoc"] = "https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/NLDAS_FORA0125_H.002"
pars["NLDASUsername"] = os.environ.get("EARTHDATA_USERNAME", "REPLACE_ME")
pars["NLDASPassword"] = os.environ.get("EARTHDATA_PASSWORD", "REPLACE_ME")

if pars["NLDASUsername"] == "REPLACE_ME" or pars["NLDASPassword"] == "REPLACE_ME":
    raise SystemExit(
        "Set EARTHDATA_USERNAME and EARTHDATA_PASSWORD as environment variables, "
        "or edit the two REPLACE_ME values in this script."
    )

# -------- 5. Run --------
print(f"PRISM + NLDAS download for {pars['StartYear']}-{pars['StartMonth']:02d} "
      f"through {pars['EndYear']}-{pars['EndMonth']:02d}")
print(f"Writing into: {os.getcwd()}")
Forcing.DownloadGriddedForcingData(pars)
print("Done.")
