#!/usr/bin/env python3

############# NOTE #############
# This script is the main file for the orthosis experiment for the IJCAI'23 competition
# Command to setup motor CAN interface : sudo ip link set can0 up type can bitrate 1000000
################################

import argparse
import serial
import multiprocessing as mp
import time
import SharedArray as sa
# Appending the relative path of the root folder
import sys, os
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
import signal
import param.orthosis_v2_param as param
import param.error_v2_param as param_err
import param.extTrigger_v2_param as param_tr
from motor_driver.canmotorlib import CanMotorController

# Uncomment the following if you have pip installed the orthosis_lib
import orthosis_lib.orthosis_v2_lib as orthosis_lib
# Uncomment the following otherwise
# import lib.orthosis_lib.orthosis_v2_lib as orthosis_lib

def runOrthosis():
    orthosis_handle = CanMotorController(can_socket=param.orthosis_can_socket, motor_id=param.orthosis_motor_id, motor_type=param.orthosis_motor_type, socket_timeout=param.orthosis_socket_timeout)
    param.is_orthosis_running=True
    orthosis_lib.generateErrorSequence()
    disturbing[0] = False
    flag_flexion_done[0] = False
    flag_flexion_started[0] = False
    signal.signal(signal.SIGINT, orthosis_lib.signalHandler)
    signal.signal(signal.SIGQUIT, orthosis_lib.signalHandler)
    signal.signal(signal.SIGTSTP, orthosis_lib.signalHandler)
    # Setting zero position for the motor
    orthosis_handle.enable_motor()
    param.orthosis_pose_desired, vel,eff = orthosis_handle.set_zero_position()
    orthosis_handle.send_deg_command(param.orthosis_position,0,kp=param.kp, kd=param.kd, tau_ff=param.tau_ff)
    print("Orthosis Process Ready!!")
    
    # move to start position first 
    orthosis_lib.move_to_start_position(param.fully_extended_pos, orthosis_handle)
    print(f"Orthosis moved to its start position!!")
            
    while param.is_orthosis_running and param.trial_count < param.n_trials+2:# and move_to_start_pos: # added start pos here 
        orthosis_lib.readValues(orthosis_handle)
        orthosis_lib.runExperimentRandomError(flag_flexion_done, disturbing, flag_flexion_started, flag_normal_trigger)
        if param.is_verbose:
            print(f"Trial Count     : {param.trial_count}")
            # print(f"Error Count     : {param_err.err_count}")
            print(f"Error Seq       : {param_err.err_sequence}")
        # Safe KeyboardInterrupt
        if param.safe_interrupt:
            orthosis_handle.disable_motor()
            break
    # Stopping the experiment
    orthosis_handle.disable_motor()


def runButton():
    button_handle   = serial.Serial(port=param.button_port_name, baudrate=param.button_baud_rate)
    param.is_listener_running= True
    is_pressed[0] = 0.0
    signal.signal(signal.SIGINT, orthosis_lib.signalHandler)
    signal.signal(signal.SIGQUIT, orthosis_lib.signalHandler)
    signal.signal(signal.SIGTSTP, orthosis_lib.signalHandler)
    print("Button Listener Ready!!")
    while param.is_listener_running:
        if button_handle.in_waiting > 0:
            param.button_val = button_handle.read().decode("utf-8")
            if param.button_val == '-':
                is_pressed[0] = True
                print("Button Pressed!!")
            elif param.button_val == ',':
                is_pressed[0] = False
        # Safe Keyboard Interrupt
        if param.safe_interrupt:
            print("Exiting Button process safely!")
            break


