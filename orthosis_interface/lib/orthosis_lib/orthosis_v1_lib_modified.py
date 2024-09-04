#!/usr/bin/env python3

## This library is the modification of orthosis_v1_lib.py with additional function
## to communicate with JS WebAPP via ZMQ.

import random
import time
import zmq
import SharedArray as sa
# Appending the relative path of the root folder
import sys, os
# sys.path.append('../')
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
import param.orthosis_param as param
import param.pseudo_viz_param as param_viz
import param.error_param as param_err
# Importing multipledispatch for function overloading
from multipledispatch import dispatch


def calibrate(orthosis_handle):
    """
    This function calibrates the force offset for the user

    Returns(pseudo):
        param.f_offset : average offset in force
        param.is_calibrated   : flag to indicate that the hand is calibrated
    """
    n=10
    m=0
    for i in range(n):
        if readValues(orthosis_handle):
            m+=1
            param.orthosis_f_offset += param.orthosis_force
    param.orthosis_f_offset /= float(m)
    param.is_calibrated = True


def forceControl(orthosis_handle):
    """
    This function performs the main functions of the experiment
            - detect the sensitivity of the force to start the motion
            - introduce errors
            - provide direciton commands for motion
    """
    if param.intro_errors:
        introduceRandomErrors()
        print("Oops! This experiment will have random errors")
    else:
        print("Enjoy error-free operation")

    # Check if the hand is moving up
    if param.orthosis_force < -param.f_sensitivity:
        if not param.is_disturbing:
            executeFlexion(orthosis_handle)
        else:
            executeExtension(orthosis_handle)
            print ("Error Introduced")
    # Check if the hand is moving down 
    elif param.orthosis_force > param.f_sensitivity:
        if not param.is_disturbing:
            executeExtension(orthosis_handle)
        else:
            executeFlexion(orthosis_handle)
            print ("Error Introduced")
    # Default condition
    else:
        stopMotion(orthosis_handle)

    # If the hard limit is reached
    if param.orthosis_position >= param.max_pos or param.orthosis_position <= param.min_pos:
        stopMotion(orthosis_handle)


def runExperiment(orthosis_handle):
    """
    This function is the main function for the basic orthosis experiment.
    Conditions:
        - The force values will only be checked at the beginning of each trial
        - Once, the force feedback > f_sensitivity, the flexion or extension motions will be executed effortlessly

    Args:
        param.is_flexion_done (bool)                : bool to check if flexion has been fully executed
        param.is_flexion_started (bool)             : bool to check if flexion has started. If False - means that extension has started
        param.is_enough_force_for_flexion (bool)    : bool to check the force condition. If False - means that there is enough force for extension

    Returns:
        param.trial_count (int)                     : total number of trials executed

    """
    if param.intro_errors:
        introduceRandomErrors()
        print("Oops! This experiment will have random errors")
    else:
        print("Enjoy error-free operation")

    # Check if enough force is applied for starting flexion
    if not param.is_flexion_done and not param.is_flexion_started:
        if param.orthosis_force < -param.f_sensitivity and param.orthosis_position > param.min_pos - param.buffer_pos:
            param.is_enough_force_for_motion = True
    # Check if enough force is applied for starting extension
    elif param.is_flexion_done and param.is_flexion_started:
        if param.orthosis_force > param.f_sensitivity and param.orthosis_position < param.max_pos:
            param.is_enough_force_for_motion = False

    # Check if flexion is supposed to be executed
    if param.is_enough_force_for_motion and not param.is_flexion_done:
        param.is_flexion_started = True
        if not param.is_disturbing:
            executeFlexion(orthosis_handle)
        elif param.is_disturbing:
            executeExtension(orthosis_handle)
            print("OOPS! Error Introduced!")
        # Check if arm is fully flexed
        if param.orthosis_position >= param.max_pos:
            param.is_flexion_done = True
            param.trial_count += 1
    
    # Check if extension is supposed to be executed
    elif not param.is_enough_force_for_motion and param.is_flexion_done:
        param.is_flexion_started = False
        if not param.is_disturbing:
            executeExtension(orthosis_handle)
        elif param.is_disturbing:
            executeFlexion(orthosis_handle)
            print("OOPS! Error Introduced!")
        # Check if arm is fully extended
        if param.orthosis_position <= param.min_pos + param.buffer_pos:
            param.is_flexion_done = False
            param.trial_count += 1

    # Default Condition
    else:
        stopMotion(orthosis_handle)

    # Hard limit check
    if param.orthosis_position >= param.max_pos or param.orthosis_position <= param.min_pos:
        stopMotion(orthosis_handle)

