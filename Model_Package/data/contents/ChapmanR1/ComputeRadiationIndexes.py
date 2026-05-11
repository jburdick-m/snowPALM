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

pars['Verbose'] = False                          # Verbose output
pars['Overwrite'] = True                        # Overwrite Files?
pars['CreatePyramids'] = False                   # Create pyramids for faster display
pars['SagaGISLoc'] = "C:\\Users\\jburdick\\saga-9.12.2_msw"        # Location of Saga GIS Executable

# Compute all indexes for different classes individually, and adjust indexes according to canopy thickness (move to separate program)
pars['VegCoverCategories'] = [[80, 100], [60, 80], [40, 60], [20, 40], [0, 20]] 
pars['Transmittances'] = [0.1, 0.3, 0.5, 0.7, 0.9]                                     
pars['CanopyTransFactor'] = 0.5                                                 # Canopy transmission coefficient

pars['GISDir'] = os.getcwd() + '/Preprocess/GIS'                                # GIS Directory
pars['IndexDir'] = os.getcwd() + '/Preprocess/Indexes'                          

#################### Compute Skyview Factor Maps ####################

# Skyview factor parameters (see https://saga-gis.sourceforge.io/saga_tool_doc/2.2.0/ta_lighting_3.html)

pars['RADIUS'] = 200                                            # Maximum Search Radius [m]
pars['METHOD'] = 0                                              # Method (0: multi scale, 1: sectors)
pars['NDIRS'] = 36                                              # Number of sectors
pars['DLEVEL'] = 3                                              # Multi scale factor

if __name__ == '__main__':
    # Compute Saga GIS Skyview Factor Maps for different canopy cover classes
    GIS.GetSkyViewMaps(pars)
    # Put these together into a single map
    Indexes.GetBelowCanopySkyviewFactor(pars)
 
#################### Compute Potential Solar Maps ####################

# Potential solar radiation parameters (see https://saga-gis.sourceforge.io/saga_tool_doc/2.2.2/ta_lighting_2.html)

pars['Solar_output_step'] = 1                                   # 0: hourly solar maps 1: daily solar maps
pars['Solar_hour_step'] = 0.5                                  # Time step for SFI calculation [h]
pars['Solar_Months'] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # Months to compute SFI for
pars['Solar_Days'] = [1]                                        # Days in Months to compute SFI for
pars['ConstantLatitude'] = True                                 # Set this to True to speed up processing for small areas
pars['SOLARCONST'] = 1367                                       # Solar Constant [W / m2]
pars['LOCALSVF'] = 1                                            # Use Local skyview Factor (0: False, 1: True)
pars['SHADOW'] = 1                                              # Shadow type (0: slim, 1: fat, 2: none)
pars['METHOD'] = 2                                              # 0: Height of Atmosphere and Vapour Pressure
                                                                # 1: Air Pressure, Water and Dust Content
                                                                # 2: Lumped Atmospheric Transmittance
                                                                # 3: Hofierka and Suri
# The following parameters are only used as applicable
pars['ATMOSPHERE'] = 12000                                      # Height of Atmosphere [m]
pars['PRESSURE'] = 1013                                         # Barometric Pressure [mbar]
pars['WATER'] = 1.68                                            # Water Content [cm]
pars['DUST'] = 100                                              # Dust [ppm]
pars['LUMPED'] = 70                                             # Lumped atmospheric transmittance [percent]

if __name__ == '__main__':
    # Compute Saga GIS Potential Solar maps for different canopy cover classes
    GIS.GetPotentialSolarMaps(pars)
    # Put these together and create SFI Maps
    Indexes.GetBelowCanopySFIMaps(pars)

#################### Compute Longwave Enhancement Maps ####################

pars['LWIHeightRed'] = 3                   # Maximum height of canopy where additional longwave enhancement is observed [m]
pars['LWIResizeFactor'] = 2                # Filter applied to enlarge LWI enhancement zones

if __name__ == '__main__':
    # Compute Longwave Enhance Maps using Top of Canopy Solar Forcing Maps
    Indexes.GetLongwaveEnhancementMaps(pars)