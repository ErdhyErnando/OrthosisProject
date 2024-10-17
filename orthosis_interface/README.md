# orthosis_interface

This project contains files for interfacing with the Orthosis. There are 2 different models of orthosis addressed by this project - orthosis_v1 and orthosis_v2.


## Overview of the project
This project is divided into different directories, each serving a specific purpose in order to facilitate a minimalist and easy-to-comprehend code.
- **lib** <br />
This directory contains all the library files for the project. It is advisable to create separate libraries specific to the purpose and importing it into the main script. 
  - *orthosis_v1_lib.py* <br />
  This file contains all the functions for operating the orthosis_v1.
  - *orthosis_v2_lib.py* <br />
  This file contains all the functions for operating the orthosis_v2.
  - *orthosis_v2_lib_oop.py* <br />
  This file is object-oriented and contains all the methods for operating the orthosis_v2. 
  - *viz_lib.py* <br />
  This file contains all the functions for real-time 2D visualisation of bio-signals.

- **misc** <br />
This directory is meant to contain all the miscellaneous files that need to be imported by the scripts and don't fit into any of the other mainstream directories viz. lib, param or src. However, note that logs and/or collected data should never be added to this or any directory.
  - *command_line_args* <br />
  This sub-directory consists of files with a series of command-line arguments that are to be used while running src/orthosis_error_intro_mp.py file.

- **param** <br />
This directory is meant for storing all the attributes and parameters that would be used inside the main script. It is advisable to have separate param files for each task and importing it into the specific library or main script.
  - *error_param.py* <br />
  This file contains all the parameters used to introduce random errors into orthosis_v1.
  - *error_v2_param.py* <br />
  This file contains all the parameters used to introduce random errors into orthosis_v2.
  - *extTrigger_param.py* <br/>
  This file contains all the parameters to setup a serial port for external trigger for experiments with orthosis_v1.
  - *extTrigger_v2_param.py* <br/>
  This file contains all the parameters to setup a serial port for external trigger for experiments with orthosis_v2.  
  - *orthosis_param.py* <br />
  This file contains all the parameters used in the basic operation of orthosis_v1. 
  - *orthosis_param.py* <br />
  This file contains all the parameters used in the basic operation of orthosis_v2. 
  - *pseudo_viz_param.py* <br />
  This file contains all the parameters used for the visualisation of the pseudo onset detection.
  


- **src** <br />
This directory has all the main scripts for experiments. It is advisable to create separate scripts inside this directory for each experiment or case. This will facilitate proper structuring.
  - *orthosis_basic.py* <br />
  This is the main script for the basic functioning of orthosis_v1. There is an argument parser implemented in this script for accepting run-time arguments via the command line. All the variables are initialised in their respective param files and for the cases where one might want to modify some parameters for the experiment, there is no need to go and edit the corresponding param file.

    For example : 
    ```
    python orthosis_basic.py
    python orthosis_basic.py --intro_errors True --n_trials 30 --epsilon 17 --f_sensitivity 0.05
    python orthosis_basic.py -ie True -e 18
    python orthosis_basic.py --help 

    ```
    The above command will modify these 4 parameters. One needs to mention the flags only for the parameter(s) they want to change. If not mentioned the default value stored in the param file will be chosen. In order to get a list of all the available flags at your disposal use the --help flag.
  
  - *orthosis_error_intro_ijcai.py* <br/>
  This is the main script used to conduct the orthosis_v2 experiments for IJCAI'23 IntEr-HRI competition. This script includes 3 parallel processes - runOrthosis, runButton and runTrigger handling orthosis_v2 movements, button event listener and sending of external trigger bytes resp. This script also accepts runtime arguments which can be listed with the --help flag.
  
    In order to setup the CAN to USB adapter, run the command ``` sudo ip link set can0 up type can bitrate 1000000 ```

  - *orthosis_error_intro_ijcai_oop.py* <br/>
  This script is similar to orthosis_error_intro_ijcai.py but with object-oriented programming.

  - *orthosis_v2_modified.py* <br />
  This script is the modification of the orthosis_error_intro_ijcai_oop.py created by Student Project Group (Sept 2024) which enable the program to connect to orthosis web app. Use this program to test the Orthosis V2 with the dedicated
web app.

  - *orthosis_pseudo_EMG_demo.py* <br />
  This is the main script used for the SummerUni demonstration of Onset detection using the pre-recorded EMG data using orthosis_v1 which took place at the UDE on Aug 2, 2022.

  - *orthosis_error_intro_mp_sophie_patrick.py* <br/>
  This is the main script that was used to run the Student Group 2 experiments (Feb/Mar 2023) using orthosis_v1. This script includes 3 parallel processes - runOrthosis, runButton and runTrigger handling orthosis_v2 movements, button event listener and sending of external trigger bytes resp. In this experiment, EMG was recorded as well as the flexion start, extension start, nominal trial, error, and button press markers.

  - *orthosis_error_intro_mp_variscia.py* <br />
  This is the main script used to conduct experiments pertaining to Variscia Putri's bachelor thesis (Sept 2022) using orthosis_v1. It uses multiprocessing library to spawn 4 independent parallel processes handling orthosis_v1 movements, button event listener, ZMQ server-client communication (system clock synchronisation) and logging respectively. This script also accepts runtime arguments in order to set the experiment parameters and the log filenames. 

    For example:
    ```
    python orthosis_error_intro_mp.py -n 3 -d 0.25 -sn AB12D -es A -eseq S2 -esuf 2H -set 2
    python orthosis_error_intro_mp.py -n 6 -d 0.075 -sn AB12D -es A -eseq S2 -esuf 2H
    python orthosis_error_intro_mp.py --n_errors 6 --duration 0.075 --sub_name AB12D --expt_scenario A --expt_seq S2 --expt_suffix 2H
    python orthosis_error_intro_mp --help

    ```
  - *orthosis_error_intro_modified.py* <br />
  This script is the modification of the orthosis_error_intro_mp_variscia.py created by Student Project Group (Sept 2024) which enable the program to connect to orthosis web app. Use this program to test the Orthosis V1 with the dedicated web app.

  
## Coding Conventions
This section describes the general coding guidelines to follow during development process.
- **Programming Language** <br />
In this project, Python is used as the primary programming Language.
- **Documentation** <br />
For the purpose of better readability and re-usability, it is essential that every script, attribute or method be well documented. In this project, the Google Style Python Docstrings should be used. (Refer : [Google Style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for more information). 
- **Defining a class** <br />
A new class in python requires a class name. Please use Pascal case (MyNewClass) for this purpose.
- **Defining a function or method** <br />
Please use Camel case (myFunc) for this purpose.
- **Declaring a variable or attribute** <br />
Please use Snake case (new_var) for this purpose.


## Hardware Conventions
- **orthosis_v1** <br/>
  - When the arm is fully extended, it corresponds to a raw position of ~900
  - On the contrary, when the arm is flexed, it corresponds to a raw position of ~1800
  - During Flexion (upward motion), the Force values are negative
  - During Extension (downward motion), the Force values are positive

- **orthosis_v2** <br/>
  - Reset the encoder by starting the orthosis at the hardware limit.
  - The fully extended poisition corresponds to 0 degrees
  - The fully flexed position in the experiment's sense corresponds to -90 degrees

  
## Dependencies
- Pyserial (Refer: [Official Site](https://pyserial.readthedocs.io/en/latest/pyserial.html))
- SharedArray (Refer: [Official Site](https://pypi.org/project/SharedArray/))
  - If using a conda environmnent please install the package with: ```conda install -c conda-forge sharedarray```
