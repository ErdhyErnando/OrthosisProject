#!/usr/bin/env python3

## This library contains all the methods being used for the orthosis force control thread ##

import random
import time
# Appending the relative path of the root folder
import sys, os
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
import param.orthosis_v2_param as param
import param.error_v2_param as param_err


def runExperimentRandomError(flag_flexion_done, disturbing, flag_flexion_started, flag_normal_trigger):
    """
    This function is the main function for the random error introduction with orthosis experiment.
    This is a modified version of the one created during Variscia's Thesis and used by Patrick and Sophia (stud_group_2) for the project
    Evaluation of Error Potential from EEG by error introduction on orthosis

    Conditions:
        - The force values will only be checked at the beginning of each trial
        - Once, the force feedback > eff_thresh, the flexion or extension motions will be executed effortlessly
        - Depending upon the experiment conditions, param_err.num will be randomly introduced with the following conditions - 
            - In each trial (flexion or extension), error will be introduced only once for param_err.duration ms
            - Error will be introduced only in the centre part of the movement range
            - No error will be introduced in consecutive trials

    Args:
        flag_flexion_done: 
            (sa float) bool to check if flexion has been fully executed
        disturbing: 
            (sa float) bool to check if the trial is an error trial
        flag_flexion_started : 
            (sa float) bool to check if flexion has started
        flag_normal_trigger: 
            (sa float) bool to check if the centre of movement has been reached during non-error execution
    """  
    if not param_err.num == 0:      
        if not disturbing[0] and not param_err.is_err_introduced:
            for i in param_err.err_sequence:
                if i == param.trial_count:
                    if not param_err.err_gen_idx:
                        chooseErrorPosition()
                        param_err.err_gen_idx = 1
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
            executeFlexion()
            if not param.trial_count in param_err.err_sequence:
                setNormalTrigger(flag_normal_trigger)
        elif disturbing[0]: 
            print(f"Error intro at {param_err.err_position} angle")
            executeExtension()
        # Check if arm is fully flexed
        checkFlexionEnd(flag_flexion_done)

    # Check if extension is supposed to be executed
    elif not param.is_enough_force_for_motion and flag_flexion_done[0]:
        flag_flexion_started[0] = False
        if not disturbing[0]:
            executeExtension()
            if not param.trial_count in param_err.err_sequence:
                setNormalTrigger(flag_normal_trigger)
        elif disturbing[0]: 
            print(f"Error intro at {param_err.err_position} angle")
            executeFlexion()
        # Check if arm is fully extended
        checkExtensionEnd(flag_flexion_done)
    # Default condition
    else:
        stopMotion()
    # Hard limit check
    if param.orthosis_position >= param.fully_extended_pos or param.orthosis_position <= param.fully_flexed_pos:
        stopMotion()

def move_to_start_position(start_pos, orthosis_handle): 

    """
    This function moves the orthosis to a start position starting from the initial position at angle 0.0. 

    Args:
        start_pos: 
            the start position where to move (target angle)
    """

    moved_to_start_pos = False 
    if not moved_to_start_pos: 
        while param.orthosis_position >= start_pos: 
            readValues(orthosis_handle)
            executeFlexion()
        # if start position reached 
        moved_to_start_pos = True
        stopMotion()



def readValues(orthosis_handle):
    """
    This function provides the feedback from the orthosis by parsing the Serial data

    Returns:
        param.orthosis_force: 
            (pseudo) force feedback
        param.orthosis_position: 
            (pseudo) position feedback
    """

    if time.time() - param.prev_cmd_time >= param.motor_loop_freq:
        param.orthosis_pose_desired = param.orthosis_pose_desired + param.step_inc
        param.orthosis_position, _, param.orthosis_force = orthosis_handle.send_deg_command(param.orthosis_pose_desired, 
                                                                                        0,
                                                                                        kp=param.kp,
                                                                                        kd=param.kd,
                                                                                        tau_ff=param.tau_ff)
        # print(f"position: {param.orthosis_position}")
        param.prev_cmd_time = time.time()
 

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
        param_err.err_sequence: 
            (list) list of random trial positions
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


def checkFlexionStart():
    """
    This function checks if enough force is applied by the wearer to start flexion
    """
    if param.orthosis_force > param.eff_thresh_flex and param.orthosis_position <= param.fully_extended_pos:
        param.is_enough_force_for_motion = True


def executeFlexion():
    """
    This function sends direction codes to the motor controller to move up
    """
    param.step_inc = -0.2


def checkFlexionEnd(flag_flexion_done):
    """
    This function checks if the arm is fully flexed
    """
    if param.orthosis_position <= param.fully_flexed_pos:
        flag_flexion_done[0] = True
        param.trial_count +=1
        param_err.is_err_introduced = False
        param_err.err_gen_idx = 0


def checkExtensionStart():
    """
    This function checks if enough force is applied by the wearer to start extension
    """
    if param.orthosis_force < -param.eff_thresh_ext and param.orthosis_position >= param.fully_flexed_pos :
        param.is_enough_force_for_motion = False


def executeExtension():
    """
    This function sends direction codes to the motor controller to move down
    """
    param.step_inc = 0.2

def checkExtensionEnd(flag_flexion_done):
    """
    This function checks if the arm is fully extended
    """
    if param.orthosis_position >= param.fully_extended_pos:
        flag_flexion_done[0] = False
        param.trial_count += 1
        param_err.is_err_introduced = False
        param_err.err_gen_idx = 0


def stopMotion():
    """
    This function sends direction codes to the motor controller to halt
    """
    param.step_inc = 0.0

def setNormalTrigger(flag_normal_trigger):
    """
    This function checks if the orthosis is near the middle of its range of motion and 
    sets the normal trigger flag accordingly
    """
    if param.orthosis_position >= param_err.err_min_pos and \
                            param.orthosis_position <= param_err.err_max_pos:
        flag_normal_trigger[0] = 1.0
    else:
        flag_normal_trigger[0] = 0.0


def chooseErrorPosition():
    """
    This function generates a random number (position error) between the acceptable error range
    """
    param_err.err_position = random.randint(param_err.err_min_pos, param_err.err_max_pos)


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


def signalHandler(signal,frame):
    """
    This method handles the keyboard interrupt signal and shuts down the resp. process safely.
    """
    param.safe_interrupt = True
    
