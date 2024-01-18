#!/usr/bin/env python3


## !!!!! Important Conventions to keep in mind !!!!! ##
    # When the arm is resting down, the param.position feedbacks 900.0
    # When the arm is up perpendicular to the body, the param.position feedbacks 1800.0
    # As the arm is moving up, the Force values are negative
    # As the arm is moving down, the Force values are positive
## !!!!! ************************************* !!!!! ##

## Orthosis Imports
import serial
## Pseudo EMG Viz Imports
import matplotlib.pyplot as plt
from matplotlib import animation
## General Imports
import threading
## Appending the relative path of the root folder
import sys, os
# sys.path.append('../')
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
## Param file Import
import param.orthosis_param as param            # Param file consisting of variables for the orthosis functioning
import param.pseudo_viz_param as param_viz      # Param file consisiting of variables for visualisation

## Library Imports
# Uncomment the following if you have pip installed the orthosis_lib
import orthosis_lib.orthosis_v1_lib as orthosis_lib
import orthosis_lib.viz_lib as viz_lib
# Uncomment the following otherwise
# import lib.orthosis_lib.orthosis_v1_lib as orthosis_lib
# import lib.orthosis_lib.viz_lib as viz_lib


def runOrthosis(orthosis_handle):
    """
    This is the main target method for the orthosis thread 

    Parameters:
        orthosis_handle : The serial port configuration instance
    """
    param.is_orthosis_running=True
    orthosis_lib.calibrate(orthosis_handle)
    while param.is_orthosis_running:
        orthosis_lib.readValues(orthosis_handle)
        orthosis_lib.triggeredMotion(orthosis_handle)
        if param.is_verbose:
            print(f"Trigger: {param_viz.is_triggered}\n")
            print(f"Onset Detected: {param_viz.onset_detected}\n\n")

def runViz():
    """
    This is the main target method for the visualisation thread
    """
    emg_pseudo_online, onset_sample_shown, onset_value, emg_norm = viz_lib.loadAndProcessEMGData()
    fig = plt.figure()
    anim = animation.FuncAnimation(fig, viz_lib.updateViz, frames = len(emg_pseudo_online)+1, interval = param_viz.update_interval, blit = False, fargs = (emg_pseudo_online, onset_sample_shown, onset_value, emg_norm))
    plt.show()



if __name__ == "__main__":
    ## Configure the serial port
    orthosis_handle = serial.Serial(port=param.orthosis_port_name, baudrate=param.orthosis_baud_rate)
    ## Declaring the orthosis thread
    thr_orthosis = threading.Thread(target=runOrthosis, args=(orthosis_handle,))
    ## Declaring the visualisation thread
    thr_viz = threading.Thread(target=runViz)
    
    ## Starting the threads
    thr_orthosis.start()
    thr_viz.start()


