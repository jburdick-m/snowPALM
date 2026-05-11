"""
DownloadForcingData.py
======================

Downloads the PRISM (monthly precip + mean temperature) and NLDAS-2 (hourly
forcing) data that SnowPALM needs, by wrapping the DownloadGriddedForcingData()
function in SnowPALM_model/Forcing.py.

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
   "NASA GESDISC DATA ARCHIVE". Without that step NLDAS downloads come back
   as HTML login pages instead of real .grb files.

2. Make sure 'wget' is available on PATH in your snowpalm env. On Windows:
       conda install -n snowpalm -c conda-forge wget

3. Point SNOWPALM_REPO below at your local clone of the snowPALM repo
   (the folder that contains Model_Package/).

4. Fill in your Earthdata credentials either by:
     (a) setting environment variables EARTHDATA_USERNAME / EARTHDATA_PASSWORD
         before launching python, OR
     (b) editing the two REPLACE_ME values below.
   Do not commit the file back to git with real credentials in it.

USAGE
-----
From an activated snowpalm env, with this script's folder as the working dir:
    python DownloadForcingData.py

It is currently set up for Water Year 2025 (Oct 2024 through Sep 2025). Edit
the date block below to change that.

Expect a long run: NLDAS-2 is hourly, so a full water year is ~8,800 small
GRB files (~7 GB total). PRISM is much smaller (24 zip files for a year).
"""

import os
import sys
from pathlib import Path

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

# -------- 2. Work out of this script's folder --------
# The downloader writes PRISM/ and NLDAS/ as RELATIVE paths, so cwd matters.
os.chdir(Path(__file__).resolve().parent)

# -------- 3. Parameters --------
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

# -------- 4. Run --------
print(f"PRISM + NLDAS download for {pars['StartYear']}-{pars['StartMonth']:02d} "
      f"through {pars['EndYear']}-{pars['EndMonth']:02d}")
print(f"Writing into: {os.getcwd()}")
Forcing.DownloadGriddedForcingData(pars)
print("Done.")
