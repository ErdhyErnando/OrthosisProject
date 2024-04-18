#!/usr/bin/env python3

############# NOTE #############
# This script is the multiprocessing script which appends all the values to the queue 
# and uses SharedArrays to share memory across processes.
################################

import multiprocessing as mp
import time
import SharedArray as sa
import time
# Appending the relative path of the root folder
import sys, os
# sys.path.append('../../')
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
print(sys.path)
import orthosis_interface.param.orthosis_param as param
import orthosis_interface.param.error_param as param_err

# Uncomment the following if you have pip installed the orthosis_lib
# import orthosis_lib.orthosis_v1_lib as orthosis_lib
# Uncomment the following otherwise
import orthosis_interface.lib.orthosis_lib.orthosis_v1_lib as orthosis_lib


def runZmqClient():
    param.is_client_running = True
    my_socket = orthosis_lib.establishZMQ()
    print("Waiting for Start Trigger!")
    while param.is_client_running:
        _, undecoded_msg = my_socket.recv_string().split(":")
        inp_msg[0] = int(undecoded_msg)
        print(f"Server msg received: {inp_msg[0]}")


def printTest():
    print(f"recent massage : {inp_msg[0]}")
    time.sleep(2)



if __name__ == "__main__":
    
    # Deleting old SharedArrays
    if len(sa.list()) != 0:
        sa.delete("shm://test")

    # Creating SharedArrays
    inp_msg         = sa.create("shm://test",1)

    pr_zmq_client   = mp.Process(target=runZmqClient)
    pr_printTest    = mp.Process(target=printTest)
    
    # Starting the processes
    pr_zmq_client.start()
    pr_printTest.start()
