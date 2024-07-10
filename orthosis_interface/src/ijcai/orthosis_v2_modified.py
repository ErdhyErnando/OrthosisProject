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
#sys.path.insert(0, abspath(join(dirname(__file__), '..')))
sys.path.insert(0, abspath(join(dirname(__file__), '../..')))
import signal

# Uncomment the following if you have pip installed the orthosis_lib
#from orthosis_lib.orthosis_v2_lib_oop import OrthosisLib, ButtonLib, TrigLib
# Uncomment the following otherwise
from lib.orthosis_lib.orthosis_v2_lib_oop import OrthosisLib, ButtonLib, TrigLib, FlaskZMQPub

def runOrthosis():
    setattr(orthosis_obj,'is_orthosis_running',True)
    orthosis_obj.generateErrorSequence()
    disturbing[0] = False
    flag_flexion_done[0] = False
    flag_flexion_started[0] = False
    signal.signal(signal.SIGINT, orthosis_obj.signalHandler)
    signal.signal(signal.SIGQUIT, orthosis_obj.signalHandler)
    signal.signal(signal.SIGTSTP, orthosis_obj.signalHandler)
    # Setting zero position for the motor
    orthosis_obj.orthosis_handle.enable_motor()
    pos,_,_ = orthosis_obj.orthosis_handle.set_zero_position()
    setattr(orthosis_obj,'orthosis_pose_desired', pos)
    print("Orthosis Process Ready!!")
    stop_flag = False
    zmqPub = FlaskZMQPub()
    myLabel = ["orth_pos","orth_des_pos","orth_force","disturb_intro"]
    # move to start position first 
    orthosis_obj.move_to_start_position(getattr(orthosis_obj,'fully_extended_pos'))
    print(f"Orthosis moved to its start position!!")

    # Initialize a list to store execution times
    execution_times = []
    disturb = 0
    prev_trial = -1        
    while getattr(orthosis_obj,'is_orthosis_running') and getattr(orthosis_obj,'trial_count') < getattr(orthosis_obj,'n_trials'):# and move_to_start_pos: # added start pos here 

        start_time = time.time()  # Record the start time

        orthosis_obj.readValues()
        orthosis_obj.runExperimentRandomError(flag_flexion_done, disturbing, flag_flexion_started, flag_normal_trigger)
        # setattr(orthosis_obj,'is_verbose', True)
        if getattr(orthosis_obj,'is_verbose'):
            print(f"Trial Count     : {getattr(orthosis_obj,'trial_count')}")
            print(f"Error Count     : {getattr(orthosis_obj,'err_count')}")
            print(f"Error Seq       : {getattr(orthosis_obj,'err_sequence')}")
            print(f"orthosis pos    : {getattr(orthosis_obj,'orthosis_position')}")
            print(f"orthosis pos des: {getattr(orthosis_obj,'orthosis_pose_desired')}")
            print(f"orthosis force  : {getattr(orthosis_obj,'orthosis_force')}")
            print(f"is error        : {orthosis_obj.is_disturbing} {disturb}")
        # Safe KeyboardInterrupt
        if getattr(orthosis_obj,'safe_interrupt'):
            print("Exiting the orthosis process safely!!")
            orthosis_obj.orthosis_handle.disable_motor()
            break

        if orthosis_obj.is_disturbing == True:
            disturb = 100.0
            prev_trial = orthosis_obj.trial_count

        elif prev_trial == orthosis_obj.trial_count :
            disturb = 100.0

        else :
            prev_trial = -1
            disturb = 0.0

        myDatas = [orthosis_obj.orthosis_position, orthosis_obj.orthosis_pose_desired, orthosis_obj.orthosis_force,disturb]
        zmqPub.zmq_publish(myDatas,myLabel,stop_flag)


        end_time = time.time()  # Record the end time
        execution_time = end_time - start_time  # Calculate the execution time for this iteration
        execution_times.append(execution_time)  # Store the execution time


    # Stopping the experiment
    orthosis_obj.orthosis_handle.disable_motor()
    stop_flag = True
    zmqPub.zmq_publish(myDatas,myLabel,stop_flag)

    if execution_times:
        average_execution_time = sum(execution_times) / len(execution_times)
    else:
        average_execution_time = 0
    
    print(f"Average Execution Time: {average_execution_time} seconds")
    time.sleep(3.0)
    sa.delete("shm://button")
    sa.delete("shm://flex")
    sa.delete("shm://dist")
    sa.delete("shm://flst")
    sa.delete("shm://notr")


def runButton():
    button_obj = ButtonLib('/dev/ttyUSB0',9600)
    setattr(button_obj,'is_listener_running', True)
    is_pressed[0] = 0.0
    signal.signal(signal.SIGINT, button_obj.signalHandler)
    signal.signal(signal.SIGQUIT, button_obj.signalHandler)
    signal.signal(signal.SIGTSTP, button_obj.signalHandler)
    print("Button Listener Ready!!")
    while getattr(button_obj,'is_listener_running'):
        if button_obj.button_handle.in_waiting > 0:
            button_val = button_obj.button_handle.read().decode("utf-8")
            setattr(button_obj,'button_val',button_val)
            if getattr(button_obj,'button_val') == '-':
                is_pressed[0] = True
                print("Button Pressed!!")
            elif getattr(button_obj,'button_val') == ',':
                is_pressed[0] = False
        # Safe Keyboard Interrupt
        if getattr(button_obj,'safe_interrupt'):
            print("Exiting Button process safely!")
            break

