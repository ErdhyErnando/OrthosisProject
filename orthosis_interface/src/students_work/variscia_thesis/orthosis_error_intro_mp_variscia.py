#!/usr/bin/env python3

############# NOTE #############
# This script is the multiprocessing script which appends all the values to the queue 
# and uses SharedArrays to share memory across processes.
################################
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
import lib.orthosis_lib.orthosis_v1_lib as orthosis_lib

def runOrthosis():
    orthosis_handle = serial.Serial(port=param.orthosis_port_name, baudrate=param.orthosis_baud_rate)
    param.is_orthosis_running=True
    orthosis_lib.calibrate(orthosis_handle)
    orthosis_lib.generateErrorSequence()
    disturbing[0] = False
    flag_flexion_done[0] = False
    print("Orthosis Process Ready!!")
    while param.is_orthosis_running:
        orthosis_lib.readValues(orthosis_handle)
        orthosis_lib.runExperimentRandomError(orthosis_handle, flag_flexion_done, disturbing)
        if param.is_verbose and not is_write[0]:
            print(f"Trial Count: {param.trial_count}")
            print(f"Error Count: {param_err.err_count}")
            print(f"Error Seq  : {param_err.err_sequence}")


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


def runLogger():
    param.is_logger_running = True
    orthosis_lib.headerFile()
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
            inp_msg[0]= 3
        elif inp_msg[0] == 2: 
            data_list_q.put("Measurement End!!" + '\n')
            inp_msg[0] = 4
            is_write[0] = True
            print(f"is_write {is_write[0]}")
        if inp_msg[0] == 3:
            data_list_q.put(time.perf_counter() - start_time[0])
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
            f = open("%s.txt" %param.filename, "a+")
            f.write(f"Measurement Duration : {end_time[0] - start_time[0]}")
            f.write('\n\n')
            for i in range(data_list_q.qsize()):
               f.write(str(data_list_q.get()))
            f.close()
            print("All data written to file")
            is_write[0] = False

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
    param.filename  =   '../test_proj/' + str(today.strftime("%d%m%Y")) + '_' + param.sub_name + '_' + param.expt_scenario + '_' + param.expt_seq + '_' + param.expt_suffix + '_' + param.set_num + '_orthosis'
    
    # Queue object to append all values to log 
    data_list_q     = mp.Queue()

    # Deleting old SharedArrays
    if len(sa.list()) != 0:
        sa.delete("shm://test")
        sa.delete("shm://wr")
        sa.delete("shm://button")
        sa.delete("shm://flex")
        sa.delete("shm://dist")
        sa.delete("shm://start")
        sa.delete("shm://end")

    # Creating SharedArrays
    inp_msg             = sa.create("shm://test",1)
    is_write            = sa.create("shm://wr",1)

    start_time          = sa.create("shm://start",1)
    end_time            = sa.create("shm://end",1)

    is_pressed          = sa.create("shm://button",1)
    flag_flexion_done   = sa.create("shm://flex",1)
    disturbing          = sa.create("shm://dist",1)

    # Process 1 - Orthosis process
    pr_orthosis    = mp.Process(target=runOrthosis)

    # Process 2 - Button press process
    pr_button      = mp.Process(target=runButton)

    # Process 3 - ZMQ-Socket connection process
    pr_zmq_client  = mp.Process(target=runZmqClient)
    
    # Process 4 - Data logging process
    pr_logger      = mp.Process(target=runLogger)

    # Starting the processes
    pr_orthosis.start()
    # pr_button.start()
    # pr_zmq_client.start()
    # pr_logger.start()
