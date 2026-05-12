# SnowPALM — collaborator handoff (2026-05-12)

You're inheriting an in-progress SnowPALM modeling effort from another Claude
Code session. This file gives you the full context you need to continue
without re-discovering the dependency migrations and known bugs that prior
session already chased.

If you only read this file plus `git log --oneline 7798feb..HEAD`, you
should have enough to resume work productively.

---

## Project at a glance

SnowPALM (Snow Physics And Lidar Mapping) — Python port of Patrick
Broxton's MATLAB forest-thinning snow model. The Python code came from a
HydroShare supplementary archive (Dwivedi et al. 2024,
doi:10.4211/hs.896aa1fdb76f4871a00362c257d3cf91), **not** from any official
GitHub. The official broxtopd/SnowPALM repo is MATLAB-only.

User context:
- Researcher new to git and Python environments — explain those concepts
  inline when relevant. Don't over-engineer or sneak in abstractions.
- Active site is **ChapmanR1** in northern California, ~2,098 m elevation
  near Bassets / Yuba Pass / Sierra City. Resampled to 1.5 m grid,
  ~1,000 acres, ~2 M pixels.
- Target simulation: **Water Year 2025** (Oct 2024 – Sep 2025), daily
  timestep, `DailyNLDASData2` config (pure NLDAS + PRISM, no station data).
- A 1-month test sim `ChapmanR1_WY2025_Dec_test` is used for fast iteration.

The user's primary work machine is Windows with miniconda env `snowpalm`
at `C:\Users\jburdick\AppData\Local\miniconda3\envs\snowpalm` (Python 3.12).
A Linux mirror clone at `/home/jburdick_m/snowPALM` is used by the prior
Claude session for code edits.

---

## Repo layout cheat sheet

```
snowPALM/
├── CLAUDE.md                                     ← you are here
├── .gitignore                                    ← restrictive allowlist:
│                                                   `*` ignored except .py / .txt
├── GriddedForcing/                               ← outside the model package;
│   ├── DownloadForcingData.py                    ←  shared across sites
│   ├── earthdata_token.local                     ← user's bearer token; gitignored
│   ├── NLDAS/<yyyy>/<ddd>/*.nc                   ← downloaded raw forcing
│   └── PRISM/{ppt,tmean}/<yyyy>/*.zip
├── Model_Package/data/contents/
│   ├── SnowPALM_model/                           ← the actual Python library
│   │   ├── Forcing.py                            ← I/O for forcing data
│   │   ├── GIS.py                                ← SAGA wrappers
│   │   ├── Indexes.py                            ← skyview / SFI / LWI / wind
│   │   ├── Initialize.py                         ← per-tile setup + interp
│   │   ├── Model.py                              ← snow physics
│   │   └── Output.py                             ← gridded TIF export
│   ├── ChapmanR1/                                ← active site
│   │   ├── GetSpatialData.py                     ← step 1
│   │   ├── ComputeRadiationIndexes.py            ← step 2 (serial)
│   │   ├── computeradiationindexes_inparallel.py ← step 2 parallel sibling
│   │   ├── GetForcingData.py                     ← step 4
│   │   ├── ComputeWindIndexes.py                 ← step 5
│   │   ├── RunModel.py                           ← step 6
│   │   ├── OutputGriddedData.py                  ← step 7
│   │   ├── ModelPars.py
│   │   ├── Preprocess/                           ← outputs of steps 1–2,4–5
│   │   ├── Model/<SimulationName>/               ← per-tile state for sim
│   │   ├── Output/<SimulationName>/              ← gridded GeoTIFFs
│   │   └── InputData/SpatialData/                ← DTM/CHM/cover inputs
│   ├── Site 1/, Site 2/, Site 3/, Site 4/        ← inactive other sites
│   └── QuickStart_for_SnowPALM_model.txt         ← canonical 6-step doc
└── SnowPALM_model/                               ← STALE duplicate; do not import
                                                    from this path. See "Stale
                                                    Forcing.py" gotcha below.
```

---

## What changed in the prior session (read commits since `7798feb`)

The 2024 Python port targeted data sources that NASA and PRISM both retired
in mid-2024 / late-2025. Prior session did a full pipeline migration plus a
handful of dependency bug fixes. Key commits, oldest first:

- `7798feb` — `Forcing.py`: switched to NLDAS-2 v2.0 NetCDF + PRISM NACSE
  endpoint. Added `_read_nldas_netcdf` helper.
- `ec19301` — Parallel + `/vsimem` in `_read_nldas_netcdf` (3–5× speedup).
- `5287cab` / `a9f8693` — Fixed `sys.path.insert(1, 'ProgramFiles')` import
  bug across the per-site scripts (was silently picking up a stale
  duplicate copy of `Forcing.py`).
- `7faa7bd` — Replaced removed `scipy.interpolate.interp2d` (SciPy 1.14
  dropped it) with a `RegularGridInterpolator`-backed shim.
- `05e247f` — Fallback in `Model.py` when `find_peaks` returns empty (only
  matters on short test runs like a 1-month December).
