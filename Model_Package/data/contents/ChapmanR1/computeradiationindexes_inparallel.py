"""
computeradiationindexes_inparallel.py
=====================================

Parallel drop-in replacement for ComputeRadiationIndexes.py. Same parameters,
same outputs, runs the SAGA jobs concurrently in a thread pool.

How it parallelizes:
- Skyview-with-vegetation maps:   one SAGA pipeline per VegCoverCategory (5 jobs).
- Potential solar maps:           one SAGA pipeline per (Month, no-veg or VegRange)
                                  (Solar_Months * (1 + len(VegCoverCategories)) jobs).
                                  Daily mode = 72 jobs; hourly mode = 72 * 24 jobs.
- Longwave enhancement maps:      one SAGA grow + post-process per Month
                                  (Solar_Months jobs).

Knobs:
- pars['MaxParallelSagaJobs']: hard cap on simultaneous SAGA processes.
  RAM is usually the binding constraint -- each SAGA solar job can use
  roughly DTM_size_in_RAM * 3-4 (DSM + SVF + outputs in memory). For a
  1.5 m, ~1000-acre site that's ~200-400 MB per worker. Scale back for
  bigger rasters or memory-constrained machines.

Run from inside the ChapmanR1 folder:
    python computeradiationindexes_inparallel.py
"""

import sys
import os
import concurrent.futures
from pathlib import Path

# Add the SnowPALM_model directory (sibling of this script's parent) to sys.path
if "__file__" in globals():
    current_file_dir = Path(__file__).resolve().parent
target_path = current_file_dir.parent / "SnowPALM_model"
if target_path.exists() and str(target_path) not in sys.path:
    sys.path.insert(1, str(target_path))
else:
    print(f"Path already in sys.path or directory not found: {target_path}")

import numpy as np
from scipy import ndimage
from osgeo import gdal, osr
from pyproj import Transformer

import GIS
import Indexes
from GIS import ReadRaster, WriteRasterMatch, exec_cmd, nodataval
print(f"Using GIS from:     {GIS.__file__}")
print(f"Using Indexes from: {Indexes.__file__}")

pars = {}

# ==================== General Parameters ====================

pars['Verbose']         = False
pars['Overwrite']       = True
pars['CreatePyramids']  = False
pars['SagaGISLoc']      = "C:\\Users\\jburdick\\saga-9.12.2_msw"

pars['MaxParallelSagaJobs'] = 16    # Cap on concurrent SAGA processes

pars['VegCoverCategories'] = [[80, 100], [60, 80], [40, 60], [20, 40], [0, 20]]
pars['Transmittances']     = [0.1, 0.3, 0.5, 0.7, 0.9]
pars['CanopyTransFactor']  = 0.5

pars['GISDir']   = os.getcwd() + '/Preprocess/GIS'
pars['IndexDir'] = os.getcwd() + '/Preprocess/Indexes'

# ==================== Skyview parameters ====================

pars['RADIUS'] = 200
pars['METHOD'] = 0
pars['NDIRS']  = 36
pars['DLEVEL'] = 3


# ==================== Skyview: parallel ====================

def _skyview_noveg(pars, DTM):
    SagaGISLoc = pars['SagaGISLoc']
    dem = pars['GISDir'] + '/DTM.tif'
    svf = pars['GISDir'] + '/SkyView_noVeg.tif'
    if os.path.exists(svf) and not pars['Overwrite']:
        return
    print('Creating ' + svf)
    cmd = ('"' + SagaGISLoc.replace('\\', '/') + '/saga_cmd" ta_lighting 3'
           ' -DEM "' + dem + '" -SVF "' + svf + '"'
           ' -RADIUS ' + str(pars['RADIUS'])
           + ' -METHOD ' + str(pars['METHOD'])
           + ' -DLEVEL ' + str(pars['DLEVEL'])
           + ' -NDIRS '  + str(pars['NDIRS']))
    exec_cmd(cmd, pars['Verbose'])
    Data = ReadRaster(svf, pars['Verbose'])
    nanlocs = np.isnan(DTM)
    Data[nanlocs] = nodataval
    WriteRasterMatch(Data, svf, svf, nodataval, pars['CreatePyramids'], pars['Verbose'])


