import sys
import os
sys.path.insert(1, 'ProgramFiles')
from datetime import date
import Initialize
import Model
import ModelPars_posthin

model_pars = ModelPars_posthin.model_pars
program_pars = {}

# Simulation Parameters

program_pars['SimulationName'] = sys.argv[1]            # Name of simulation
program_pars['Verbose'] = True                         # Verbose Output
program_pars['ReinitializeModel'] = True               # Reinitialize Model? (Causes everything for a particular simulation to be overwritten)
program_pars['OverwriteForcing'] = True                # Overwrite preprocessing forcing files?
program_pars['OverwriteIndexes'] = True                # Overwrite preprocessing index files?

program_pars['NProcesses'] = 60                         # Maximum Number of processes used for multiprocessing
program_pars['CreatePyramids'] = False

if program_pars['SimulationName'] == 'EntireArea_Daily_2019':

#    model_pars = ModelPars_station.model_pars
    program_pars['ForcingSetName'] = 'DailyStationData'             # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 1                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = False                       # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2018, 10, 1)                   # Simulation Start Date
    program_pars['EndDate'] = date(2019, 5, 31)                     # Simulation End Date
    program_pars['SimulationType'] = 0                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['MaxChunkSize'] = 25000                            # Maximum size (in pixels) of each model chunk 
    program_pars['UseWindModel'] = True                             # Use Wind Model

if program_pars['SimulationName'] == 'EntireArea_Daily_2020':

#    model_pars = ModelPars_station.model_pars
    program_pars['ForcingSetName'] = 'DailyStationData'             # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 1                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = False                       # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2019, 10, 1)                   # Simulation Start Date
    program_pars['EndDate'] = date(2020, 5, 31)                     # Simulation End Date
    program_pars['SimulationType'] = 0                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['MaxChunkSize'] = 25000                            # Maximum size (in pixels) of each model chunk 
    program_pars['UseWindModel'] = True                             # Use Wind Model
  
if program_pars['SimulationName'] == 'EntireArea_Daily_2021':
    
#    model_pars = ModelPars_station.model_pars
    program_pars['ForcingSetName'] = 'DailyStationData'             # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 1                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = False                       # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2020, 10, 1)                   # Simulation Start Date
    program_pars['EndDate'] = date(2021, 5, 31)                     # Simulation End Date
    program_pars['SimulationType'] = 0                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['MaxChunkSize'] = 25000                            # Maximum size (in pixels) of each model chunk 
    program_pars['UseWindModel'] = True                             # Use Wind Model
    
if program_pars['SimulationName'] == 'EntireArea_Hourly_2022_10_21':
    
#    model_pars = ModelPars_station.model_pars
    program_pars['ForcingSetName'] = 'HourlyNLDASData'              # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 0                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = True                        # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2022, 10, 21)                  # Simulation Start Date
    program_pars['EndDate'] = date(2022, 10, 21)                    # Simulation End Date
    program_pars['SimulationType'] = 0                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['MaxChunkSize'] = 25000                            # Maximum size (in pixels) of each model chunk 
    program_pars['UseWindModel'] = True                             # Use Wind Model

elif program_pars['SimulationName'] == 'SnowtographyArea_Daily_2017_old':
    program_pars['ForcingSetName'] = 'DailyNLDASData'               # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 1                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = False                       # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2016, 10, 1)                   # Simulation Start Date
    program_pars['EndDate'] = date(2017, 9, 30)                     # Simulation End Date
    program_pars['SimulationType'] = 1                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['NSWE'] = [3824754,3824646,470045,470259]        # Spatial Extents of Subset Area
    program_pars['MaxChunkSize'] = 500                              # Maximum size (in pixels) of each model chunk
    program_pars['UseWindModel'] = True                             # Use Wind Model

elif program_pars['SimulationName'] == 'SnowtographyArea_Daily_2019_old':
    program_pars['ForcingSetName'] = 'DailyNLDASData'               # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 1                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = False                       # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2018, 10, 1)                   # Simulation Start Date
    program_pars['EndDate'] = date(2019, 9, 30)                     # Simulation End Date
    program_pars['SimulationType'] = 1                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['NSWE'] = [3824754,3824646,470045,470259]        # Spatial Extents of Subset Area
    program_pars['MaxChunkSize'] = 500                              # Maximum size (in pixels) of each model chunk
    program_pars['UseWindModel'] = True                             # Use Wind Model

