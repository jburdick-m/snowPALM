import sys
import os
sys.path.insert(1, 'ProgramFiles')
import GIS
import Indexes
pars = {}

#################### General Parameters ####################

pars['Verbose'] = False                          # Verbose output
pars['Overwrite'] = True                        # Overwrite Files?
pars['CreatePyramids'] = False                   # Create pyramids for faster display
pars['SagaGISLoc'] = r'C:\saga-8.2.0_x64'        # Location of Saga GIS Executable

# Compute all indexes for different classes individually, and adjust indexes according to canopy thickness (move to separate program)
pars['VegCoverCategories'] = [[80, 100], [60, 80], [40, 60], [20, 40], [0, 20]] 
pars['Transmittances'] = [0.1, 0.3, 0.5, 0.7, 0.9]                                     
pars['CanopyTransFactor'] = 0.5                                                 # Canopy transmission coefficient

pars['GISDir'] = os.getcwd() + '/Preprocess/GIS'                                 # GIS Directory
pars['IndexDir'] = os.getcwd() + '/Preprocess/Indexes'       

#################### Compute Wind Effect Maps (note: requires a Forcing Set be generated) ####################

# GIS Wind Effect parameters (see https://saga-gis.sourceforge.io/saga_tool_doc/2.2.1/ta_morphometry_15.html)

pars['WindDirs'] = range(0, 360, 30)                            # Directions to compute wind index maps for
pars['MAXDIST'] = 0.1                                           # Search Distance [km]
pars['OLDVER'] = 0                                              # Old Version [0: False, 1: True]
# The following parameters are only used if OLDVER is set to 0
pars['ACCEL'] = 1.5                                             # Accelaration
pars['PYRAMIDS'] = 0                                            # Elevation Averaging [0: False, 1: True]

# Wind Index Parameters

pars['StartYear'] = 2016                    # Start Year
pars['StartMonth'] = 10                     # Start Month
pars['EndYear'] = 2022                      # End Year
pars['EndMonth'] = 9                        # End Month
pars['ForcingSet'] = 'DailyNLDASData'
# Forcing set used to create wind index maps (wind direction, as well as precipitation and temperature thresholds could be used)

pars['IncludeAllDays'] = False              # Whether to create a wind map each day regardless of whether there is snowfall
# The following are only used if pars['IncludeAllDays'] is False
pars['TThresh'] = 10                        # Do not create maps for days where T > TThresh (e.g. since it is too warm for snowfall)
pars['PThresh'] = 10                        # Do not create maps for days where P < PThresh (e.g. since there is lighter or no snowfall)
pars['WindDirs'] = range(0, 360, 30)        # Directions to compute wind index maps for
pars['WindEffectResizeFactor'] = 3          # Filter applied to soften edges around canopy
                    
pars['ForceDirection'] = True
pars['WindDir'] = 210                       # Wind direction applied to all maps (only if pars['ForceDirection'] is true)
pars['WindVegInfluence'] = 1                # Reduction of wind effect under canopy (0: no reduction, 1: full reduction, >1: reduction near canopy as well)
pars['ForceUnity'] = True                   # Force all maps to have an average of 1

pars['ForcingDir'] = os.getcwd() + '/Preprocess/Forcing/' + pars['ForcingSet']   # Forcing Directory

if __name__ == '__main__':
    # Compute Saga GIS Wind Index maps for different canopy cover classes
    GIS.GetWindIndexMaps(pars)
    # Put these together and generate the necessary map for each day that has significant snowfall
    Indexes.GetSnowfallDistributionMults(pars)
