#!/usr/bin/env python3

## !!!!! Variable file to store all variables used in the orthosis_basic script !!!!! ##

import time

## Port Configuration ##
orthosis_port_name              = '/dev/ttyUSB0'
orthosis_baud_rate              = 128000

button_port_name                = '/dev/ttyUSB1'
button_baud_rate                = 9600

zmq_server_ip                   = "192.168.217.112:34761"

## Direction of Motion ##
move_up                         = ['a', '1', ';', 'b', '0', ';' ]
move_down                       = ['a', '0', ';', 'b', '1', ';' ]
stop_motion                     = ['a', '0', ';', 'b', '0', ';' ]
direction_codes                 = [stop_motion, move_up, move_down]

## Feedback Variables ##
orthosis_voltage                = 0.0
orthosis_deflection             = 0.0
orthosis_force                  = 0.0
orthosis_status                 = 0.0
orthosis_position               = 0.0
orthosis_f_offset               = 0.0

## Status booleans ##
is_orthosis_running             = False
is_calibrated                   = False
is_disturbing                   = False
is_verbose                      = True
dist_onset                      = time.time()
intro_errors                    = False
is_flexion_done                 = False
is_flexion_started              = False
is_enough_force_for_motion      = False

## Experiment variables ##
min_pos                         = 900.0    # Position when the arm is resting down
max_pos                         = 1800.0   # Position when the arm is up ppl to the body
buffer_pos                      = 65       # value which defines a soft limit range for min and max pose
n_trials                        = 30       # Total number of trials 
epsilon                         = 13       # Random number selected for error introduction
err_duration                    = 0.1      # Duration for error to last
f_sensitivity                   = 0.25     # Force sensitivity to detect a motion
trial_count                     = 0        # Total number of trials executed

## Button Listener variables ##
button_val                      = bytes(0)
is_listener_running             = False

## ZMQ Socket Client Variables ##
zmq_topic                       = b"10"
is_client_running               = False

## Logger variables ##
is_logger_running               = False
sub_name                        = "XYZ"
expt_scenario                   = "A"
expt_seq                        = "0"
expt_suffix                     = "H"
set_num                         = "1"
filename                        = "ABC.txt"