def _skyview_one_vcat(pars, c, VegRange, DTM, Cover, VegHT):
    SagaGISLoc = pars['SagaGISLoc']
    dsm = pars['GISDir'] + '/DSM_vcat_' + str(c) + '.tif'
    svf = pars['GISDir'] + '/SkyView_withVeg_vcat_' + str(c) + '.tif'

    if (not os.path.exists(dsm)) or pars['Overwrite']:
        print('Creating ' + dsm)
        locs = np.logical_and(Cover > VegRange[0], Cover <= VegRange[1])
        DSM = DTM + VegHT * locs.astype(float)
        nanlocs = np.isnan(DTM)
        DSM[nanlocs] = nodataval
        WriteRasterMatch(DSM, dsm, pars['GISDir'] + '/DTM.tif',
                         nodataval, pars['CreatePyramids'], pars['Verbose'])

    if (not os.path.exists(svf)) or pars['Overwrite']:
        print('Creating ' + svf)
        cmd = ('"' + SagaGISLoc.replace('\\', '/') + '/saga_cmd" ta_lighting 3'
               ' -DEM "' + dsm + '" -SVF "' + svf + '"'
               ' -RADIUS ' + str(pars['RADIUS'])
               + ' -METHOD ' + str(pars['METHOD'])
               + ' -DLEVEL ' + str(pars['DLEVEL'])
               + ' -NDIRS '  + str(pars['NDIRS']))
        exec_cmd(cmd, pars['Verbose'])

        SVF = ReadRaster(svf, pars['Verbose'])
        locs = ndimage.binary_dilation(np.logical_and(Cover > VegRange[0], Cover <= VegRange[1]))
        SVF[locs] = nodataval
        nanlocs = np.isnan(DTM)
        SVF[nanlocs] = 0
        WriteRasterMatch(SVF, svf, svf, nodataval, False, pars['Verbose'])

        cmd = ('"' + SagaGISLoc.replace('\\', '/') + '/saga_cmd" grid_tools 29'
               ' -GROW 1.2 -INPUT "' + svf + '" -RESULT "' + svf + '"')
        exec_cmd(cmd, pars['Verbose'])

        Data = ReadRaster(svf, pars['Verbose'])
        nanlocs = np.isnan(DTM)
        Data[nanlocs] = nodataval
        WriteRasterMatch(Data, svf, svf, nodataval, pars['CreatePyramids'], pars['Verbose'])