- `5577ea3` — User fixed `ChapmanR1/GetSpatialData.py` IndexDir path so
  LAI ends up in `Preprocess/Indexes/` (was going to `Preprocess/`).
- `ffe7d9d` — Parallel
  `ChapmanR1/computeradiationindexes_inparallel.py`. Use this for any
  site bigger than ~1k acres at sub-2m resolution.
- `11debd5` — Fixed import path + `NProcesses` in
  `ChapmanR1/OutputGriddedData.py`.
- **`941feb3` — Fix NLDAS Rainf units (CRITICAL).** Prior session initially
  multiplied Rainf by 3600 thinking it was kg/m²/s; verified against
  a live NLDAS file that units are actually `kg m-2` (mm accumulated in
  the hour). The `*3600` was making precipitation 3,600× too high; PRISM
  lapse-rate correction only partly compensated.

---

## Current state of the model (close of 2026-05-12)

User ran one-month December 2024 test (`ChapmanR1_WY2025_Dec_test`). After
fixing the Rainf bug (`941feb3`), most recent reported output on Dec 31, 2024:

| Variable | Model output | Realistic (Sierra SNOTEL @ ~2,100 m) |
|---|---|---|
| SWE | 1,345–2,599 mm | 190–470 mm |
| Snow Depth | 3,922–6,734 mm | 50–100 cm |
| AirT | −19 to −37 °C | plausible for cold winter |

**Model is overpredicting SWE by ~3–13× and depth by ~8–13×.** Reference
SNOTEL stations checked on Dec 31, 2024:
- Independence Camp (2,125 m): 190 mm SWE, 51 cm depth
- Central Sierra Snow Lab (2,103 m): 384 mm SWE
- Gold Lake (2,057 m): 472 mm SWE
- Huysink (2,012 m): 296 mm SWE

WY 2025 had a slow start in the northern Sierra, so observed values are
on the lower end of normal.

**Open debugging question:** unclear whether the user re-ran
`GetForcingData.py` after pulling commit `941feb3` before checking these
numbers. **First diagnostic:**

```bat
python -c "import netCDF4, numpy as np; ds=netCDF4.Dataset(r'Preprocess\Forcing\DailyNLDASData2\2024\12\15.nc'); p=ds['Precip'][:]; print('Dec 15 daily Precip (mm):', float(np.nanmin(p)), float(np.nanmax(p)), float(np.nanmean(p)))"
```

- If Precip still shows ~1336–1492 mm: GetForcingData wasn't re-run; the
  daily forcing files still carry the 3,600× bug. Solution: delete
  `Preprocess/Forcing/DailyNLDASData2/2024/12/` and re-run
  `GetForcingData.py DailyNLDASData2 2024 12 2024 12`.
- If Precip is 0–80 mm but SWE is still 1,300+ mm: the residual 3–5×
  overshoot is from elsewhere. Most likely candidates are the two
  carried-forward bugs below.

---

## Known unresolved bugs (NOT fixed this session)

These were in the original Dwivedi 2024 port. Worth fixing if the
remaining SWE overshoot persists after a clean GetForcingData rerun.

### Bug 1 — Tetens vapor-pressure formula applied to Kelvin

In `Forcing.py` ~line 437 (RH calc) and `Model.py` ~line 287 (Qe latent
heat flux):

```python
ESAT = 0.6108 * np.exp(17.27 * AIRT / (237.3 + AIRT)) * 1000  # in Pa
```

The Tetens formula expects T in **°C**; AIRT here is in **K** (NLDAS Tair
is in Kelvin). Plugging K into this formula gives ESAT values in the
millions of Pa instead of ~600 Pa, so RH comes out ~0.01% instead of
~50–80%.

Symptom: `RuntimeWarning: overflow encountered in multiply` on the Qe
line of `Model.py`. Practical effect: sublimation is likely wildly under-
or over-estimated, possibly contributing to over-accumulation of snow.

Fix: pass `AIRT - 273.15` to the Tetens formula. Verify against the rest
of the surrounding math first — there may be a partial compensation
elsewhere that this would break.

### Bug 2 — NLDAS PotEvap unit mismatch

`Forcing.py::_read_nldas_netcdf` reads `data[8] = PotEvap` directly.
NLDAS-2 v2.0 NetCDF PotEvap is in **W/m²** (latent-energy flux). Old
GRIB-1 PEVAP was in **kg/m²/hr** (mm of evaporation per hour). The model
stores this as `pet` and consumes it downstream — currently ~700× too
large in numerical value.

Conversion: `mm/hr = W/m² × 3600 / λv` where λv ≈ 2.5e6 J/kg, i.e.
multiply by ~1.44e-3.

Apply in `_read_nldas_netcdf` alongside the existing band assignments.

### Bug 3 — cosmetic, OutVars unit strings

`RunModel.py` OutVars table has multiple incorrect unit strings, e.g.
`['Snow Depth', 'depth', 'W/m2']` (should be `mm`). Values are stored
correctly in mm — only metadata is wrong. Low priority.

---

## Data-pipeline reference

### Endpoints (verified as of 2026-05-12)

