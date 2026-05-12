import sys
import os
from pathlib import Path

# Add the SnowPALM_model directory (sibling of this script's parent) to sys.path
if "__file__" in globals():
    current_file_dir = Path(__file__).resolve().parent
target_path = current_file_dir.parent / "SnowPALM_model"
if target_path.exists() and str(target_path) not in sys.path:
    sys.path.insert(1, str(target_path))
else:
    print(f"Path already in sys.path or directory not found: {target_path}")

import dateutil.parser
import Output
print(f"Using Output from: {Output.__file__}")
program_pars = {}

# Simulation Parameters

program_pars['SimulationName'] = sys.argv[1]        # Name of simulation
program_pars['Verbose'] = False                     # Verbose Output

program_pars['NProcesses'] = 8     # Match your CPU core count; bump up on a beefy VM

StartDate_str = sys.argv[2]
EndDate_str = sys.argv[3]
program_pars['StartDate'] = dateutil.parser.parse(StartDate_str)        # Simulation Start Date
program_pars['EndDate'] = dateutil.parser.parse(EndDate_str)            # Simulation End Date

program_pars['VarList'] = sys.argv[4]

# Additional Parameters (probably no change)

program_pars['ModelDir'] = 'Model/' + program_pars['SimulationName']                # Directory where model files are saved
program_pars['OutputDir'] = 'Output/' + program_pars['SimulationName']              # Directory where output files are saved
program_pars['least_significant_digit'] = 3                                         # Smallest decimal place in unpacked data that is a reliable value for nc data
program_pars['CreatePyramids'] = False                                              # Create pyramids for faster display (only affects tile maps)

## Call function to Output Data
if __name__ == '__main__':
    Output.getData(program_pars)
    