def runTrigger():
    arduino_handle = serial.Serial(port=param_tr.arduino_port_name, baudrate=param_tr.arduino_baud_rate)
    param_tr.is_trigger_running = True
    loop_idx = 0
    dt = 0.002
    print("Trigger Process Ready!!")
    prev_flag_flexion_started   = 0.0
    prev_flag_disturbing        = 0.0
    prev_button_state           = 0.0
    prev_normal_trigger         = 0.0
    loop_start_time = time.perf_counter()
    signal.signal(signal.SIGINT, orthosis_lib.signalHandler)
    signal.signal(signal.SIGQUIT, orthosis_lib.signalHandler)
    signal.signal(signal.SIGTSTP, orthosis_lib.signalHandler)
    while param_tr.is_trigger_running:
        loop_idx += 1
        # Flexion or Extension
        if flag_flexion_done[0] == 0.0 and flag_flexion_started[0] == 1.0:
            if prev_flag_flexion_started == 0.0: # If flexion started
                # ard_start_time = time.perf_counter()
                arduino_handle.write(b'F') # flexion trigger
                # print(f"Sending time :{time.perf_counter() - ard_start_time}" )
                print("F trigger is sent")
        elif flag_flexion_done[0] == 1.0 and flag_flexion_started[0] == 0.0:
            if prev_flag_flexion_started == 1.0: # If extension started
                arduino_handle.write(b'E') # extension trigger
                print("E trigger is sent")
        
        # Error Introduced or not
        if disturbing[0] == 1.0 and prev_flag_disturbing == 0.0:
            arduino_handle.write(b'Y') # error command "Y" is send
            print("Error trigger sent")
        elif disturbing[0] == 0.0 and flag_normal_trigger[0] == 1.0 and prev_normal_trigger == 0.0:
            arduino_handle.write(b'N')
            print("Nominal trigger sent")
        
        # Button Press Status
        if is_pressed[0] == 1.0 and prev_button_state == 0.0:
            arduino_handle.write(b'P') # pressed command "P" is send
            print("Button trigger sent")

        prev_flag_flexion_started   = flag_flexion_started[0]
        prev_normal_trigger         = flag_normal_trigger[0]
        prev_flag_disturbing        = disturbing[0]
        prev_button_state           = is_pressed[0]
        
        # Ensuring const. desired loop freq
        while time.perf_counter() - loop_start_time < dt * loop_idx: # This process does not work as intended for freq higher than 500 Hz (some triggers are not sent)
            pass
        # Safe KeyboardInterrupt
        if param.safe_interrupt:
            print("Exiting Trigger process safely!")
            break
        

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser("Custom Error: ")
    parser.add_argument('-n','--n_errors', help='No of errors to introduce')
    parser.add_argument('-d','--duration', help='Duration of error in microseconds')
    parser.add_argument('-v','--verbose', help='Bool to decide if you want to print on console')
    parser.add_argument('-tf','--thr_flex', help='Force threshold for flexion')
    parser.add_argument('-te','--thr_ext', help='Force threshold for extension')


    args = vars(parser.parse_args())
    if args['n_errors'] is not None:
        param_err.num = int(args['n_errors'])
    if args['duration'] is not None:
        param_err.duration = float(args['duration'])
    if args['verbose'] is not None:
        param.is_verbose = bool(args['verbose'])
    if args['thr_flex'] is not None:
        param.eff_thresh_flex = float(args['thr_flex'])
    if args['thr_ext'] is not None:
        param.eff_thresh_ext = float(args['thr_ext'])

    
    # Deleting old SharedArrays
    if len(sa.list()) != 0:
        sa.delete("shm://button")
        sa.delete("shm://flex")
        sa.delete("shm://dist")
        sa.delete("shm://flst")
        sa.delete("shm://notr")

    # Creating SharedArrays
    is_pressed          = sa.create("shm://button",1)
    flag_flexion_done   = sa.create("shm://flex",1)
    disturbing          = sa.create("shm://dist",1)
    flag_flexion_started= sa.create("shm://flst",1)
    flag_normal_trigger = sa.create("shm://notr",1)

    # Process 1 - Orthosis process
    pr_orthosis    = mp.Process(target=runOrthosis)

    # Process 2 - Button press process
    pr_button      = mp.Process(target=runButton)

    # Process 3 - Trigger generating process
    pr_trigger     = mp.Process(target=runTrigger)

    # Starting the processes
    pr_orthosis.start()
    pr_button.start()
    pr_trigger.start()
