import sys
import os
from pathlib import Path

# Add the SnowPALM_model directory (sibling of this script's parent) to sys.path
# so `import Forcing` picks up the maintained module, not a stale copy elsewhere.
if "__file__" in globals():
    current_file_dir = Path(__file__).resolve().parent
target_path = current_file_dir.parent / "SnowPALM_model"
if target_path.exists() and str(target_path) not in sys.path:
    sys.path.insert(1, str(target_path))
else:
    print(f"Path already in sys.path or directory not found: {target_path}")
import Forcing
print(f"Using Forcing from: {Forcing.__file__}")
pars = {}

#################### General Parameters ####################

pars['Verbose'] = False                                # Verbose output
#pars['GriddedForcingDir'] = r'Z:\GriddedForcing'  # Directory containing gridded forcing data

#pars['GriddedForcingDir'] = '../../GriddedForcing'     # Directory containing gridded forcing data
pars['GriddedForcingDir'] = str(Path(__file__).resolve().parents[4] / 'GriddedForcing')   # Directory containing gridded forcing data (resolved relative to this script: ChapmanR1 -> contents -> data -> Model_Package -> repo root)

#    'GriddedForcing'     # Directory containing gridded forcing data

# Note: Existing files will always be overwritten!!!

pars['prism_ppt_version'] = 3                   # PRISM Precip version
pars['prism_tmean_version'] = 3                 # PRISM TMean version
pars['PRISMLapsePX'] = 3                        # Number of surrounding rows and columns to calclate local lapse rates (1 implies 9 pixels, 2 implies 25 pixels, 3 implies 49 pixels ...)
pars['NLDASResamplingMethod'] = 'bilinear'      # Resampling method applied to NLDAS data
pars['least_significant_digit'] = 3             # Smallest decimal place in unpacked data that is a reliable value

pars['ForcingSetName'] = sys.argv[1]
pars['StartYear'] = eval(sys.argv[2])
pars['StartMonth'] = eval(sys.argv[3])
pars['EndYear'] = eval(sys.argv[4])
pars['EndMonth'] = eval(sys.argv[5])

#################### Get Forcing Data ####################

pars['UTCOffset'] = -7                      # Local UTC offset (for NLDAS data)

if pars['ForcingSetName'] == 'DailyNLDASData':
    # Daily forcing files (needed if using Data Source = 1 (Local Station))
    pars['DailyForcingFile'] = r'D:\RD_python_wok_3D_veg\CS_site\InputData\ForcingData\CSPPMTimeseries_da_04_21_2023_with_snow_rain_rates_s0.csv'
#    pars['DailyForcingFile'] = r'D:\Three_D_vegetation_structure_impact\python_snowpalm_work\BB_site\InputData\ForcingData\BBPPMTimeseries_da_02_14_2023_with_snow_rain_frac_s4.csv'
    # Monthly forcing files (needed for Lapse Rates = 2 (PRISM lapse rate corrected to station data))
    pars['MonthlyForcingFile'] =r'D:\RD_python_wok_3D_veg\CS_site\InputData\ForcingData\ChimneySpringsMonthlyForcing_vRD.csv'
    pars['DataSource'] = 1                      # 0: NLDAS, 1: Local Station
    pars['FillWithNLDAS'] = False                # Fill Missing Station Data with NLDAS data (only when station data is used)
    pars['ApplyPPTLapseRate'] = 2               # Apply monthly lapse rate precipitation correction (0: None, 1: PRISM-based, 2: PRISM-based lapse rate with station based correction)
    pars['ApplyAirTLapseRate'] = 2              # Apply monthly lapse rate temperature correction (0: None, 1: PRISM-based, 2: PRISM-based lapse rate with station based correction)
    pars['OutputTimestep'] = 1                  # 0: Hourly, 1: Daily

elif pars['ForcingSetName'] == 'DailyNLDASData2':
    # Daily forcing files (needed if using Data Source = 1 (Local Station))
    pars['DailyForcingFile'] = ''
    # Monthly forcing files (needed for Lapse Rates = 2 (PRISM lapse rate corrected to station data))
    pars['MonthlyForcingFile'] = ''
    pars['DataSource'] = 0                      # 0: NLDAS, 1: Local Station
    pars['FillWithNLDAS'] = True                # Fill Missing Station Data with NLDAS data (only when station data is used)
    pars['ApplyPPTLapseRate'] = 1               # Apply monthly lapse rate precipitation correction (0: None, 1: PRISM-based, 2: PRISM-based lapse rate with station based correction)
    pars['ApplyAirTLapseRate'] = 1              # Apply monthly lapse rate temperature correction (0: None, 1: PRISM-based, 2: PRISM-based lapse rate with station based correction)
    pars['OutputTimestep'] = 1                  # 0: Hourly, 1: Daily

