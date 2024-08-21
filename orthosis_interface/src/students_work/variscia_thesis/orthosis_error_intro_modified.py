#!/usr/bin/env python3

############# NOTE #############
#This script is modification of orthosis_error_intro_mp_variscia.py
#Several additional lines are added to communicate and send data from
#Orthosis device to the JS WebApp.
###############################


import argparse
import serial
import multiprocessing as mp
import time
import datetime
import SharedArray as sa
# Appending the relative path of the root folder
import sys, os
# sys.path.append('../../')
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '../../../')))
print(sys.path)
import param.orthosis_param as param
import param.error_param as param_err

# Uncomment the following if you have pip installed the orthosis_lib
# import orthosis_lib.orthosis_v1_lib as orthosis_lib
# Uncomment the following otherwise
import lib.orthosis_v1_lib_modified as orthosis_lib


#Function to run the orthosis
def runOrthosis():
    orthosis_handle = serial.Serial(port=param.orthosis_port_name, baudrate=param.orthosis_baud_rate)
    param.is_orthosis_running=True
    orthosis_lib.calibrate(orthosis_handle)
    orthosis_lib.generateErrorSequence()
    disturbing[0] = False
    flag_flexion_done[0] = False
    inp_msg[0] = 1
    myStop_flag = False
    i = 0
    for i in range(len(param_err.err_sequence)):
        error_seq[i] = param_err.err_sequence[i]
    
    #establishing ZMQ Publisher to publish data to the JS WebAPP
    pubSocket = orthosis_lib.EstablishZMQPub()
    myLabels = ["orth_pos","err_pos","orth_force","orth_def","orth_f_offset","orth_status","orth_voltage","is_error_introduced"]
    print("Orthosis Process Ready!!")
    trial_counter[0] = 0

    # Initialize a list to store execution times
    execution_times = []

    while param.trial_count < param.n_trials:
        start_time = time.time()  # Record the start time

        orthosis_lib.readValues(orthosis_handle)
        orthosis_lib.runExperimentRandomError(orthosis_handle, flag_flexion_done, disturbing)
        current_pos[0] = param.orthosis_position
        error_pos[0] = param_err.err_position
        trial_counter[0] = param.trial_count
        intro_error = 0.0
        if param_err.is_err_introduced == True:
            intro_error = 100.0
        myData = [param.orthosis_position,param_err.err_position,param.orthosis_force,
                  param.orthosis_deflection,param.orthosis_f_offset,param.orthosis_status,param.orthosis_voltage,intro_error]
        
        #Publish data to JS WebAPP
        orthosis_lib.ZMQPublish(myData,myLabels,myStop_flag,pubSocket)
        if param.is_verbose and not is_write[0]:
            print(f"Trial Count: {param.trial_count}")
            print(f"Error Count: {param_err.err_count}")
            print(f"Error Seq  : {param_err.err_sequence}")
        
        end_time = time.time()  # Record the end time
        execution_time = end_time - start_time  # Calculate the execution time for this iteration
        execution_times.append(execution_time)  # Store the execution time


    myStop_flag = True
    orthosis_lib.ZMQPublish(myData,myLabels,myStop_flag,pubSocket)

    # Calculate the average execution time
    average_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
    print("done!!!")
    print(f"Average Execution Time: {average_execution_time} seconds")

    inp_msg[0] = 2

    time.sleep(4.0)
    #Delete the old shared array
    sa.delete("shm://test")
    sa.delete("shm://wr")
    sa.delete("shm://button")
    sa.delete("shm://flex")
    sa.delete("shm://dist")
    sa.delete("shm://start")
    sa.delete("shm://end")
    sa.delete("shm://trialCount")
    sa.delete("shm://position")
    sa.delete("shm://err_pos")
    sa.delete("shm://err_seq")
 


