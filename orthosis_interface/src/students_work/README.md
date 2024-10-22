# students_work Folder
This folder contain all of the src file that was built for student project or thesis purpose. Inside this folder are mostly the program to run the orthosis v1. In this documentation, the Author will only discuss about the program **orthosis_error_intro_modified.py** inside variscia_thesis folder since this was the file where the Author and the team was working on. This program is a modification of orthosis_error_intro.py that enable the program to communicate with the WebApp. 

## orthosis_error_intro.py
This file has runtime arguments :
- *--n_errors*
pass number of errors to be introduced. can be called using *-n*.
- *--duration*
pass the duration of error in microseconds. Can be called using *-d*.
- *--file_name*
pass the name of the saved text file log (not from the app). Can be called using *-f*.
- *--verbose*
pass the boolean value to decide whether there will be console print or not. Can be called using *-v*.
- *--sensitivity*
pass the value of the sensitivity of the force. Can be called using *-s*.
- *--n_trial*
pass the number of trial. Can be called using *-nt*.
- *--sub_name*
pass the name of the subject pseudo name *-sn*.
- *--expt_scenario*
pss the experiment scenarion. Can be called using *-es*.
- *--expt_seq*
pass the experiment sequence. Can be called using *-eseq*.
- *--expt_suffix*
pass the experiment suffix. Can be called using *-esuf*.
- *--set_num*
pass the set number. Can be called using *-set*.
- *--name*
pass the name of the subject. **Name can not contain space (use "_" instead).** Can be called using *-nm*.

This run time argument can be called before running the program inside CLI or inside the WebApp but not necessary. This program has four functions and main to run those function using multithreading library.
```python
#!/usr/bin/env python3

############# NOTE #############
#This script is modification of orthosis_error_intro_mp_variscia.py
#Several additional lines are added to communicate and send data from
#Orthosis device to the JS WebApp. HAS NOT BEEN TESTED since the Orthosis v1
#was broken during the development of this program.
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
import lib.orthosis_lib.orthosis_v1_lib as orthosis_lib

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
    trial_prev = param.trial_count
    i = 0
    for i in range(len(param_err.err_sequence)):
        error_seq[i] = param_err.err_sequence[i]
    
    #establishing ZMQ Publisher to publish data to the JS WebAPP
    pubSocket = orthosis_lib.EstablishZMQPub()
    myLabels = ["orth_pos","err_pos","flex_ext","distrub_intro","new_trial","is_pressed","err_count"]
    print("Orthosis Process Ready!!")
    trial_counter[0] = 0

    # Initialize a list to store execution times
    execution_times = []
    num_ittr = 0

    while param.trial_count < param.n_trials:
        start_time = time.time()  # Record the start time

        orthosis_lib.readValues(orthosis_handle)
        orthosis_lib.runExperimentRandomError(orthosis_handle, flag_flexion_done, disturbing)
        current_pos[0] = param.orthosis_position
        error_pos[0] = param_err.err_position
        trial_counter[0] = param.trial_count
        intro_error = None
        err_pos = None
        new_trial = None
        pressed = None

        #generate spike on graph everytime it enter new trial
        if param.trial_count != trial_prev:
            new_trial = 100.0

        #generate spike on graph everytime error is introduced (and show error position)
        if param_err.is_err_introduced == True:
            intro_error = 100.0
            err_pos = param_err.err_position

        #generate spike on graph everytime the button is pressed
        if is_pressed[0] == True:
            pressed = 100.0

        #flexion or extention
        flex_ext = None
        if not flag_flexion_done[0]:
            flex_ext = "F"
        else:
            flex_ext = "E"
            
        #sending data only after 150 itteration
        if num_ittr == 150 or pressed != None or intro_error != None or new_trial != None:
        
            myData = [round(param.orthosis_position,2),round(err_pos,2),flex_ext,round(intro_error,2),new_trial,pressed,param_err.err_count]
            #Publish data to JS WebAPP
            orthosis_lib.ZMQPublish(myData,myLabels,myStop_flag,pubSocket)
            num_ittr = 0

        else:
            num_ittr += 1

        if param.is_verbose and not is_write[0]:
            print(f"Trial Count: {param.trial_count}")
            print(f"Error Count: {param_err.err_count}")
            print(f"Error Seq  : {param_err.err_sequence}")
        
        trial_prev = param.n_trials
        
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
        time.sleep(0.06)

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
    parser.add_argument('-nm','--name',help='Subject Name')


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
 ```
This program utlizes multithreading to run each of the function simultinously in different core. To make those functions able to send data to each other, sharedArrays are used. The detail of each function and the main will be explained below.

