#!/usr/bin/env python3

## !!!!! Variable file to store all variables used in the orthosis_v2 script !!!!! ##

import time

## Port Configuration ##
orthosis_can_socket             = "can0"
orthosis_motor_id               = 0x01
orthosis_motor_type             = "AK80_6_V1p1"
orthosis_socket_timeout         = 0.5

button_port_name                = '/dev/ttyUSB0'
button_baud_rate                = 9600

## Feedback Variables ##
orthosis_force                  = 0.0
orthosis_position               = 0.0
orthosis_pose_desired           = 0.0       # Desired position to send to motor

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
safe_interrupt                  = False     # Bool to check KeyboardInterrupt

## Experiment variables ##
fully_flexed_pos                = -90.0     # Position when the arm is fully flexed
fully_extended_pos              = -10.0     # Position when the arm is fully extended
n_trials                        = 30        # Total number of trials 
epsilon                         = 13        # Random number selected for error introduction
eff_thresh_ext                  = 1.2       # Effort threshold to detect extension
eff_thresh_flex                 = 1.0       # Effort threshold to detect flexion
trial_count                     = 0         # Total number of trials executed
step_inc                        = 0.0       # Step increment for the v2 motor
prev_cmd_time                   = time.time()
kp                              = 100.0     # PID controller Proportional Gain
kd                              = 1.5       # PID controller Derivative Gain
tau_ff                          = 0         # Torque offset
motor_loop_freq                 = 0.01      # 100 Hz motor loop frequency

## Button Listener variables ##
button_val                      = bytes(0)
is_listener_running             = False