elif program_pars['SimulationName'] == 'SnowtographyArea_Daily_1622_old':
    program_pars['ForcingSetName'] = 'DailyNLDASData'               # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 1                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = False                       # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2016, 10, 1)                   # Simulation Start Date
    program_pars['EndDate'] = date(2022, 9, 30)                     # Simulation End Date
    program_pars['SimulationType'] = 1                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['NSWE'] = [3824754,3824646,470045,470259]        # Spatial Extents of Subset Area
    program_pars['MaxChunkSize'] = 500                              # Maximum size (in pixels) of each model chunk
    program_pars['UseWindModel'] = True                             # Use Wind Model


elif program_pars['SimulationName'] == 'SnowtographyArea_Daily_2017':
    program_pars['ForcingSetName'] = 'DailyNLDASData'               # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 1                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = False                       # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2016, 10, 1)                   # Simulation Start Date
    program_pars['EndDate'] = date(2017, 9, 30)                     # Simulation End Date
    program_pars['SimulationType'] = 1                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['NSWE'] = [3824771.409,3824638.684,470138.9939,470231.585]        # Spatial Extents of Subset Area
    program_pars['MaxChunkSize'] = 500                              # Maximum size (in pixels) of each model chunk
    program_pars['UseWindModel'] = True                             # Use Wind Model

elif program_pars['SimulationName'] == 'SnowtographyArea_Daily_2019':
    program_pars['ForcingSetName'] = 'DailyNLDASData'               # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 1                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = False                       # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2018, 10, 1)                   # Simulation Start Date
    program_pars['EndDate'] = date(2019, 9, 30)                     # Simulation End Date
    program_pars['SimulationType'] = 1                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['NSWE'] = [3824771.409,3824638.684,470138.9939,470231.585]        # Spatial Extents of Subset Area
    program_pars['MaxChunkSize'] = 500                              # Maximum size (in pixels) of each model chunk
    program_pars['UseWindModel'] = True                             # Use Wind Model

elif program_pars['SimulationName'] == 'SnowtographyArea_Daily_1622':
    program_pars['ForcingSetName'] = 'DailyNLDASData'               # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 1                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = False                       # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2016, 10, 1)                   # Simulation Start Date
    program_pars['EndDate'] = date(2022, 9, 30)                     # Simulation End Date
    program_pars['SimulationType'] = 1                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['NSWE'] = [3824771.409,3824638.684,470138.9939,470231.585]        # Spatial Extents of Subset Area
    program_pars['MaxChunkSize'] = 500                              # Maximum size (in pixels) of each model chunk
    program_pars['UseWindModel'] = True                             # Use Wind Model


elif program_pars['SimulationName'] == 'POIs_Daily':

    program_pars['ForcingSetName'] = 'DailyNLDASData'               # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 1                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = False                       # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2016, 10, 1)                   # Simulation Start Date
    program_pars['EndDate'] = date(2022, 9, 30)                     # Simulation End Date
    program_pars['SimulationType'] = 2                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['POIDir'] = r'D:\RD_python_wok_3D_veg\LV_site\InputData\POIs'                       # POI directory
    program_pars['UseWindModel'] = True                             # Use Wind Model

elif program_pars['SimulationName'] == 'POIs_Daily2':

    model_pars = ModelPars_station.model_pars
    program_pars['ForcingSetName'] = 'DailyStationData'               # Name of forcing dataset to use as model input
    program_pars['ModelTimestep'] = 1                               # 0: Hourly, 1: Daily
    program_pars['UseHourlySFIFiles'] = False                       # Use hourly solar forcing files (only for hourly model)
    program_pars['StartDate'] = date(2018, 10, 1)                   # Simulation Start Date
    program_pars['EndDate'] = date(2022, 4, 30)                     # Simulation End Date
    program_pars['SimulationType'] = 2                              # 0: Entire Area, 1: Subset Area, 2: POIs only
    program_pars['POIDir'] = '../InputData/POIs'                       # POI directory
    program_pars['UseWindModel'] = True                             # Use Wind Model

