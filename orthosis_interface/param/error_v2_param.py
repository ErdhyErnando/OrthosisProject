#!/usr/bin/env python3

## !!!!! Variable file to store all variables used to introduce random errors into Orthosis !!!!! ##

## Error Parameters ##
num                 = 6             # Total number of errors to be introduced
duration            = 0.25          # Duration of introduced error in sec. (0.075 or 0.25)
err_position        = -50.0         # Exact raw position when error will be introduced
buffer_pos          = 3.0           # Buffer for introducing errors
err_min_pos         = -55.0         # Start limit for error range
err_max_pos         = -45.0         # End limit for error range
err_count           = 0             # Total number of errors introduced
start_num           = 2             # Start idx for generating random error samples
gap_desired         = 3             # Desired gap between consecutive error trials

is_err_introduced   = False         # Flag to check if error has been introduced
err_sequence        = []            # List of trial numbers where error needs to be introduced
err_gen_idx         = 0             # Index to ensure that the random error position is only generated once every trial