elif pars['ForcingSetName'] == 'DailyNLDASData3':
    # Daily forcing files (needed if using Data Source = 1 (Local Station))
    pars['DailyForcingFile'] = r'InputData\ForcingData\BBPPMTimeseries_da_02_14_2023_with_snow_rain_frac_s4.csv'
    # Monthly forcing files (needed for Lapse Rates = 2 (PRISM lapse rate corrected to station data))
    pars['MonthlyForcingFile'] = ''
    pars['DataSource'] = 1                      # 0: NLDAS, 1: Local Station
    pars['FillWithNLDAS'] = False                # Fill Missing Station Data with NLDAS data (only when station data is used)
    pars['ApplyPPTLapseRate'] = 0               # Apply monthly lapse rate precipitation correction (0: None, 1: PRISM-based, 2: PRISM-based lapse rate with station based correction)
    pars['ApplyAirTLapseRate'] = 0              # Apply monthly lapse rate temperature correction (0: None, 1: PRISM-based, 2: PRISM-based lapse rate with station based correction)
    pars['OutputTimestep'] = 1                  # 0: Hourly, 1: Daily

elif pars['ForcingSetName'] == 'HourlyNLDASData':
    # Daily forcing files (needed if using Data Source = 1 (Local Station))
#    pars['HourlyForcingFile'] = r'D:\Three_D_vegetation_structure_impact\python_snowpalm_work\BB_site\InputData\ForcingData\BBPPMTimeseries_latest_01_17_2022_step_1.csv'
    pars['HourlyForcingFile'] = r'D:\Three_D_vegetation_structure_impact\python_snowpalm_work\BB_site\InputData\ForcingData\BBPPMTimeseries_02_09_2023.csv'
    # Monthly forcing files (needed for Lapse Rates = 2 (PRISM lapse rate corrected to station data))
    pars['MonthlyForcingFile'] = ''
    pars['DataSource'] = 1                      # 0: NLDAS, 1: Local Station
    pars['FillWithNLDAS'] = False                # Fill Missing Station Data with NLDAS data (only when station data is used)
    pars['ApplyPPTLapseRate'] = 0               # Apply monthly lapse rate precipitation correction (0: None, 1: PRISM-based, 2: PRISM-based lapse rate with station based correction)
    pars['ApplyAirTLapseRate'] = 0              # Apply monthly lapse rate temperature correction (0: None, 1: PRISM-based, 2: PRISM-based lapse rate with station based correction)
    pars['OutputTimestep'] = 0                  # 0: Hourly, 1: Daily

elif pars['ForcingSetName'] == 'DailyStationData':

    # Daily forcing files (needed if using Data Source = 1 (Local Station))
    pars['DailyForcingFile'] = 'InputData/ForcingValidationData/BakerButteDailyForcing.csv'
    # Monthly forcing files (needed for Lapse Rates = 2 (PRISM lapse rate corrected to station data))
    pars['MonthlyForcingFile'] = 'InputData/ForcingValidationData/BakerButteMonthlyForcing.csv'
    pars['DataSource'] = 1                      # 0: NLDAS, 1: Local Station
    pars['FillWithNLDAS'] = True                # Fill Missing Station Data with NLDAS data
    pars['ApplyPPTLapseRate'] = 2               # Apply monthly lapse rate precipitation correction (0: None, 1: PRISM-based, 2: PRISM-based lapse rate with station based correction)
    pars['ApplyAirTLapseRate'] = 2              # Apply monthly lapse rate temperature correction (0: None, 1: PRISM-based, 2: PRISM-based lapse rate with station based correction)
    pars['OutputTimestep'] = 1                  # 0: Hourly, 1: Daily
    
    
pars['LoResDTMFile'] = os.getcwd() + '/Preprocess/GIS/DTM_small.tif'            # Low Resolution DTM (defines grid and lapse rates for forcing data)
#pars['NLDASForcingDir'] = pars['GriddedForcingDir'] + '/NLDAS'                  # Path to NLDAS Data Directory
#pars['PRISMForcingDir'] = pars['GriddedForcingDir'] + '/PRISM'

#pars['NLDASForcingDir'] = r'Y:\GriddedForcing\NLDAS'
#pars['PRISMForcingDir'] = r'Y:\GriddedForcing\PRISM'

pars['NLDASForcingDir'] = pars['GriddedForcingDir'] + '/NLDAS'                  # Path to NLDAS Data Directory
pars['PRISMForcingDir'] = pars['GriddedForcingDir'] + '/PRISM'



#pars['HourlyForcingFileDir'] =r'D:\Three_D_vegetation_structure_impact\python_snowpalm_work\BB_site\InputData\ForcingData'
pars['DailyForcingFileDir'] =r'D:\RD_python_wok_3D_veg\CS_site\InputData\ForcingData'

pars['OFDir'] = os.getcwd() + '/Preprocess/Forcing/' + pars['ForcingSetName']   # Output Directory

if __name__ == '__main__':
    Forcing.GetForcingData(pars)