@dispatch(object, object, object)
def runExperimentRandomError(orthosis_handle, flag_flexion_done, disturbing):
    """
    This function is the main function for the random error introduction with orthosis experiment.
    This was developed during Variscia Putri's Bachelor Thesis (Aug 2022 - Oct 2022) for studying the error potential.

    Conditions:
        - The force values will only be checked at the beginning of each trial
        - Once, the force feedback > f_sensitivity, the flexion or extension motions will be executed effortlessly
        - Depending upon the experiment conditions, param_err.num will be randomly introduced with the following conditions - 
            -> In each trial (flexion or extension), error will be introduced only once for param_err.duration ms
            -> Error will be introduced only in the centre part of the movement range
            -> No error will be introduced in consecutive trials

    Args:
        flag_flexion_done[0] (sa float)     : bool to check if flexion has been fully executed
        disturbing[0] (sa float)            : bool to check if the trial is an error trial
    """  
    if not param_err.num == 0:      
        if not disturbing[0] and not param_err.is_err_introduced:
            for i in param_err.err_sequence:
                if i == param.trial_count:
                    chooseErrorPosition()
                    setErrorFlags(disturbing)
                        
        if disturbing[0] and not param_err.is_err_introduced:
            checkErrorDuration(disturbing)

    # Check if enough force is applied for starting flexion
    if not flag_flexion_done[0] and not param.is_flexion_started:
        checkFlexionStart()
    # Check if enough force is applied for starting extension
    elif flag_flexion_done[0] and param.is_flexion_started:        
        checkExtensionStart()

    # Check if flexion is supposed to be executed
    if param.is_enough_force_for_motion and not flag_flexion_done[0]:
        param.is_flexion_started = True
        if not disturbing[0]:
            executeFlexion(orthosis_handle)
        elif disturbing[0]: 
            print(f"Error intro at {param_err.err_position} angle")
            executeExtension(orthosis_handle)
        # Check if arm is fully flexed
        checkFlexionEnd(flag_flexion_done)

    # Check if extension is supposed to be executed
    elif not param.is_enough_force_for_motion and flag_flexion_done[0]:
        param.is_flexion_started = False
        if not disturbing[0]:
            executeExtension(orthosis_handle)
        elif disturbing[0]: 
            print(f"Error intro at {param_err.err_position} angle")
            executeFlexion(orthosis_handle)
        # Check if arm is fully extended
        checkExtensionEnd(flag_flexion_done)
    # Default condition
    else:
        stopMotion(orthosis_handle)
    # Hard limit check
    if param.orthosis_position >= param.max_pos or param.orthosis_position <= param.min_pos:
        stopMotion(orthosis_handle)


