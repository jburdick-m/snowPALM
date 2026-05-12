# SnowPALM — collaborator handoff

You're inheriting an in-progress SnowPALM modeling effort from another Claude
Code session (most recent work landed 2026-05-12). This file is the canonical
context dump; everything else can be derived from it plus `git log` and the
code itself. Companion memory files live at `.claude/memory/` in this repo
(copied from the previous session's memory store) for additional context on
the user and project history.

> **First read on pickup:** scroll to **"How to pick this up"** at the bottom
> for the numbered onboarding steps.

---

## 1. Who you're working with

The user is a **snow / forest-hydrology researcher**, comfortable with the
science domain (snowpack physics, forest thinning, NLDAS/PRISM, lidar) but
**new to git and to Python environment management**. Spell out vocabulary
inline when those topics come up (what does `git pull` do; what `conda
activate` does; where envs live on disk). Don't talk down — they're a
researcher, just new to *these* tools. Don't sneak in abstractions, don't
refactor for refactoring's sake — keep patches obvious enough that they can
audit. See `.claude/memory/user_role.md` for more.

The user's primary work machine is **Windows** with miniconda env
`snowpalm` at `C:\Users\jburdick\AppData\Local\miniconda3\envs\snowpalm`
(Python 3.12). They will run model commands there. The Linux mirror clone
that produced earlier commits is at `/home/jburdick_m/snowPALM` on a
*different* VM — you (on Google Cloud or wherever) are a third machine
collaborating via this GitHub repo.

---

## 2. Project at a glance

**SnowPALM (Snow Physics And Lidar Mapping)** — Python port of Patrick
Broxton's MATLAB forest-thinning snow model. The Python code came from a
HydroShare supplementary archive:

> Dwivedi et al. 2024, doi:10.4211/hs.896aa1fdb76f4871a00362c257d3cf91

The official `broxtopd/SnowPALM` GitHub repo is **MATLAB only**. Don't waste
time searching GitHub for the Python version — this repo
(`jburdick-m/snowPALM`) is the working fork.

**Active site:** ChapmanR1 in northern California, ~2,098 m elevation
near Bassets / Yuba Pass / Sierra City. Domain is ~1,000 acres, resampled
to **1.5 m** grid (~2 M model pixels, 64 tiles).

**Active simulation:** WY 2025 (Oct 2024 – Sep 2025), daily timestep,
`DailyNLDASData2` config (pure NLDAS + PRISM, no station-data
augmentation). A 1-month test sim `ChapmanR1_WY2025_Dec_test` is used for
fast iteration.

---

## 3. Repo layout — IMPORTANT (stale duplicates everywhere)

```
snowPALM/
├── CLAUDE.md                                     ← this file
├── .claude/memory/                               ← session-history memory
├── .gitignore                                    ← allowlist: *.py, *.txt, *.md
├── environment.yml                               ← conda env spec
├── requirements.txt                              ← pip fallback (see note)
├── GriddedForcing/                               ← shared across sites
│   ├── DownloadForcingData.py                    ← parallel downloader
│   ├── earthdata_token.local                     ← user's bearer token (gitignored)
│   ├── NLDAS/<yyyy>/<ddd>/*.020.nc               ← raw forcing
│   └── PRISM/{ppt,tmean}/<yyyy>/*.zip
├── Model_Package/data/contents/
│   ├── SnowPALM_model/                           ← the LIVE Python library
│   │   ├── Forcing.py (836 lines)
│   │   ├── GIS.py
│   │   ├── Indexes.py
│   │   ├── Initialize.py
│   │   ├── Model.py
│   │   └── Output.py
│   ├── ChapmanR1/                                ← active site
│   │   ├── GetSpatialData.py                     ← step 1
│   │   ├── ComputeRadiationIndexes.py            ← step 2 (serial)
│   │   ├── computeradiationindexes_inparallel.py ← step 2 (parallel)
│   │   ├── GetForcingData.py                     ← step 4
│   │   ├── ComputeWindIndexes.py                 ← step 5
│   │   ├── RunModel.py                           ← step 6
│   │   ├── OutputGriddedData.py                  ← step 7
│   │   ├── ModelPars.py
│   │   ├── Preprocess/                           ← outputs of steps 1,2,4,5
│   │   ├── Model/<SimulationName>/               ← per-tile model state
│   │   ├── Output/<SimulationName>/              ← gridded GeoTIFFs
│   │   └── InputData/SpatialData/                ← DTM/CHM/cover inputs
│   ├── Site 1/, Site 2/, Site 3/, Site 4/        ← inactive prior sites
│   └── QuickStart_for_SnowPALM_model.txt
└── ⚠ STALE DUPLICATES AT REPO ROOT (DO NOT USE):
    SnowPALM_model/         ← 780 lines of pre-migration Forcing.py etc.
    ComputeRadiationIndexes.py, ComputeWindIndexes.py, GetForcingData.py,
    GetSpatialData.py, OutputForcingData.py, OutputGriddedData.py,
    ModelPars_postthin.py, Transmittances.py, Site 2/
```

**The repo root has stale copies of every per-site script and the entire
`SnowPALM_model/` library.** These are leftovers from how the HydroShare
ZIP was extracted, NOT canonical sources. The previous session burned ~20
minutes diagnosing one of these silent collisions (the broken
`sys.path.insert(1, 'ProgramFiles')` pattern in the per-site scripts was
falling through to the stale top-level `SnowPALM_model/Forcing.py`,
producing baffling errors). The per-site scripts now use anchored-relative
imports and print `Forcing.__file__` on startup so you can verify which
copy got loaded.

If you ever consider tidying this up, **ask the user first** — they may
want the stale copies retained for parity with the HydroShare archive.

---

## 4. What the previous session changed (chronological)

The 2024 Python port targeted data sources that NASA and PRISM both
retired in 2024–2025. The previous session migrated the pipeline and
patched a handful of dependency-related breakages.

Run `git log --oneline 7798feb~1..HEAD` for the full list. Highlights:

- `7798feb` — `Forcing.py` switched to NLDAS-2 v2.0 NetCDF + PRISM NACSE
  endpoint. Added `_read_nldas_netcdf()` helper.
- `ec19301` — Parallel + `/vsimem` in `_read_nldas_netcdf` (3–5× speedup).
- `5287cab`, `a9f8693`, `11debd5` — Fixed broken
  `sys.path.insert(1, 'ProgramFiles')` import across per-site scripts.
- `7faa7bd` — Replaced removed `scipy.interpolate.interp2d` (SciPy 1.14+
  dropped it) with a `RegularGridInterpolator`-backed shim.
- `05e247f` — Fallback in `Model.py::get_forcing_data` when `find_peaks`
  returns empty (relevant for short test runs).
- `ffe7d9d` — Parallel sibling
  `ChapmanR1/computeradiationindexes_inparallel.py` (use for sites bigger
  than ~1k acres at sub-2m resolution).
- `5577ea3` — User fixed `ChapmanR1/GetSpatialData.py` `IndexDir` path
  (LAI was going to `Preprocess/` instead of `Preprocess/Indexes/`).
- `941feb3` — **CRITICAL: NLDAS Rainf unit fix.** Earlier in the session
  Rainf was multiplied by 3600 on the assumption that NetCDF Rainf is
  `kg/m²/s` (a rate). It's actually `kg/m²` (mm accumulated in the hour),
  same as the old GRIB-1 APCP. The bogus ×3600 was making precipitation
  3,600× too high at the source. PRISM lapse-rate correction partially
  compensated; final daily forcing was still ~35× too high before the fix.
- `7aa9754` — first version of this CLAUDE.md (now superseded).

---

## 5. Where the model stands right now

User ran a 1-month December test (`ChapmanR1_WY2025_Dec_test`) and
reported Dec 31, 2024 output values:

| Variable | Model output | Realistic (Sierra SNOTEL @ ~2,100 m) |
|---|---|---|
| SWE | 1,345 – 2,599 mm | 190 – 472 mm |
| Snow Depth | 3,922 – 6,734 mm | ~50 cm at the one nearby station with a depth sensor |
| AirT | −19 to −37 °C | Plausible for cold winter at this elevation |

Comparison stations on Dec 31, 2024 (verified via CDEC and NRCS SNOTEL
reports):
- **Independence Camp SNOTEL** (2,125 m): 190 mm SWE, 51 cm depth
- **Central Sierra Snow Lab** (2,103 m): 384 mm SWE
- **Gold Lake** (2,057 m): 472 mm SWE
- **Huysink** (2,012 m): 296 mm SWE
- WY 2025 had a slow start in the northern Sierra; observed values are on
  the lower end of normal.

Model is **overpredicting SWE by ~3–13×**. Depth overestimate ratio is
based on a single observation (Independence Camp's 51 cm depth) so treat
the "8–13×" figure as soft.

**OPEN QUESTION carried over from the previous session:** it's not
confirmed whether the user re-ran `GetForcingData.py` after pulling
commit `941feb3` before sampling these output values. **First diagnostic
step before chasing anything else:**

```bat
python -c "import netCDF4, numpy as np; ds=netCDF4.Dataset(r'Preprocess\Forcing\DailyNLDASData2\2024\12\15.nc'); p=ds['Precip'][:]; print('Dec 15 daily Precip (mm):', float(np.nanmin(p)), float(np.nanmax(p)), float(np.nanmean(p)))"
```

- If Precip is still ~1336–1492 mm: `GetForcingData.py` wasn't re-run.
  Solution: delete `Preprocess\Forcing\DailyNLDASData2\2024\12\` and
  re-run `python GetForcingData.py DailyNLDASData2 2024 12 2024 12` from
  the ChapmanR1 folder.
- If Precip is now 0–80 mm but SWE is still 1,300+ mm: residual
  ~3–5× overshoot is from elsewhere — chase the two carry-forward bugs
  below.

---

## 6. Carry-forward bugs (NOT fixed this session)

These were in the original Dwivedi 2024 port. Worth chasing if the
remaining overshoot persists after a clean `GetForcingData.py` re-run.

### Bug A — NLDAS PotEvap unit mismatch (HIGH confidence, likely real)

`Forcing.py::_read_nldas_netcdf` reads `data[8] = PotEvap` directly from
the NetCDF. NLDAS-2 v2.0 NetCDF PotEvap is in **W/m²** (latent-energy
flux). The old GRIB-1 PEVAP was in **kg/m²/hr** (mm of water per hour) —
which is what `Forcing.py` and the model treat the value as.

PET *is* actively consumed: `Model.py` line 505 uses it in the
evapotranspiration calculation:

```python
et = PET * ((state['sm_stor'] / model_pars['H']) - model_pars['wp']) / \
     (model_pars['cmc'] - model_pars['wp'])
```

So `et` is also ~700× too large, draining soil moisture too fast. This
primarily hits the hydrology side (soil moisture, runoff). It does *not*
directly affect SWE, but watch out if downstream analysis uses ET / soil
moisture.

**Fix sketch:** in `_read_nldas_netcdf` after the warp loop, multiply
`data[8]` by `3600 / Lv` where `Lv ≈ 2.5e6 J/kg`, i.e. multiply by
~1.44e-3 to convert W/m² → kg/m²/hr. Then check `model_pars['PET_Mult']`
(applied in `Model.py` line 676) to make sure it isn't already silently
compensating.

### Bug B — Tetens vapor-pressure formula applied to Kelvin (LOW–MEDIUM confidence)

In `Forcing.py` around line 437 (inside `GetForcingData`):

```python
AIRT = airt[c,:,:]     # NLDAS Tair in K
...
ESAT = 0.6108 * np.exp(17.27 * AIRT / (237.3 + AIRT)) * 1000
RH = np.maximum(0, np.minimum(1, (VAPP / ESAT))) * 100
```

The Tetens formula expects T in **°C**; `AIRT` here is in **K** (raw NLDAS
Tair). Plugging K into the formula gives ESAT in the megapascal range
instead of ~600 Pa, so the RH written to the daily forcing NetCDF is
essentially 0.

**Practical impact is muted**, however: `Model.py` line 185 recomputes
`rh = vapp/svapp*100` locally from `airt` and `vapp`, shadowing the value
read from the forcing file. As long as `airt` reaches the model in **°C**
(which happens automatically when `ApplyAirTLapseRate` is 1 or 2 — the
lapse-rate correction's K→C arithmetic is what bakes in the conversion),
Tetens at `Model.py:184` and `Model.py:284` works on Celsius and is fine.

**But:** the previous session observed a
`RuntimeWarning: overflow encountered in multiply` on `Model.py:287`
(`Qe = ... * (vapp - svapp)`) during the test run. The root cause wasn't
fully pinned down. Possible avenues if you chase this:
- Confirm `airt` in the per-tile forcing NetCDFs is actually in °C
  (`ncdump -h Model/<sim>/Tile0/Forcing.nc | grep -i airt`).
- If ApplyAirTLapseRate is ever set to 0 in a config, airt reaches the
  model in K and Tetens explodes — Forcing.py should explicitly K→C
  convert when no lapse rate is applied.
- If overflow persists with airt in °C, look upstream of `k0` in Model.py
  for whatever else feeds into the multiply.

### Bug C — Cosmetic: OutVars unit strings in RunModel.py

`RunModel.py` `OutVars` table has wrong unit strings, e.g.
`['Snow Depth', 'depth', 'W/m2']` (should be `mm`). Values are stored
correctly; only the metadata is wrong. Low priority.

---

## 7. Data-pipeline reference

### Endpoints (verified 2026-05-12)

**PRISM** (NACSE, free, no auth, rate-limited):

```
https://services.nacse.org/prism/data/get/us/4km/<var>/<yyyymm>?format=bil
```

- `<var>` ∈ {`ppt`, `tmean`, `tmin`, `tmax`, `tdmean`, `vpdmin`, `vpdmax`}
- Returns a zip with `.bil`/`.hdr`/`.prj` inside; 32-bit float, unscaled.
  Units mm for ppt, °C for tmean. **No stable/provisional split anymore.**
- Rate limit: same file twice per IP per 24 h. `DownloadForcingData.py`
  sleeps 2 s between PRISM requests.

**NLDAS-2 v2.0** (NASA GES DISC, requires Earthdata bearer token):

```
https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/NLDAS_FORA0125_H.2.0/
    {YYYY}/{DDD}/NLDAS_FORA0125_H.A{YYYYMMDD}.{HH}00.020.nc
```

- Token generated at urs.earthdata.nasa.gov; user must approve
  "NASA GESDISC DATA ARCHIVE" under Authorized Apps once.
- Lives in `GriddedForcing/earthdata_token.local` (gitignored via `*.local`).
- GRIB-1 retired 2024-08-01 — NetCDF only.
- Variable conventions to remember:
  - `Tair`: K
  - `Qair`: kg/kg
  - `PSurf`: Pa
  - `Wind_E` / `Wind_N`: m/s
  - `LWdown` / `SWdown`: W/m²
  - `Rainf`: **kg/m² (mm accumulated in the hour)** — same as old GRIB APCP.
  - `PotEvap`: **W/m²** — DIFFERENT from old GRIB PEVAP (mm/hr). See Bug A.

### Workflow (canonical, 7 steps)

From inside `Model_Package/data/contents/ChapmanR1/`:

1. `python GetSpatialData.py`
2. `python ComputeRadiationIndexes.py` (or parallel sibling for large sites)
3. **One-time per date range**, from `GriddedForcing/`:
   `python DownloadForcingData.py`
4. `python GetForcingData.py DailyNLDASData2 <SY> <SM> <EY> <EM>`
5. `python ComputeWindIndexes.py` (needs step 4 output)
6. `python RunModel.py <SimulationName>`
7. `python OutputGriddedData.py <SimulationName> <StartDate> <EndDate> swe,depth,airt`

Step 3 only runs once for a date range; the downloaded CONUS-wide forcing
is shared across all sites in `GriddedForcing/`.

### Env setup

Two options:

- **Conda (preferred):** `conda env create -f environment.yml`, then
  `conda activate snowpalm`. Handles GDAL's C libraries cleanly.
- **Pip:** see `requirements.txt`. Requires system `libgdal-dev` and PROJ
  pre-installed and matching the pip-installed `GDAL` version exactly.
  Usually painful — use conda unless you have a reason not to.

Additional non-Python dependency: **SAGA GIS**. `ComputeRadiationIndexes`
and `ComputeWindIndexes` invoke `saga_cmd` to compute terrain-radiation
and wind-redistribution indexes. The path is hardcoded in each script as
`pars['SagaGISLoc']`. Set it for your machine.

---

## 8. Practical gotchas

- **Stale duplicates at repo root.** See §3. Always run scripts from
  `Model_Package/data/contents/ChapmanR1/`, never from the repo root.
  Verify your script's first stdout line — it should print
  `Using Forcing from: …Model_Package/data/contents/SnowPALM_model/…`.
- **`OverwriteForcing` / `OverwriteIndexes`** flags in `RunModel.py`
  control whether the per-tile NetCDF forcing/index files for a given
  `SimulationName` get rebuilt. Default `False` = skip if file exists.
  Set `program_pars['ReinitializeModel'] = True` (or delete
  `Model/<SimulationName>/`) to force a full rebuild after any forcing or
  index change.
- **`GetForcingData.py` has no resume** — it always rewrites every daily
  output `.nc` for the date range you pass. Chunk by month to localize
  work after a fix.
- **`NProcesses`** in `RunModel.py` and `OutputGriddedData.py`: the
  upstream defaults were 60 (author's hardware). Knocked to 8 by the
  previous session. Tune to your CPU core count.
- **Earthdata bearer tokens expire** every ~60 days. If NLDAS downloads
  start returning HTTP 401, regenerate the token at
  urs.earthdata.nasa.gov and replace
  `GriddedForcing/earthdata_token.local`.
- **PRISM rate-limit anti-pattern:** the NACSE service blocks IPs that
  request the same file more than twice per 24 h. If a download chunk
  failed, edit `START_*`/`END_*` in `DownloadForcingData.py` to the
  shorter retry range instead of retrying the whole year.
- **VS Code interactive windows** stall the second one if the first is
  busy with a long-running script. Default is `single`-mode shared kernel.
  Set `jupyter.interactiveWindow.creationMode` to `perFile` for
  independent kernels.

---

## 9. Things to NOT do

- **Don't reintroduce the `wget`-based downloader.** `wget` isn't
  reliably installable on conda-forge Windows builds. The requests-based
  version in `GriddedForcing/DownloadForcingData.py` works cross-platform.
- **Don't commit credentials.** `.gitignore` blocks `*.local`, `*.secret`,
  `credentials*`, `*token*.txt`, `*.pem`, `*.key`, plus the allowlist
  pattern at the top denies anything that isn't `.py`/`.txt`/`.md`. The
  prior session had a token leak from a default-value pattern like
  `os.environ.get("EARTHDATA_TOKEN", "<real-token-here>")`. The token was
  revoked; don't repeat it. **Anything that could be a credential goes
  in `earthdata_token.local` or similar `*.local`, never as a string
  default in code.**
- **Don't force-push to main without explicit user approval.** The prior
  session did it once during a coordinated push (`git push --force origin
  HEAD~1:main` followed by a rebase); user authorized it explicitly. If
  you need to do it again, ask first.
- **Don't blanket-recompute** when files already exist on disk. SnowPALM's
  preprocessing scripts skip existing outputs by design (controlled per
  script via `pars['Overwrite']`). Respect that — recomputing
  `ComputeRadiationIndexes` at 1.5 m for a 1000-acre site is a 30-min job
  even with the parallel script.
- **Don't refactor for refactoring's sake.** The user is new to Python
  and reads diffs carefully. Keep patches obvious; prefer the smallest
  fix to the named problem.

---

## 10. How to pick this up

In order:

1. `git pull` to get the latest commits.
2. Skim `git log --oneline -25` for chronology.
3. Read this file (you're doing it) and at least skim
   `.claude/memory/project_snowpalm.md` and
   `.claude/memory/user_role.md`.
4. **Verify which `Forcing.py` you'd import.** From the snowPALM root:
   ```bash
   find . -name "Forcing.py"
   ```
   Make sure your mental model of the two copies (live vs. stale top-level)
   matches §3.
5. Ask the user: did they re-run `GetForcingData.py` after pulling commit
   `941feb3`? Have them run the one-line Precip inspection from §5.
6. Branch from there: either chase a stale `GetForcingData` regeneration
   OR start investigating Bug A (PotEvap unit mismatch) — see §6.

Good luck.
