#!/usr/bin/env python3


## !!!!!!!!!!!!!!!!!!!! Note !!!!!!!!!!!!!!!!!!!! ##
# This script is the main file for the pseudo EMG onset detection demo with orthosis v2 at BMT 2023 conference (25.09 to 28.09)
# Command to setup motor CAN interface : sudo ip link set can0 up type can bitrate 1000000
## !!!!! ********************************** !!!!! ##

## Orthosis Imports
import signal
## Pseudo EMG Viz Imports
import matplotlib.pyplot as plt
from matplotlib import animation
## General Imports
import multiprocessing as mp
import SharedArray as sa
## Appending the relative path of the root folder
import sys, os
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '../..')))
## Param file import
import param.pseudo_viz_param as param_viz


## Library Imports
# Uncomment the following if you have pip installed the orthosis_lib
from orthosis_lib.orthosis_v2_lib_oop import OrthosisLib
import orthosis_lib.viz_lib as viz_lib
# Uncomment the following otherwise
# from lib.orthosis_lib.orthosis_v2_lib_oop import OrthosisLib
# import lib.orthosis_lib.viz_lib as viz_lib



def runOrthosis():
    """
    This is the main target method for the orthosis thread 
    """
    setattr(orthosis_obj,'is_orthosis_running',True)
    signal.signal(signal.SIGINT, orthosis_obj.signalHandler)
    signal.signal(signal.SIGQUIT, orthosis_obj.signalHandler)
    signal.signal(signal.SIGTSTP, orthosis_obj.signalHandler)

    # Setting zero position for the motor
    orthosis_obj.orthosis_handle.enable_motor()
    pos,_,_ = orthosis_obj.orthosis_handle.set_zero_position()
    setattr(orthosis_obj,'orthosis_pose_desired', pos)
    print("Orthosis Process Ready!!")

    # move to start position first 
    orthosis_obj.move_to_start_position(getattr(orthosis_obj,'fully_extended_pos'))
    print(f"Orthosis moved to its start position!!")
    viz_start_flag[0] = True

    while getattr(orthosis_obj,'is_orthosis_running'):
        orthosis_obj.readValues()
        orthosis_obj.triggeredMotion(onset_detected)
        if getattr(orthosis_obj,'is_verbose'):
            print(f"Trigger         : {getattr(orthosis_obj,'is_triggered')}")
            print(f"Onset Detected  : {onset_detected[0]}")

        # Safe KeyboardInterrupt
        if getattr(orthosis_obj,'safe_interrupt'):
            print("Exiting the orthosis process safely!!")
            orthosis_obj.orthosis_handle.disable_motor()
            break
    # Stopping the experiment
    orthosis_obj.orthosis_handle.disable_motor()

def runViz():
    """
    This is the main target method for the visualisation thread
    """
    while not viz_start_flag[0]:
        pass
    
    emg_pseudo_online, onset_sample_shown, onset_value, emg_norm = viz_lib.loadAndProcessEMGData()
    fig = plt.figure()
    anim = animation.FuncAnimation(fig, viz_lib.updateViz, frames = len(emg_pseudo_online)+1, interval = param_viz.update_interval, blit = False, fargs = (emg_pseudo_online, onset_sample_shown, onset_value, emg_norm, onset_detected))
    plt.show()



if __name__ == "__main__":
    orthosis_obj = OrthosisLib("can0", 0x01, "AK80_6_V1p1", 0.5)

    # Deleting old SharedArrays
    if len(sa.list()) != 0:
        sa.delete("shm://onset")
        sa.delete("shm://start")
    
    # Creating SharedArrays
    onset_detected = sa.create("shm://onset",1)
    viz_start_flag = sa.create("shm://start",1)

    viz_start_flag[0] = False

    # Process 1 - Orthosis thread
    pr_orthosis    = mp.Process(target=runOrthosis)

    # Process 2 - Button press thread
    pr_viz      = mp.Process(target=runViz)


    # Starting the processes
    pr_orthosis.start()
    pr_viz.start()