@dispatch(object, object, object, object, object)
def runExperimentRandomError(orthosis_handle, flag_flexion_done, disturbing, flag_flexion_started, flag_normal_trigger):
    """
    This function is the main function for the random error introduction with orthosis experiment.
    This is a modified version of the one created during Variscia's Thesis and used by Patrick and Sophia (stud_group_2) for the project
    Evaluation of Error Potential from EEG by error introduction on orthosis

    Conditions:
        - The force values will only be checked at the beginning of each trial
        - Once, the force feedback > f_sensitivity, the flexion or extension motions will be executed effortlessly
        - Depending upon the experiment conditions, param_err.num will be randomly introduced with the following conditions - 
            -> In each trial (flexion or extension), error will be introduced only once for param_err.duration ms
            -> Error will be introduced only in the centre part of the movement range
            -> No error will be introduced in consecutive trials

    Args:
        flag_flexion_done[0] (sa float)     : bool to check if flexion has been fully executed
        disturbing[0] (sa float)            : bool to check if the trial is an error trial
        flag_flexion_started[0] (sa float)  : bool to check if flexion has started
        flag_normal_trigger[0] (sa float)   : bool to check if the centre of movement has been reached during non-error execution
    """  
    if not param_err.num == 0:      
        if not disturbing[0] and not param_err.is_err_introduced:
            for i in param_err.err_sequence:
                if i == param.trial_count:
                    chooseErrorPosition()
                    setErrorFlags(disturbing)
                        
        if disturbing[0] and not param_err.is_err_introduced:
            checkErrorDuration(disturbing)

    # Check if enough force is applied for starting flexion
    if not flag_flexion_done[0] and not flag_flexion_started[0]:
        checkFlexionStart()
    # Check if enough force is applied for starting extension
    elif flag_flexion_done[0] and flag_flexion_started[0]:        
        checkExtensionStart()

    # Check if flexion is supposed to be executed
    if param.is_enough_force_for_motion and not flag_flexion_done[0]:
        flag_flexion_started[0] = True
        if not disturbing[0]:
            executeFlexion(orthosis_handle)
            if not param.trial_count in param_err.err_sequence:
                setNormalTrigger(flag_normal_trigger)
        elif disturbing[0]: 
            print(f"Error intro at {param_err.err_position} angle")
            executeExtension(orthosis_handle)
        # Check if arm is fully flexed
        checkFlexionEnd(flag_flexion_done)

    # Check if extension is supposed to be executed
    elif not param.is_enough_force_for_motion and flag_flexion_done[0]:
        flag_flexion_started[0] = False
        if not disturbing[0]:
            executeExtension(orthosis_handle)
            if not param.trial_count in param_err.err_sequence:
                setNormalTrigger(flag_normal_trigger)
        elif disturbing[0]: 
            print(f"Error intro at {param_err.err_position} angle")
            executeFlexion(orthosis_handle)
        # Check if arm is fully extended
        checkExtensionEnd(flag_flexion_done)
    # Default condition
    else:
        stopMotion(orthosis_handle)
    # Hard limit check
    if param.orthosis_position >= param.max_pos or param.orthosis_position <= param.min_pos:
        stopMotion(orthosis_handle)


def triggeredMotion(orthosis_handle):
    """
    This function performs the main functions of the experiment
            - detect the onset to start the motion 
            - complete the full episode (flexion and execution)
            - provide direciton commands for motion
    """
    # condition to check if there is an onset_detected
    if param_viz.onset_detected == True:
        param_viz.is_triggered = True
        param_viz.onset_detected = False

    # Logic for episodic motion
    if param_viz.is_triggered:
        # Doing a Flexion movement
        if not param_viz.is_flexion_done and param.orthosis_position < param.max_pos - param.buffer_pos:
            executeFlexion(orthosis_handle)
        # Reached upper limit and hence stop
        elif not param_viz.is_flexion_done and param.orthosis_position > param.max_pos - param.buffer_pos:
            stopMotion(orthosis_handle)
            param_viz.is_flexion_done = True
            time.sleep(0.3) # small delay when on upper position before extension 
        # Doing an Extension movement 
        elif param_viz.is_flexion_done and param.orthosis_position > param.min_pos + param.buffer_pos:
            executeExtension(orthosis_handle)
        # Reached lower limit. End of the episode
        elif param_viz.is_flexion_done and param.orthosis_position < param.min_pos + param.buffer_pos:
            stopMotion(orthosis_handle)
            param_viz.is_flexion_done = False
            param_viz.is_triggered = False
    else:
        stopMotion(orthosis_handle)

    # If the hard limit is reached
    if param.orthosis_position >= param.max_pos or param.orthosis_position <= param.min_pos:
        stopMotion(orthosis_handle)