# Output Variables
#                            Variable Name                      Short Name (in code)    Units
program_pars['OutVars'] = [ ['Air Temperature',                 'airt',                 'C',            ],
                            ['Wind Speed',                      'wind',                 'm/s'           ],
                            ['Shortwave Radiation',             'srad',                 'W/m2'          ],
                            ['Longwave Radiation',              'lrad',                 'W/m2'          ],
                            ['Vapor Pressure',                  'vapp',                 'Pa'            ],
                            ['Relative Humidity',               'rh',                   '%'             ],
                            ['Rainfall',                        'rainfall',             'mm/timestep'   ],
                            ['Snowfall',                        'snowfall',             'mm/timestep'   ],
                            ['Potential Evapotranspiration',    'PET',                  'mm/timestep'   ], 
                            ['Snow Water Equivalent',           'swe',                  'mm'            ],
                            ['Snow Depth',                      'depth',                'W/m2'          ],
                            ['Snow Density',                    'density',              'W/m2'          ],
                            ['Rain on Snow',                    'rain_on_snow',         'mm/timestep'   ],
                            ['Snowpack Sublimation',            'snowpack_sublimation', 'mm/timestep'   ],
                            ['Snow throughfall',                'tsfall',               'mm/timestep'   ],
                            ['Snow Unload from Canopy',         'snow_unload',          'mm/timestep'   ],
                            ['Melt Drip from Canopy',           'melt_drip',            'mm/timestep'   ],
                            ['Canopy Snow Sublimation',         'canopy_sublimation',   'mm/timestep'   ],
                            ['Canopy Snow Storage',             'canopy_snow_storage',  'mm'            ],
                            ['Snow Melt',                       'melt',                 'mm/timestep'   ],
                            ['Albedo',                          'albedo',               '-'             ],
                            ['Snowpack Temperature',            'Tm',                   'C'             ],
                            ['Surface Temperature',             'Ts',                   'C'             ],
                            ['Net Shortwave Radiation',         'Qsn',                  'W/m2'          ],
                            ['Outgoing Longwave Radiation',     'Qle',                  'W/m2'          ],
                            ['Net Radiation',                   'Qn',                   'W/m2'          ],
                            ['Net Radiation over Snowpack',     'Qn_snow',              'W/m2'          ],
                            ['Sensible Heat Flux',              'Qh',                   'W/m2'          ],
                            ['Ground Heat Flux',                'Qg',                   'W/m2'          ],
                            ['Latent Heat Flux (sublimation)',  'Qe',                   'W/m2'          ],
                            ['Precipitation Heat Flux',         'Qp',                   'W/m2'          ],
                            ['Melt Heat Flux',                  'Qm',                   'W/m2'          ],
                            ['Cold Content',                    'Q',                    'J/m2'          ],
                            ['Surface Layer Soil Temperature',  'T_soil',               'C'             ],
                            ['Surface Layer Soil Ice Content',  'ice_percent_soil',     '%'             ], 
                            ['Actual Evapotranspiration',       'ET',                   'mm/timestep'   ],
                            ['Soil Moisutre Content',           'SMC',                  '%'             ],
                            ['Infiltration Excess Runoff',      'infil_runoff',         'mm/timestep'   ],
                            ['Saturation Excess Runoff',        'sat_runoff',           'mm/timestep'   ],
                            ['Percolation',                     'perc',                 'mm/timestep'   ],
                            ['Infiltration',                    'infiltration',         'mm/timestep'   ],
                            ['Vadose Zone Water Storage',       'x_vadose',             'mm'            ],
                            ['Phreatic Zone Water Storage',     'x_phreatic',           'mm'            ],
                            ['Discharge from Vadose Zone',      'q_vadose',             'mm/timestep'   ],
                            ['Discharge from Phreatic Zone',    'q_phreatic',           'mm/timestep'   ]]
                            
# program_pars['OutVars'] = [ ['Air Temperature',                 'airt',                 'C',            ],
                            # ['Shortwave Radiation',             'srad',                 'W/m2'          ],
                            # ['Snow Water Equivalent',           'swe',                  'mm'            ]]
                            
# Additional Parameters (probably no change)

program_pars['POIForcingInterpMethod'] = 0                                          # Forcing Interpolation for POIs (doesn't affect the results)
                                                                                    # 0: Default (Better for smaller number of POIs), 1: May be better when many POI grids or for small domains
program_pars['GISDir'] = 'Preprocess/GIS'                                           # Directory with preprocessed GIS data
program_pars['IndexDir'] = 'Preprocess/Indexes'                                     # Directory with preprocessed subcanopy indexes
program_pars['ForcingDir'] = 'Preprocess/Forcing/' + program_pars['ForcingSetName'] # Directory with forcing data (clipped at for main model domain)
program_pars['ModelDir'] = 'Model/' + program_pars['SimulationName']                # Directory where model files are saved
program_pars['OutputDir'] = 'Output/' + program_pars['SimulationName']              # Directory where output files are saved
program_pars['least_significant_digit'] = 3                                         # Smallest decimal place in unpacked data that is a reliable value

## Call function to RunModel
if __name__ == '__main__':
    Initialize.Initialize(program_pars)
    Initialize.InterpForcingData(program_pars)
    Initialize.InterpIndexes(program_pars)
    Model.run(program_pars,model_pars)
    