#Function to read button value
def runButton():
    button_handle   = serial.Serial(port=param.button_port_name, baudrate=param.button_baud_rate)
    param.is_listener_running= True
    print("Button Listener Ready!!")
    while param.is_listener_running:
        if button_handle.in_waiting > 0:
            param.button_val = button_handle.read()
            if param.button_val == b'\x01':
                is_pressed[0] = True
                print("Button Pressed!!")
            elif param.button_val == b'\x00':
                is_pressed[0] = False


#Function to replace the button with keyboard and mouse
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


#Function to run ZMQ Cleint to communicate with second device
def runZmqClient():
    param.is_client_running = True
    my_socket = orthosis_lib.establishZMQ()
    print("Waiting for Start Trigger!")
    while param.is_client_running:
        undecoded_msg = my_socket.recv()
        inp_msg[0] = int(undecoded_msg[2:])
        if inp_msg[0] == 1:
            start_time[0] = time.perf_counter()
        elif inp_msg[0] == 2:
            end_time[0] = time.perf_counter()
        print(f"Server msg received: {inp_msg[0]}")

#Function to map the angle from the sensor reading data into degree
def mapAngle(angle):
    real_angle = 0.1*angle-90
    return real_angle


#Function to run Logger
def runLogger():
    param.is_logger_running = True
    # orthosis_lib.headerFile(error_seq)
    is_write[0] = False
    loop_idx    = 0
    loop_freq   = 1000
    dt          = 1/loop_freq
    print("Logger Process Ready!!")
    loop_start_time = time.perf_counter()
    while param.is_logger_running:
        # Increment loop index
        loop_idx += 1
        if inp_msg[0] == 1: 
            data_list_q.put("Measurement Start!!" + '\n') 
            start_time[0] = time.perf_counter()
            inp_msg[0]= 3
        elif inp_msg[0] == 2: 
            data_list_q.put("Measurement End!!" + '\n')
            end_time[0] = time.perf_counter()
            inp_msg[0] = 4
            is_write[0] = True
            print(f"is_write {is_write[0]}")
        if inp_msg[0] == 3:
            data_list_q.put(f" ,{trial_counter[0]}")
            data_list_q.put(f" ,{mapAngle(current_pos[0])}")
            data_list_q.put(f" ,{mapAngle(error_pos[0])}")
            #data_list_q.put(time.perf_counter() - start_time[0])
            # Flexion or Extension
            if not flag_flexion_done[0]:
                data_list_q.put(' ,F')
            else:
                data_list_q.put(' ,E')
            # Error Introduced or not
            if disturbing[0]:
                data_list_q.put(' ,Y')
            else:
                data_list_q.put(' ,N')
            # Button Press Status
            if is_pressed[0]:
                data_list_q.put(' ,P\n')
            else:
                data_list_q.put(' ,NP\n')
        
        # Writing to the file
        if is_write[0]:
            print("Exiting Logger Loop!")
            print("Entered file condition")
            orthosis_lib.headerFile(error_seq)
            f = open("%s.txt" %param.filename, "a+")
            f.write(f"Measurement Duration : {end_time[0] - start_time[0]}")
            f.write('\n\n')
            for i in range(data_list_q.qsize()):
               f.write(str(data_list_q.get()))
            f.close()
            print("All data written to file")
            is_write[0] = False
            param.is_logger_running = False

        # Ensuring const. desired loop freq
        while time.perf_counter() - loop_start_time < dt * loop_idx:
            pass


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser("Custom Error: ")
    parser.add_argument('-n','--n_errors', help='No of errors to introduce')
    parser.add_argument('-d','--duration', help='Duration of error in microseconds')
    parser.add_argument('-f','--file_name', help='Name of saved Text File')
    parser.add_argument('-v','--verbose', help='Bool to decide if you want to print on console')
    parser.add_argument('-s','--sensitivity', help='Force Sensitivity')
    parser.add_argument('-nt','--n_trial', help='Number of Trials')
   

    parser.add_argument('-sn','--sub_name', help='Subject Pseudo name')
    parser.add_argument('-es','--expt_scenario', help='Experiment Scenario')
    parser.add_argument('-eseq','--expt_seq', help='Experiment Sequence')
    parser.add_argument('-esuf','--expt_suffix', help='Experiment Suffix')
    parser.add_argument('-set','--set_num', help='Set number')


    args = vars(parser.parse_args())
    if args['n_errors'] is not None:
        param_err.num = int(args['n_errors'])
    if args['duration'] is not None:
        param_err.duration = float(args['duration'])
    if args['file_name'] is not None:
        param.filename = args['file_name']
    if args['verbose'] is not None:
        param.is_verbose = bool(args['verbose'])
    if args['sensitivity'] is not None:
        param.f_sensitivity = float(args['sensitivity'])
    if args['n_trial'] is not None:
        param.n_trials = int(args['n_trial'])

    if args['sub_name'] is not None:
        param.sub_name = args['sub_name']
    if args['expt_scenario'] is not None:
        param.expt_scenario = args['expt_scenario']
    if args['expt_seq'] is not None:
        param.expt_seq = args['expt_seq']
    if args['expt_suffix'] is not None:
        param.expt_suffix = args['expt_suffix']
    if args['set_num'] is not None:
        param.set_num = args['set_num']

    
    today     =   datetime.date.today() 
    # param.filename  =   '../data/' + str(today.strftime("%d%m%Y")) + '_' + param.sub_name + '_' + param.expt_scenario + '_' + param.expt_seq + '_' + param.expt_suffix + '_' + param.set_num + '_orthosis'
    # param.filename  =   str(today.strftime("%d%m%Y")) + '_' + param.sub_name + '_' + param.expt_scenario + '_' + param.expt_seq + '_' + param.expt_suffix + '_' + param.set_num
    param.filename  =   '../../../data/' + str(today.strftime("%d%m%Y")) + '_' + param.sub_name + '_' + param.expt_scenario + '_' + param.expt_seq + '_' + param.expt_suffix + '_' + param.set_num + '_orthosis'
    
    # Queue object to append all values to log 
    data_list_q     = mp.Queue()

    # # Deleting old SharedArrays
    # if len(sa.list()) != 0:
    #     sa.delete("shm://test")
    #     sa.delete("shm://wr")
    #     sa.delete("shm://button")
    #     sa.delete("shm://flex")
    #     sa.delete("shm://dist")
    #     sa.delete("shm://start")
    #     sa.delete("shm://end")
    #     sa.delete("shm://trialCount")
    #     sa.delete("shm://position")
    #     sa.delete("shm://err_pos")
    #     sa.delete("shm://err_seq")


    # Creating SharedArrays
    inp_msg             = sa.create("shm://test",1)
    is_write            = sa.create("shm://wr",1)

    start_time          = sa.create("shm://start",1)
    end_time            = sa.create("shm://end",1)

    is_pressed          = sa.create("shm://button",1)
    flag_flexion_done   = sa.create("shm://flex",1)
    disturbing          = sa.create("shm://dist",1)
    trial_counter       = sa.create("shm://trialCount",1)
    error_seq           = sa.create("shm://err_seq",param_err.num)
    current_pos         = sa.create("shm://position",1)
    error_pos           = sa.create("shm://err_pos",1)
    

    # Process 1 - Orthosis process
    pr_orthosis    = mp.Process(target=runOrthosis)

    # Process 2 - Button press process
    pr_button      = mp.Process(target=runButton)

    # Process 3 - ZMQ-Socket connection process (not needed for now)
    #pr_zmq_client  = mp.Process(target=runZmqClient)
    
    # Process 4 - Data logging process
    pr_logger      = mp.Process(target=runLogger)

    # Starting the processes
    pr_orthosis.start()
    pr_button.start()
    # pr_zmq_client.start()
    pr_logger.start()