**PRISM** (NACSE, free, no auth, but rate-limited):
```
https://services.nacse.org/prism/data/get/us/4km/<var>/<yyyymm>?format=bil
```
- `<var>` in {ppt, tmean, tmin, tmax, tdmean, vpdmin, vpdmax}
- Returns a zip with .bil/.hdr/.prj inside, 32-bit float, units mm or °C
  (unscaled — direct float values).
- Rate limit: same file twice per IP per 24 h.
  `DownloadForcingData.py` sleeps 2 s between PRISM requests.

**NLDAS-2 v2.0** (NASA GES DISC, requires Earthdata Bearer Token):
```
https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/NLDAS_FORA0125_H.2.0/
    {YYYY}/{DDD}/NLDAS_FORA0125_H.A{YYYYMMDD}.{HH}00.020.nc
```
- Token must be generated at urs.earthdata.nasa.gov; user must approve
  "NASA GESDISC DATA ARCHIVE" under Authorized Apps.
- Stored in `GriddedForcing/earthdata_token.local` (gitignored).
- GRIB-1 retired 2024-08-01 — NetCDF only.
- Variable units worth remembering:
    - Tair: K
    - Qair: kg/kg
    - PSurf: Pa
    - Wind_E/Wind_N: m/s
    - LWdown/SWdown: W/m²
    - Rainf: **kg/m² (mm accumulated in the hour)** — same as old GRIB APCP
    - PotEvap: **W/m²** — different from old GRIB PEVAP, see Bug 2

### Canonical workflow

From inside `Model_Package/data/contents/ChapmanR1/`:

1. `python GetSpatialData.py`
2. `python ComputeRadiationIndexes.py` (or the parallel sibling)
3. *One-time per date range:* `python ..\..\..\..\GriddedForcing\DownloadForcingData.py`
4. `python GetForcingData.py DailyNLDASData2 <SY> <SM> <EY> <EM>`
5. `python ComputeWindIndexes.py` (needs step 4 output)
6. `python RunModel.py <SimulationName>`
7. `python OutputGriddedData.py <SimulationName> <StartDate> <EndDate> swe,depth,airt`

Step 3 only needs to run once for a date range; the downloaded forcing is
shared across all sites in `GriddedForcing/`.

---

## Practical gotchas

- **Stale Forcing.py duplicate.** There are *two* copies of `SnowPALM_model`
  in this repo: the live one at `Model_Package/data/contents/SnowPALM_model/`
  and a stale legacy copy at `<repo-root>/SnowPALM_model/`. The per-site
  scripts use anchored-relative imports (`current_file_dir.parent /
  "SnowPALM_model"`) to pick up the live one. If you see code referencing
  the top-level copy or vice versa, check the import. Easy fix when in
  doubt is to print `Forcing.__file__` early in the script — the scripts
  already do this.
- **`OverwriteForcing`/`OverwriteIndexes` flags** in `RunModel.py` control
  whether already-computed forcing/index NetCDFs for a `SimulationName`
  get rebuilt. Default False = skip if exists. To force a full rebuild
  after a code/data change, delete `Model/<SimulationName>/` (or set
  `program_pars['ReinitializeModel'] = True`).
- **`GetForcingData.py` has no resume.** It always rewrites every daily
  output for the date range you pass. Chunk by month if needed.
- **`NProcesses`** in `RunModel.py` and `OutputGriddedData.py`: defaults
  in the upstream repo were 60 (author's machine). Prior session knocked
  them down to 8. Set to your CPU core count; bump up on a VM.
- **VS Code interactive windows** can stall if you try to open a second
  one while the first is running. Default is `single`-mode shared kernel.
  Set `jupyter.interactiveWindow.creationMode` to `perFile` if you want
  independent kernels.

---

## Things to NOT do

- Don't reintroduce the wget-based downloader. `wget` isn't reliably
  installable on conda-forge Windows builds; the requests-based version
  with Earthdata bearer token works on both Windows and Linux.
- Don't commit credentials. `.gitignore` blocks `*.local`, `*.secret`,
  `credentials*`, `*token*.txt`, `*.pem`, `*.key` — and the allowlist
  `.gitignore` blocks everything that isn't `.py`/`.txt` by default. Both
  layers should hold but be careful with default-value patterns like
  `os.environ.get("FOO", "<token>")` — the session opened with a token
  leak from exactly that pattern.
- Don't force-push to main without coordinating. Prior session has done
  it once (rebasing user's commits onto our SciPy fix); user explicitly
  authorized it. If you need to do it again, ask first.
- Don't blanket-recompute when files exist. SnowPALM's preprocessing is
  designed to skip existing outputs unless `Overwrite` is true.

---

## How to pick up from here

1. `git pull` to get the latest commits.
2. `git log --oneline -25` for chronology.
3. Read this file.
4. Ask the user the diagnostic question about whether they re-ran
   `GetForcingData.py` after commit `941feb3` and what the daily Precip
   inspection command returned.
5. Based on the answer, either chase the GetForcingData rerun OR start
   investigating the two carried-forward bugs above.

Good luck.