def get_skyview_maps_parallel(pars):
    DTM = ReadRaster(pars['GISDir'] + '/DTM.tif', pars['Verbose'])
    Cover = ReadRaster(pars['GISDir'] + '/Cover.tif', pars['Verbose'])
    Cover[Cover < 0] = 0
    Cover[np.isnan(Cover)] = 0
    VegHT = ReadRaster(pars['GISDir'] + '/VegHT.tif', pars['Verbose'])
    VegHT[VegHT < 0] = 0
    VegHT[np.isnan(VegHT)] = 0

    _skyview_noveg(pars, DTM)

    workers = min(pars['MaxParallelSagaJobs'], len(pars['VegCoverCategories']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [
            ex.submit(_skyview_one_vcat, pars, c, vr, DTM, Cover, VegHT)
            for c, vr in enumerate(pars['VegCoverCategories'])
        ]
        for f in concurrent.futures.as_completed(futures):
            f.result()    # re-raise any exception in main thread


# ==================== Potential Solar: parallel ====================

def _build_location_string(pars):
    if pars['ConstantLatitude']:
        src = gdal.Open(pars['GISDir'] + '/DTM.tif')
        ulx, xres, _, uly, _, yres = src.GetGeoTransform()
        lrx = ulx + (src.RasterXSize * xres)
        lry = uly + (src.RasterYSize * yres)
        y = (uly + lry) / 2
        x = (ulx + lrx) / 2
        srs = osr.SpatialReference()
        srs.ImportFromWkt(src.GetProjectionRef())
        prj = srs.ExportToProj4()
        trans = Transformer.from_crs(prj, 'epsg:4326', always_xy=True)
        lon, lat = trans.transform(x, y)
        return '-LOCATION 0 -LATITUDE ' + str(lat)
    return '-LOCATION 1'


def _solar_cmd_base(pars, GRD_DEM, GRD_SVF, GRD_DIRECT, GRD_DIFFUS,
                    LocationString, mm, Day, hour_range_min, hour_range_max):
    SagaGISLoc = pars['SagaGISLoc']
    return ('"' + SagaGISLoc.replace('\\', '/') + '/saga_cmd" ta_lighting 2'
            ' -GRD_DEM "' + GRD_DEM + '" -GRD_SVF "' + GRD_SVF + '"'
            ' -GRD_DIRECT "' + GRD_DIRECT + '" -GRD_DIFFUS "' + GRD_DIFFUS + '"'
            ' -SOLARCONST ' + str(pars['SOLARCONST'])
            + ' -LOCALSVF ' + str(pars['LOCALSVF'])
            + ' -UNITS 1 -SHADOW ' + str(pars['SHADOW']) + ' ' + LocationString
            + ' -PERIOD 1 -HOUR_RANGE_MIN ' + str(hour_range_min)
            + ' -HOUR_RANGE_MAX ' + str(hour_range_max)
            + ' -HOUR_STEP ' + str(pars['Solar_hour_step'])
            + ' -DAY 2000-' + mm + '-' + str(Day + 1)
            + ' -METHOD '     + str(pars['METHOD'])
            + ' -ATMOSPHERE ' + str(pars['ATMOSPHERE'])
            + ' -PRESSURE '   + str(pars['PRESSURE'])
            + ' -WATER '      + str(pars['WATER'])
            + ' -DUST '       + str(pars['DUST'])
            + ' -LUMPED '     + str(pars['LUMPED']))


def _solar_noveg_daily(pars, Month, Day, DTM, LocationString):
    mm = f"{Month:02d}"
    dd = f"{Day:02d}"
    out_dir = pars['GISDir'] + '/PotentialSolar/Daily'
    os.makedirs(out_dir, exist_ok=True)
    GRD_DEM    = pars['GISDir'] + '/DTM.tif'
    GRD_SVF    = pars['GISDir'] + '/SkyView_noVeg.tif'
    GRD_DIRECT = out_dir + '/' + mm + '-' + dd + '_direct_noVeg.tif'
    GRD_DIFFUS = out_dir + '/' + mm + '-' + dd + '_diffuse_noVeg.tif'

    if os.path.exists(GRD_DIRECT) and os.path.exists(GRD_DIFFUS) and not pars['Overwrite']:
        return
    print('Creating ' + GRD_DIRECT + ' and ' + GRD_DIFFUS)
    cmd = _solar_cmd_base(pars, GRD_DEM, GRD_SVF, GRD_DIRECT, GRD_DIFFUS,
                          LocationString, mm, Day, 0, 24)
    exec_cmd(cmd, pars['Verbose'])
    for grd in (GRD_DIRECT, GRD_DIFFUS):
        Data = ReadRaster(grd, pars['Verbose'])
        Data[np.isnan(DTM)] = nodataval
        WriteRasterMatch(Data, grd, grd, nodataval, pars['CreatePyramids'], pars['Verbose'])


def _solar_withveg_daily(pars, Month, Day, c, VegRange, DTM, Cover, LocationString):
    mm = f"{Month:02d}"
    dd = f"{Day:02d}"
    out_dir = pars['GISDir'] + '/PotentialSolar/Daily'
    os.makedirs(out_dir, exist_ok=True)
    GRD_DEM    = pars['GISDir'] + '/DSM_vcat_' + str(c) + '.tif'
    GRD_SVF    = pars['GISDir'] + '/SkyView_withVeg_vcat_' + str(c) + '.tif'
    GRD_DIRECT = out_dir + '/' + mm + '-' + dd + '_direct_withVeg_vcat_' + str(c) + '.tif'
    GRD_DIFFUS = out_dir + '/' + mm + '-' + dd + '_diffuse_withVeg_vcat_' + str(c) + '.tif'

    if os.path.exists(GRD_DIRECT) and os.path.exists(GRD_DIFFUS) and not pars['Overwrite']:
        return
    print('Creating ' + GRD_DIRECT + ' and ' + GRD_DIFFUS)
    cmd = _solar_cmd_base(pars, GRD_DEM, GRD_SVF, GRD_DIRECT, GRD_DIFFUS,
                          LocationString, mm, Day, 0, 24)
    exec_cmd(cmd, pars['Verbose'])

    PSolar = ReadRaster(GRD_DIFFUS, pars['Verbose'])
    locs = ndimage.binary_dilation(np.logical_and(Cover > VegRange[0], Cover <= VegRange[1]))
    PSolar[locs] = nodataval
    PSolar[np.isnan(DTM)] = 0
    WriteRasterMatch(PSolar, GRD_DIFFUS, GRD_DIFFUS, nodataval, False, pars['Verbose'])

    cmd = ('"' + pars['SagaGISLoc'].replace('\\', '/') + '/saga_cmd" grid_tools 29'
           ' -GROW 1.2 -INPUT "' + GRD_DIFFUS + '" -RESULT "' + GRD_DIFFUS + '"')
    exec_cmd(cmd, pars['Verbose'])

    Data = ReadRaster(GRD_DIFFUS, pars['Verbose'])
    Data[np.isnan(DTM)] = nodataval
    WriteRasterMatch(Data, GRD_DIFFUS, GRD_DIFFUS, nodataval, pars['CreatePyramids'], pars['Verbose'])

    Data = ReadRaster(GRD_DIRECT, pars['Verbose'])
    Data[np.isnan(DTM)] = nodataval
    WriteRasterMatch(Data, GRD_DIRECT, GRD_DIRECT, nodataval, pars['CreatePyramids'], pars['Verbose'])


def get_potential_solar_maps_parallel(pars):
    if pars['Solar_output_step'] != 1:
        # Fall back to the serial version for hourly mode -- the parallel
        # implementation here only handles the daily case (Solar_output_step=1).
        print("Solar_output_step != 1 -- falling back to serial GIS.GetPotentialSolarMaps")
        GIS.GetPotentialSolarMaps(pars)
        return

    DTM = ReadRaster(pars['GISDir'] + '/DTM.tif', pars['Verbose'])
    Cover = ReadRaster(pars['GISDir'] + '/Cover.tif', pars['Verbose'])
    Cover[Cover < 0] = 0
    Cover[np.isnan(Cover)] = 0

    LocationString = _build_location_string(pars)

    tasks = []
    for Month in pars['Solar_Months']:
        for Day in pars['Solar_Days']:
            tasks.append(('noveg', Month, Day, None, None))
            for c, VegRange in enumerate(pars['VegCoverCategories']):
                tasks.append(('withveg', Month, Day, c, VegRange))

    def run_task(task):
        kind, Month, Day, c, VegRange = task
        if kind == 'noveg':
            _solar_noveg_daily(pars, Month, Day, DTM, LocationString)
        else:
            _solar_withveg_daily(pars, Month, Day, c, VegRange, DTM, Cover, LocationString)

    workers = min(pars['MaxParallelSagaJobs'], len(tasks))
    print(f"Dispatching {len(tasks)} solar-map jobs across {workers} workers")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(run_task, t) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            f.result()


# ==================== Longwave enhancement: parallel ====================

def _longwave_one_month(pars, root, file, DTM, VegHT):
    """Process one ``_direct_noVeg.tif`` file -- equivalent to one iteration
    of the loop body in Indexes.GetLongwaveEnhancementMaps."""
    from PIL import Image

    psolar_base = root + '/' + file.replace('_direct_noVeg.tif', '')
    OFName = (root.replace(pars['GISDir'], pars['IndexDir'])
                  .replace('PotentialSolar', 'LWI')
              + '/' + file.replace('_direct_noVeg.tif', '.tif'))
    IndexDir = os.path.dirname(OFName)
    os.makedirs(IndexDir, exist_ok=True)

    if os.path.exists(OFName) and not pars['Overwrite']:
        return

    print('Creating ' + OFName)

    PSolar_0 = ReadRaster(psolar_base + '_direct_noVeg.tif', pars['Verbose'])
    LWI = np.zeros(PSolar_0.shape)

    for c, VegRange in enumerate(pars['VegCoverCategories']):
        PSolar = ReadRaster(psolar_base + '_direct_withVeg_vcat_' + str(c) + '.tif',
                             pars['Verbose'])
        T = pars['Transmittances'][c]
        LWI = np.maximum(LWI, T * (PSolar * np.maximum(0, 1 - VegHT / pars['LWIHeightRed']) - PSolar_0))

    LWI[VegHT > 2] = nodataval
    LWI[np.isnan(DTM)] = 0

    WriteRasterMatch(LWI, OFName, pars['GISDir'] + '/DTM.tif',
                     nodataval, False, pars['Verbose'])

    cmd = ('"' + pars['SagaGISLoc'].replace('\\', '/') + '/saga_cmd" grid_tools 29'
           ' -GROW 1.2 -INPUT "' + OFName + '" -RESULT "' + OFName + '"')
    exec_cmd(cmd, pars['Verbose'])

    LWI = ReadRaster(OFName, pars['Verbose'])
    rows, cols = LWI.shape
    PSolar_Flat = ReadRaster(psolar_base + '_direct_flat.tif', pars['Verbose'])
    PSolar_Flat = np.array(Image.fromarray(PSolar_Flat).resize(size=(cols, rows)))

    LWI = np.array(Image.fromarray(LWI).resize(size=(round(rows / pars['LWIResizeFactor']),
                                                       round(cols / pars['LWIResizeFactor'])))
                                            .resize(size=(cols, rows)))
    LWI[LWI < 0] = 0
    LWI = LWI / PSolar_Flat

    LWI[np.isnan(DTM)] = nodataval
    WriteRasterMatch(LWI, OFName, pars['GISDir'] + '/DTM.tif',
                     nodataval, pars['CreatePyramids'], pars['Verbose'])


def get_longwave_enhancement_maps_parallel(pars):
    DTM = ReadRaster(pars['GISDir'] + '/DTM.tif', pars['Verbose'])
    VegHT = ReadRaster(pars['GISDir'] + '/VegHT.tif', pars['Verbose'])
    VegHT[VegHT < 0] = 0
    VegHT[np.isnan(VegHT)] = 0

    tasks = []
    for root, _, files in os.walk(pars['GISDir'] + '/PotentialSolar'):
        for file in files:
            if file.endswith('_direct_noVeg.tif'):
                tasks.append((root, file))

    if not tasks:
        print("No _direct_noVeg.tif files found under PotentialSolar/. "
              "Did the solar step finish?")
        return

    workers = min(pars['MaxParallelSagaJobs'], len(tasks))
    print(f"Dispatching {len(tasks)} longwave-enhancement jobs across {workers} workers")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_longwave_one_month, pars, r, f, DTM, VegHT) for (r, f) in tasks]
        for f in concurrent.futures.as_completed(futures):
            f.result()


# ==================== Main: same flow as ComputeRadiationIndexes.py ====================

if __name__ == '__main__':
    # Stage 1: skyview
    get_skyview_maps_parallel(pars)
    Indexes.GetBelowCanopySkyviewFactor(pars)

# ==================== Potential Solar parameters ====================

pars['Solar_output_step'] = 1
pars['Solar_hour_step']   = 0.25
pars['Solar_Months']      = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
pars['Solar_Days']        = [1]
pars['ConstantLatitude']  = True
pars['SOLARCONST']        = 1367
pars['LOCALSVF']          = 1
pars['SHADOW']            = 1
pars['METHOD']            = 2
pars['ATMOSPHERE']        = 12000
pars['PRESSURE']          = 1013
pars['WATER']             = 1.68
pars['DUST']              = 100
pars['LUMPED']            = 70

if __name__ == '__main__':
    # Stage 2: potential solar
    get_potential_solar_maps_parallel(pars)
    Indexes.GetBelowCanopySFIMaps(pars)

# ==================== Longwave Enhancement parameters ====================

pars['LWIHeightRed']     = 3
pars['LWIResizeFactor']  = 2

if __name__ == '__main__':
    # Stage 3: longwave enhancement
    get_longwave_enhancement_maps_parallel(pars)
