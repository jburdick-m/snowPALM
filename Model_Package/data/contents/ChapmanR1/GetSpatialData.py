import sys
from pathlib import Path
import os
#add SnowPALM_model dir to path
if "__file__" in globals():
    current_file_dir = Path(__file__).resolve().parent
# This assumes SnowPALM_model is one level up from this script
target_path = current_file_dir.parent / "SnowPALM_model"
# Add to sys.path if the directory exists and isn't already there
if target_path.exists() and str(target_path) not in sys.path:
    sys.path.insert(1, str(target_path))
    print(f"Added to path: {target_path}")
else:
    print(f"Path already in sys.path or directory not found: {target_path}")
import GIS
print('imported_GIS')
import Indexes
print('imported Indexes')
pars = {}

#################### General Parameters ####################

pars['Verbose'] = True                                 # Verbose output
pars['Overwrite'] = True                               # Overwrite Files?
pars['CreatePyramids'] = False                          # Create pyramids for faster display 

# Compute all indexes for different classes individually, and adjust indexes according to canopy thickness (move to separate program)
pars['VegCoverCategories'] = [[80, 100], [60, 80], [40, 60], [20, 40], [0, 20]] 
pars['Transmittances'] = [0.1, 0.3, 0.5, 0.7, 0.9]                                     
pars['CanopyTransFactor'] = 0.5                                                 # Canopy transmission coefficient

pars['GISDir'] = os.getcwd() + '/Preprocess/GIS'        # GIS Directory
pars['IndexDir'] = os.getcwd() + '/Preprocess/'  # GIS Directory

#################### Get Spatial Data ####################

# Elevation raster to get data from
pars['DTM_File'] = 'InputData/SpatialData/chapman_DEM.tif'
# Canopy height raster to get data from
pars['VegHT_File'] = 'InputData/SpatialData/chapman_CHM_1point5m.tif'
# Canopy cover raster to get data from
pars['VegCover_File'] = 'InputData/SpatialData/chapman_CC_1point5m.tif'
# Cutline file to clip out shape (will only be used if pars['Cutline_File'] is not an empty string)
pars['Cutline_File'] = ''

pars['NSWE'] = [4393023.945, 4391963.945, 711538.86, 712923.86]       # Spatial Extents
pars['UseOriginalPixels'] = False                    # Force model boundaries to accomodate existing  pixels

# The following parameters are only used if UseOriginalPixels is set to False
pars['Target_SRS'] = 'EPSG:26910'                       # Spatial Reference System (Proj4)
pars['CellSize'] = 1.5                                    # Model Cell Size
pars['CellSize_LowRes'] = 30                            # Low resolution cell size (for interpolation of forcing data)
pars['Resample'] = 'average'                            # Resampling Method (near(default) bilinear, cubic, cubicspline, lanczos, 
                                                        # average, rms, mode, max, min, med, Q1, Q3, sum)

if __name__ == '__main__':
    GIS.GetSpatialData(pars)

#################### Compute Leaf Area Index Map ####################

pars['LAI_ref'] = 6                                 # Reference LAI
pars['H_ref'] = 30                                  # Reference Canopy Height
pars['LAI_exp'] = 0.5                               # Exponent on height dependence on LAI

if __name__ == '__main__':
    Indexes.GetVerticalLAI(pars)
print('GetSpatialData.py execution complete.')