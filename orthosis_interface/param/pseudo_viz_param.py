#!/usr/bin/env python3

## !!!!! Variable file to store all variables used for the Pseudo Visualisation of Onset Detection !!!!! ##

## Onset triggered variables
is_flexion_done         = False    # flag which is set True when the orthosis is fully flexed i.e. reaches max pose
is_triggered            = False    # flag to start the episode
onset_detected          = False    # Current value of onset detection
prev_onset_detected     = False    # previous value of onset_detected

## EMG variables ##
tval                    = 50       # how fast should we plot it, upscalen makes it faster 
update_interval         = 180      # 200 ms between updates
start_index             = 20000    # where to start in the whole measurement (how many movements ? )
