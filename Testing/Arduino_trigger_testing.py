import argparse
import serial
import multiprocessing as mp
import time
import SharedArray as sa
import time

# Appending the relative path of the root folder
import sys, os
from os.path import dirname, join, abspath
#sys.path.insert(0, abspath(join(dirname(__file__), '..')))
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
import signal

# Uncomment the following if you have pip installed the orthosis_lib
#from orthosis_lib.orthosis_v2_lib_oop import OrthosisLib, ButtonLib, TrigLib
# Uncomment the following otherwise
from orthosis_interface.lib.orthosis_lib.orthosis_v2_lib_oop import OrthosisLib, ButtonLib, TrigLib

def runTrigger():
    trig_obj = TrigLib('/dev/ttyACM0', 9600)
    setattr(trig_obj,'is_trigger_running', True)
    loop_idx = 0
    dt = 0.002
    print("Trigger Process Ready!!")

    loop_start_time = time.perf_counter()
    signal.signal(signal.SIGINT, trig_obj.signalHandler)
    signal.signal(signal.SIGQUIT, trig_obj.signalHandler)
    signal.signal(signal.SIGTSTP, trig_obj.signalHandler)

    while getattr(trig_obj, 'is_trigger_running'):
        loop_idx += 1
        if count[0]%2 == 0:
            trig_obj.arduino_handle.write(b'T')
            print("Changing Trigger T is sent")
            print(count[0])
        elif count[0]%2 != 0:
            trig_obj.arduino_handle.write(b'F')
            print("Changing Trigger F is sent")
            print(count[0])
            prev_led_state=False
        
        # Ensuring const. desired loop freq
        while time.perf_counter() - loop_start_time < dt * loop_idx: # This process does not work as intended for freq higher than 500 Hz (some triggers are not sent)
            pass
        # Safe KeyboardInterrupt
        if getattr(trig_obj, 'safe_interrupt'):
            print("Exiting Trigger process safely!")
            break


def counter():
    i = 0
    while i<90:
        i=i+1
        count[0] = i
        time.sleep(1)


if __name__== "__main__":

     #Deleting old SharedArrays
    if len(sa.list()) != 0:
        sa.delete("shm://count")

    # Creating SharedArrays
    count       = sa.create("shm://count",1)


    # Process 3 - Trigger generating process
    pr_trigger  = mp.Process(target=runTrigger)
    pr_counter = mp.Process(target=counter)

    # Starting the processes
    pr_counter.start()
    pr_trigger.start()

        