### runOrthosis()
this function is the one that responsible for moving the orthosis and sending the data of the orthosis to the webApp. At the first part, all the variables and object are intialized.
```python
def runOrthosis():
    orthosis_handle = serial.Serial(port=param.orthosis_port_name, baudrate=param.orthosis_baud_rate)
    param.is_orthosis_running=True
    orthosis_lib.calibrate(orthosis_handle)
    orthosis_lib.generateErrorSequence()
    disturbing[0] = False
    flag_flexion_done[0] = False
    inp_msg[0] = 1
    myStop_flag = False
    trial_prev = param.trial_count
    i = 0
    for i in range(len(param_err.err_sequence)):
        error_seq[i] = param_err.err_sequence[i]
    #other intialization, see the full code
```
The label and the ZMQ Publisher are also intialized  to establish communication with the WebApp.
```python
#establishing ZMQ Publisher to publish data to the JS WebAPP
    pubSocket = orthosis_lib.EstablishZMQPub()
    myLabels = ["orth_pos","err_pos","flex_ext","distrub_intro","new_trial","is_pressed","err_count"]
    print("Orthosis Process Ready!!")
    trial_counter[0] = 0
```
After that a while loop will be executed. This while looop responsible to run the process of the orthosis as long as the number of trial is not exceed the desired number of trial.
```python
 while param.trial_count < param.n_trials:
        start_time = time.time()  # Record the start time

        orthosis_lib.readValues(orthosis_handle)
        orthosis_lib.runExperimentRandomError(orthosis_handle, flag_flexion_done, disturbing)
        current_pos[0] = param.orthosis_position
        error_pos[0] = param_err.err_position
        trial_counter[0] = param.trial_count
        intro_error = None
        err_pos = None
        new_trial = None
        pressed = None
```
The data that are taken will then be processed. As has been explained on the documentation of the library (orthosis_v1_lib.py). There are certain data that need to be sent to the orthosis such as *flex_ext*,*disturb_intro*,*new_trial*,*is_pressed* and *err_count*. For those first four datas, there is an exact value that to be sent, for example *flex_ext* should send a string whether F or E and *is_pressed* should whether 0 (when it is pressed) or 100 (when pressed). Hence there are lines that process this data to get the desired value :
```python
        #generate spike on graph everytime it enter new trial
        if param.trial_count != trial_prev:
            new_trial = 100.0

        #generate spike on graph everytime error is introduced (and show error position)
        if param_err.is_err_introduced == True:
            intro_error = 100.0
            err_pos = param_err.err_position

        #generate spike on graph everytime the button is pressed
        if is_pressed[0] == True:
            pressed = 100.0

        #flexion or extention
        flex_ext = None
        if not flag_flexion_done[0]:
            flex_ext = "F"
        else:
            flex_ext = "E"
```
To prevent a bottle neck during publishing the data which can cause delay inside the webApp, the data will only be sent every 150 itteration of the while loop or if the value  of the pressed, disturb, and new_trial is 100. 
```python
        #sending data only after 150 itteration
        if num_ittr == 150 or pressed != None or intro_error != None or new_trial != None:
        
            myData = [round(param.orthosis_position,2),round(err_pos,2),flex_ext,round(intro_error,2),new_trial,pressed,param_err.err_count]
            #Publish data to JS WebAPP
            orthosis_lib.ZMQPublish(myData,myLabels,myStop_flag,pubSocket)
            num_ittr = 0

        else:
            num_ittr += 1
```
After the loop is done, the orthosis will publish stop_flag to tell the WebApp that the process already finish.
```python
    myStop_flag = True
    orthosis_lib.ZMQPublish(myData,myLabels,myStop_flag,pubSocket)
```
All sharedArray will be deleted.
```python
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
```

### runButton()
This function is used to listen to the button and read the value of the button whether the button is pressed or not. First it initilized all of the object and variable.
```python
def runButton():
    button_handle   = serial.Serial(port=param.button_port_name, baudrate=param.button_baud_rate)
    param.is_listener_running= True
    print("Button Listener Ready!!")
```
Then there is a while loop which will always run as long as  the orthosis is running and no keyboard interrupt. Inside this loop, there will be listener that listen to the button state and update the is_pressed[0] variable accordingly.
```python
    while param.is_listener_running:
        if button_handle.in_waiting > 0:
            param.button_val = button_handle.read()
            if param.button_val == b'\x01':
                is_pressed[0] = True
                print("Button Pressed!!")
            elif param.button_val == b'\x00':
                is_pressed[0] = False
        time.sleep(0.06)
```
### runZmqClient()
This function is used to connect the Orthosis device to another device. It use ZMQ to establish communication. This function will wait for the message from the client and use that as indication whether the measurement is started or ended.
```python
 while param.is_client_running:
        undecoded_msg = my_socket.recv()
        inp_msg[0] = int(undecoded_msg[2:])
        if inp_msg[0] == 1:
            start_time[0] = time.perf_counter()
        elif inp_msg[0] == 2:
            end_time[0] = time.perf_counter()
        print(f"Server msg received: {inp_msg[0]}")
```

### runLogger()
This function is used to create a logger locally. It will run inside the loop while the paramater is_logger_running is True.
```python
    while param.is_logger_running:
```
This program will then read value from sharedArray that has been passed from other program and write the data to the txt document according to the value inside this SharedArray. The Program however will only start to log the value if there is an indication that the measurment is started which come from the runZmqClient() function. The start of the logging is indicated by inp_msg[0]=3.
```python
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
```
Then the program will write the logged value to txt file if the SharedArray is_write[0] is True.
```python
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
```
this is_write[0] value is updated to True when inp_msg[0] = 2 which means measurment is ended (passed from the runZmqClient()).
```python
        elif inp_msg[0] == 2: 
            data_list_q.put("Measurement End!!" + '\n')
            end_time[0] = time.perf_counter()
            inp_msg[0] = 4
            is_write[0] = True
            print(f"is_write {is_write[0]}")
```
### Main
in the main program, the run time argument will be intialized.
```python
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
    parser.add_argument('-nm','--name',help='Subject Name')


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
```
it also intialized all of necessary sharedArray for communication between function.
```python
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
```
Then at the last part, all of the functions will be assigned to dedicated multithreading process and then run those thread in parallel.
```python
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
```