def readValues(orthosis_handle):
    """
    This function provides the feedback from the orthosis by parsing the Serial data

    Returns(pseudo):
        param.orthosis_voltage        : voltage
        param.orthosis_deflection     : deflection
        param.orthosis_force          : force feedback
        param.orthosis_status         : status
        param.orthosis_position       : position feedback
        param.orthosis_f_offset       : force offset
    """
    values = orthosis_handle.readline()
    values = values.decode("utf-8").strip('\n')
    values = values.split(';')
    if len(values) != 5:
        return False
    else:
        try:
            param.orthosis_voltage = float(values[0])
            param.orthosis_deflection = float(values[1])
            param.orthosis_force = float(values[2])
            if param.is_calibrated:
                param.orthosis_force -= param.orthosis_f_offset
            param.orthosis_status = float(values[3])
            param.orthosis_position = float(values[4])
            return True
        except:
            return False
            # pass


def introduceRandomErrors():
    """
    This function randomly introduces errors in the experiment

    Returns(pseudo):
        param.disturbing  : flag to denote if the error is Introduced
        param.dist_onset  : time when the error is introduced
    """
    if not param.is_disturbing:
        rand_var = random.randint(0,param.n_trials)
        if rand_var == param.epsilon:
            param.is_disturbing = True
            param.dist_onset = time.time()
    else:
        if time.time()-param.dist_onset > param.err_duration:
            param.is_disturbing = False
 

def generateErrorSequence():
    """
    This function generates a list of random error trial positions
    Conditions:
        - There should be a gap of atleast 2 between consecutive numbers

    Args:
        param_err.start_num             : first acceptable trial number in which error can be introduced
        param.n_trials                  : total number of trials
        param_err.num                   : total number of errors to be introduced

    Returns:
        param_err.err_sequence (list)   : list of random trial positions
    """
    chk_flag = False
    if param_err.num != 0:
        while not chk_flag:
            # Generate a random list of integers containing "n_errors" elements betwen the specified range
            param_err.err_sequence = random.sample(range(param_err.start_num, param.n_trials), param_err.num)
            # Sort the list in ascending order
            param_err.err_sequence.sort()
            # Check the user defined conditions 
            ele_counter = 0
            for i in range(1,len(param_err.err_sequence)):
                if(param_err.err_sequence[i] - param_err.err_sequence[i-1] < param_err.gap_desired):
                    continue
                else:
                    ele_counter += 1

            if ele_counter == len(param_err.err_sequence)-1:
                chk_flag = True
    elif param_err.num == 0:
        chk_flag = True


def chooseErrorPosition():
    """
    This function generates a random number (position error) between the acceptable error range
    """
    param_err.err_position = random.randint(param_err.err_min_pos, param_err.err_max_pos)


def checkFlexionStart():
    """
    This function checks if enough force is applied by the wearer to start flexion
    """
    if param.orthosis_force < -param.f_sensitivity and param.orthosis_position > param.min_pos:
        param.is_enough_force_for_motion = True


def executeFlexion(orthosis_handle):
    """
    This function sends direction codes to the motor controller to move up
    """
    for c in param.direction_codes[1]:
        orthosis_handle.write(c.encode())


def checkFlexionEnd(flag_flexion_done):
    """
    This function checks if the arm is fully flexed
    """
    if param.orthosis_position >= param.max_pos:
        flag_flexion_done[0] = True
        param.trial_count +=1
        param_err.is_err_introduced = False


def checkExtensionStart():
    """
    This function checks if enough force is applied by the wearer to start extension
    """
    if param.orthosis_force > param.f_sensitivity + 0.1 and param.orthosis_position < param.max_pos:
        param.is_enough_force_for_motion = False


def executeExtension(orthosis_handle):
    """
    This function sends direction codes to the motor controller to move down
    """
    for c in param.direction_codes[2]:
        orthosis_handle.write(c.encode())


