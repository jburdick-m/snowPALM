import sys
import os
sys.path.insert(1, 'ProgramFiles')
import GIS
import Indexes
pars = {}

#################### General Parameters ####################

pars['Verbose'] = False                                 # Verbose output
pars['Overwrite'] = True                               # Overwrite Files?
pars['CreatePyramids'] = True                          # Create pyramids for faster display 

# Get Canopy transmittance estimates
import Transmittances
pars['VegCoverCategories'], pars['Transmittances'], pars['CanopyTransFactor'] = Transmittances.get_trans()

pars['GISDir'] = os.getcwd() + '/Preprocess/GIS'        # GIS Directory
pars['IndexDir'] = os.getcwd() + '/Preprocess/Indexes'  # Processed Index Directory

#################### Get Spatial Data ####################

# Elevation raster to get data from
pars['DTM_File'] = r'D:\RD_python_wok_3D_veg\CS_site\InputData\SpatialData\Bare_Earth.tif'
# Low Res DTM (needed here because high res dem does not extend beyond model boundaries (so has edge effects))
pars['DTM_LoRes_File'] = r'D:\RD_python_wok_3D_veg\CS_site\InputData\SpatialData\LoResDTM.tif'
# Canopy height raster to get data from
pars['VegHT_File'] = r'D:\RD_python_wok_3D_veg\CS_site\InputData\SpatialData\Canopy_Height_postthin.tif'
# Canopy cover raster to get data from
pars['VegCover_File'] = r'D:\RD_python_wok_3D_veg\CS_site\InputData\SpatialData\Closure_postthin.tif'
# Cutline file to clip out shape (will only be used if pars['Cutline_File'] is not an empty string)
pars['Cutline_File'] = r'D:\RD_python_wok_3D_veg\CS_site\InputData\SpatialData\Boundary\TNC_Chimney_Springs_Project_Boundary.shp'

pars['NSWE'] = [3906043, 3900519, 435636, 440479]   # Spatial Extents
pars['UseOriginalPixels'] = True                    # Force model boundaries to accomodate existing  pixels

# The following parameters are only used if UseOriginalPixels is set to False
pars['Target_SRS'] = 'EPSG:31966'                       # Spatial Reference System (Proj4)
pars['CellSize'] = 1                                    # Model Cell Size
pars['CellSize_LowRes'] = 30                            # Low resolution cell size (for interpolation of forcing data)
pars['Resample'] = 'average'                            # Resampling Method (near(default) bilinear, cubic, cubicspline, lanczos, 
                                                        # average, rms, mode, max, min, med, Q1, Q3, sum)

if __name__ == '__main__':
    GIS.GetSpatialData(pars)

#################### Compute Leaf Area Index Map ####################

pars['LAI_ref'] = 6                                # Reference LAI
pars['H_ref'] = 30                                  # Reference Canopy Height
pars['LAI_exp'] = 0.5                               # Exponent applied to Canopy Height Adjustment

if __name__ == '__main__':
    Indexes.GetVerticalLAI(pars)