# def runButton():
#     def on_release(key):
#         if key == Key.esc:
#             print("exit run Button")
#             m_listener.stop()
#             return False   

#     def on_click(x, y, button, pressed):
#         if pressed:
#             is_pressed[0] = True
#             print("Button Pressed!!")
#         else:
#             is_pressed[0] = False
#             print("Button Released")

#     with KeyboardListener(on_release=on_release) as k_listener, \
#         MouseListener(on_click=on_click) as m_listener:
#             k_listener.join()
#             m_listener.join()

def runTrigger():
    trig_obj = TrigLib('/dev/ttyUSB1', 9600)
    setattr(trig_obj,'is_trigger_running', True)
    loop_idx = 0
    dt = 0.002
    print("Trigger Process Ready!!")
    prev_flag_flexion_started   = 0.0
    prev_flag_disturbing        = 0.0
    prev_button_state           = 0.0
    prev_normal_trigger         = 0.0
    loop_start_time = time.perf_counter()
    signal.signal(signal.SIGINT, trig_obj.signalHandler)
    signal.signal(signal.SIGQUIT, trig_obj.signalHandler)
    signal.signal(signal.SIGTSTP, trig_obj.signalHandler)
    while getattr(trig_obj, 'is_trigger_running'):
        loop_idx += 1
        # Flexion or Extension
        if flag_flexion_done[0] == 0.0 and flag_flexion_started[0] == 1.0:
            if prev_flag_flexion_started == 0.0: # If flexion started
                # ard_start_time = time.perf_counter()
                trig_obj.arduino_handle.write(b'F') # flexion trigger
                # print(f"Sending time :{time.perf_counter() - ard_start_time}" )
                print("F trigger is sent")
        elif flag_flexion_done[0] == 1.0 and flag_flexion_started[0] == 0.0:
            if prev_flag_flexion_started == 1.0: # If extension started
                trig_obj.arduino_handle.write(b'E') # extension trigger
                print("E trigger is sent")
        
        # Error Introduced or not
        if disturbing[0] == 1.0 and prev_flag_disturbing == 0.0:
            trig_obj.arduino_handle.write(b'Y') # error command "Y" is send
            print("Error trigger sent")
        elif disturbing[0] == 0.0 and flag_normal_trigger[0] == 1.0 and prev_normal_trigger == 0.0:
            trig_obj.arduino_handle.write(b'N')
            print("Nominal trigger sent")
        
        # Button Press Status
        if is_pressed[0] == 1.0 and prev_button_state == 0.0:
            trig_obj.arduino_handle.write(b'P') # pressed command "P" is send
            print("Button trigger sent")

        prev_flag_flexion_started   = flag_flexion_started[0]
        prev_normal_trigger         = flag_normal_trigger[0]
        prev_flag_disturbing        = disturbing[0]
        prev_button_state           = is_pressed[0]
        
        # Ensuring const. desired loop freq
        while time.perf_counter() - loop_start_time < dt * loop_idx: # This process does not work as intended for freq higher than 500 Hz (some triggers are not sent)
            pass
        # Safe KeyboardInterrupt
        if getattr(trig_obj, 'safe_interrupt'):
            print("Exiting Trigger process safely!")
            break
        


if __name__ == "__main__":

    orthosis_obj = OrthosisLib("can0", 0x01, "AK80_6_V1p1", 0.5)
    
    parser = argparse.ArgumentParser("Custom Error: ")
    parser.add_argument('-n','--n_errors', help='No of errors to introduce')
    parser.add_argument('-d','--duration', help='Duration of error in microseconds')
    parser.add_argument('-v','--verbose', help='Bool to decide if you want to print on console')
    parser.add_argument('-tf','--thr_flex', help='Force threshold for flexion')
    parser.add_argument('-te','--thr_ext', help='Force threshold for extension')
    parser.add_argument('-nt','--num_trial',help='Number of trial')


    args = vars(parser.parse_args())
    if args['n_errors'] is not None:
        setattr(orthosis_obj, 'n_err', int(args['n_errors']))
    if args['duration'] is not None:
        setattr(orthosis_obj, 'duration', float(args['duration']))
    if args['verbose'] is not None:
        setattr(orthosis_obj, 'is_verbose', bool(args['verbose']))
    if args['thr_flex'] is not None:
        setattr(orthosis_obj, 'eff_thresh_flex', float(args['thr_flex']))
    if args['thr_ext'] is not None:
        setattr(orthosis_obj, 'eff_thresh_ext', float(args['thr_ext']))
    if args['num_trial'] is not None:
        setattr(orthosis_obj, 'n_trials', int(args['num_trial']))
    

    #Deleting old SharedArrays
    # if len(sa.list()) != 0:
    #     sa.delete("shm://button")
    #     sa.delete("shm://flex")
    #     sa.delete("shm://dist")
    #     sa.delete("shm://flst")
    #     sa.delete("shm://notr")

        

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
    # pr_button.start()
    # pr_trigger.start()