def checkExtensionEnd(flag_flexion_done):
    """
    This function checks if the arm is fully extended
    """
    if param.orthosis_position <= param.min_pos:
        flag_flexion_done[0] = False
        param.trial_count += 1
        param_err.is_err_introduced = False


def stopMotion(orthosis_handle):
    """
    This function sends direction codes to the motor controller to halt
    """
    for c in param.direction_codes[0]:
        orthosis_handle.write(c.encode())


def setNormalTrigger(flag_normal_trigger):
    """
    This function checks if the orthosis is near the middle of its range of motion and 
    sets the normal trigger flag accordingly
    """
    if (param.orthosis_position >= param_err.err_min_pos - param_err.buffer_pos) and \
                            (param.orthosis_position <= param_err.err_max_pos + param_err.buffer_pos):
        flag_normal_trigger[0] = 1.0
    else:
        flag_normal_trigger[0] = 0.0


def setErrorFlags(disturbing):
    """
    This function checks if the orthosis is near the middle of its range of motion and
    sets the disturbing flag and initialises the dist_onset timer
    """
    if (param.orthosis_position >= param_err.err_position - param_err.buffer_pos) and \
                            (param.orthosis_position <= param_err.err_position + param_err.buffer_pos):
        disturbing[0] = True
        param.dist_onset = time.time()


def checkErrorDuration(disturbing):
    """
    This function checks the error duration and if it is exceeded, sets the error flags to False 
    indicating that the error will no more be introduced in the movement 
    """
    if(time.time()-param.dist_onset > param_err.duration):
        disturbing[0] = False
        param_err.is_err_introduced = True
        param_err.err_count += 1

def headerFile(error_seq):
    """
    This function creates a header section for the log file with the experiment info
    """
    with open(f"{param.filename}.txt",'w') as f:
        f.write(f"Subject Name  : {param.sub_name} \n")
        f.write(f"Error duration: {param_err.duration} \n")
        f.write(f"Total errors  : {param_err.num} \n")
        f.write(f"Scenario      : {param.expt_scenario} \n")
        f.write(f"Err Sequence  : {error_seq} \n")
        f.write(f"Min Error Pos : {param_err.err_min_pos} \n")
        f.write(f"Max Error Pos : {param_err.err_max_pos} \n")
        f.write(f"Suffix        : {param.expt_suffix} \n")
        f.write(f"Set number    : {param.set_num} \n")
        f.write('Data Collection \n\n\n')  
    f.close()


def establishZMQ():
    """
    This function sets up the ZMQ Server client connection
    """
    my_context      = zmq.Context()
    my_socket       = my_context.socket(zmq.SUB)
    my_socket.connect("tcp://"+param.zmq_server_ip)
    my_socket.setsockopt(zmq.SUBSCRIBE, param.zmq_topic)

    return my_socket


def EstablishZMQPub():
    """
    Function to establish a ZMQ publisher (connection to WebAPP purpose)
    input : None

    Output : socket of ZMQ
    """
    port = "5001"
    # Creates a socket instance
    context = zmq.Context()
    mySocket = context.socket(zmq.PUB)
    # Binds the socket to a predefined port on localhost
    mySocket.bind(f"tcp://*:{port}")

    return mySocket


def ZMQPublish(datas, labels, stop_flag,mySocket):
    """
    function to publish data from orthosis device to WebApp.
    Input : 
    - array of data that will be sent
    - array of label correspond to the data 
    - stop flag value (Boolean)
    - socket of ZMQ

    output : None                                                   
    """
    
    if stop_flag == False:

        data_string = ""
        label_idx = 0
        for data in datas :
            data_string += labels[label_idx]
            data_string += f":{data}:"
            label_idx += 1

        print(data_string)
        mySocket.send_string(data_string)

        time.sleep(0.04)

    else :
        time.sleep(0.5)
        mySocket.send_string("STOP")
    
   
