---
name: SnowPALM project context
description: User's SnowPALM forest-thinning project — repo, source provenance, data-pipeline migration state, and known unresolved bugs
type: project
originSessionId: 2193571c-d312-4cd9-8f23-520690e51b90
---
User is running SnowPALM (Snow Physics And Lidar Mapping) to simulate
forest-thinning effects on snowpack.

Repo: https://github.com/jburdick-m/snowPALM
Local clone (Linux mirror): /home/jburdick_m/snowPALM
User's primary work machine is Windows + miniconda env `snowpalm` at
`C:\Users\jburdick\AppData\Local\miniconda3\envs\snowpalm` (Python 3.12).

Source provenance:
- Python port came from HydroShare resource
  doi:10.4211/hs.896aa1fdb76f4871a00362c257d3cf91 (Dwivedi et al. 2024).
- broxtopd/SnowPALM on GitHub is MATLAB only; the Python port is on
  HydroShare as supplementary data, not a packaged library.

Active site: **ChapmanR1** in California. ~1000 acres, resampled to
1.5 m grid. High-enough elevation that Dec daily means run -19 to -37 °C
in WY 2025 (cold winter; values plausible after lapse-rate correction).

Active simulation: WY 2025 (Oct 2024 – Sep 2025), `DailyNLDASData2`
config (pure NLDAS+PRISM, no station data). Test sim
`ChapmanR1_WY2025_Dec_test` exists for one-month dry-runs.

## Data-pipeline migration (2026-05-12)

Both upstream data sources changed since the Dwivedi 2024 port was
written; pipeline was overhauled this session:

- **PRISM**: ftp.prism.oregonstate.edu retired 2025-09-30. New endpoint
  `services.nacse.org/prism/data/get/us/4km/<var>/<yyyymm>?format=bil`.
  New BIL files are 32-bit float in unscaled units (mm for ppt, °C for
  tmean) — confirmed by inspecting Dec 2024 files. No stable/provisional
  split anymore. Hard rate limit: same file twice per IP per 24 h.
- **NLDAS-2**: GRIB-1 distribution stopped 2024-08-01. NetCDF-4 only via
  `NLDAS_FORA0125_H.2.0` path, filename `.020.nc`. Earthdata bearer
  token required (set in `GriddedForcing/earthdata_token.local`).
  Rainf is in **kg m-2 (mm accumulated in the hour)** — same convention
  as the old GRIB-1 APCP. PotEvap changed to W/m^2 (was mm/hr).
- `Forcing.py::DownloadGriddedForcingData()` is dead code now;
  `GriddedForcing/DownloadForcingData.py` is the entry point.
- `Forcing.py::_read_nldas_netcdf()` reads NetCDF via 9 parallel
  `gdal.Warp` calls (one per variable) writing to `/vsimem/` — 3–5×
  faster than serial disk warping. Same gdal-warp algorithm as before.

Other code changes done this session:
- `Initialize.py::_interp2d_linear()` — drop-in replacement for the
  removed `scipy.interpolate.interp2d` (gone in SciPy 1.14).
- `Model.py` — fallback when `find_peaks` returns empty in short runs.
- Per-site script imports fixed: `sys.path.insert(1, 'ProgramFiles')`
  pattern was broken (silently picked up the stale top-level
  snowPALM/SnowPALM_model copy). Now anchored relative to script file.
- Parallel sibling `ChapmanR1/computeradiationindexes_inparallel.py`
  dispatches SAGA jobs across `pars['MaxParallelSagaJobs']` threads.

## Known unresolved bugs (carried forward from original code)

1. **Tetens vapor-pressure formula applied to Kelvin** in `Forcing.py`
   line ~437 (RH calc) and `Model.py` line ~287 (Qe / latent heat).
   Formula expects °C; AIRT is in K. Produces wildly wrong `ESAT` and
   manifests as `RuntimeWarning: overflow encountered in multiply` on
   the Qe line. Not crashing but probably affecting sublimation /
   snow-energy-balance subtly. **Worth fixing if snow numbers look off
   in subtle ways.**
2. **NLDAS PotEvap unit mismatch**: NetCDF v2.0 reports W/m^2 (energy
   flux), old GRIB-1 PEVAP was kg/m^2/hr (water flux). Conversion needs
   `× 3600 / Lv` (~1.44e-3) to match historical units. Currently fed
   through as W/m^2. Not snow-critical, but any output that uses `pet`
   directly is ~700× off. **Flag for any ET/PET analysis.**

## Why all this matters

The user is new to git and Python envs; explain those terms inline (see
user_role memory). Future-you should NOT silently introduce new
abstractions — keep changes minimal and explicit, and prefer obvious
patches the user can audit over clever rewrites.
