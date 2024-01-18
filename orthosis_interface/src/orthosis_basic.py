#!/usr/bin/env python3


## !!!!! Important Conventions to keep in mind !!!!! ##
    # When the arm is resting down, it corresponds to a raw position of ~900.0
    # When the arm is flexed, it corresponds to a raw position of ~1800.0
    # During Flexion (upward motion), the Force values are negative
    # During Extension (downward motion), the Force values are positive
## !!!!! ************************************* !!!!! ##

import serial
import threading
import argparse
# Appending the relative path of the root folder 
import sys, os
# sys.path.append('../')
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
import param.orthosis_param as param        # Param file consisting of all the required variables for the script
import lib.orthosis_lib.orthosis_v1_lib as orthosis_lib


def runOrthosis(orthosis_handle):
    """
    This is the main target method for the thread 

    Parameters:
        orthosis_handle : The serial port configuration instance
    """
    # print("Entered the thread function")
    param.is_orthosis_running=True
    orthosis_lib.calibrate(orthosis_handle)
    while param.is_orthosis_running:
        orthosis_lib.readValues(orthosis_handle)
        # orthosis_lib.forceControl(orthosis_handle)
        orthosis_lib.runExperiment(orthosis_handle)
        if param.is_verbose:
            print("voltage: %f\n" %   param.orthosis_voltage)
            print("deflection: %f\n" %   param.orthosis_deflection)
            print("Force: %f\n" %   param.orthosis_force)
            print("status: %f\n" %   param.orthosis_status)
            print("position: %f\n" %   param.orthosis_position)
            print("F_Offset: %f\n\n" % param.orthosis_f_offset)


def assignRuntimeVars(args):
    if args['port_name'] is not None:
        param.port_name = args['port_name']
    if args['is_verbose'] is not None:
        param.is_verbose = bool(args['is_verbose'])
    if args['n_trials'] is not None:
        param.n_trials = int(args['n_trials'])
    if args['intro_errors'] is not None:
        param.intro_errors = bool(args['intro_errors'])
    if args['epsilon'] is not None:
        param.epsilon = int(args['epsilon'])
    if args['err_duration'] is not None:
        param.err_duration = float(args['err_duration'])
    if args['f_sensitivity'] is not None:
        param.f_sensitivity = float(args['f_sensitivity'])


if __name__ == "__main__":
    ## Defining the argument parser
    parser = argparse.ArgumentParser("Parser for accepting run-time arguments")
    parser.add_argument('-port','--port_name',help='Serial Port name')
    parser.add_argument('-v','--is_verbose',help='Bool to decide if the values need to be logged into console or not')
    parser.add_argument('-nt','--n_trials',help='Total number of trials to perform')
    parser.add_argument('-ie','--intro_errors',help='Bool to suggest if error has to be introduced or not')
    parser.add_argument('-e','--epsilon',help='Random number for error introduction')
    parser.add_argument('-ed','--err_duration',help='Duration for error to last')
    parser.add_argument('-fs','--f_sensitivity',help='Force sensitivity to detect a motion')
    args = vars(parser.parse_args())

    ## Assigning run-time variables to the Parameters
    assignRuntimeVars(args)

    ## Configure the serial port
    orthosis_handle = serial.Serial(port=param.orthosis_port_name, baudrate=param.orthosis_baud_rate)
    
    ## Declaring the orthosis thread
    orthosis = threading.Thread(target=runOrthosis, args=(orthosis_handle,))
    ## Starting the thread
    orthosis.start()
