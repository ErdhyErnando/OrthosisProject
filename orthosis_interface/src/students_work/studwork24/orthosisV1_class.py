import argparse
import serial
import multiprocessing as mp
import time
import datetime
import SharedArray as sa
from pynput.keyboard import Listener  as KeyboardListener
from pynput.mouse    import Listener  as MouseListener
from pynput.keyboard import Key
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
import lib.orthosis_v1_lib_modified as orthosis_lib


class OrthosisV1 :
    def __init__(self,n_errors,duration,file_name,verbose,sensitivity,n_trial,sub_name,scenario,seq,suffix,num):
        param_err.num = n_errors
        param_err.duration = duration
        param.filename = file_name
        param.is_verbose = verbose
        param.f_sensitivity = sensitivity
        param.n_trials = n_trial
        param.sub_name = sub_name
        param.expt_scenario = scenario
        param.expt_seq = seq
        param.expt_suffix = suffix
        param.set_num = num


        today     =   datetime.date.today() 
        # param.filename  =   '../data/' + str(today.strftime("%d%m%Y")) + '_' + param.sub_name + '_' + param.expt_scenario + '_' + param.expt_seq + '_' + param.expt_suffix + '_' + param.set_num + '_orthosis'
        # param.filename  =   str(today.strftime("%d%m%Y")) + '_' + param.sub_name + '_' + param.expt_scenario + '_' + param.expt_seq + '_' + param.expt_suffix + '_' + param.set_num
        param.filename  =   '../../../data/' + str(today.strftime("%d%m%Y")) + '_' + param.sub_name + '_' + param.expt_scenario + '_' + param.expt_seq + '_' + param.expt_suffix + '_' + param.set_num + '_orthosis'
        
        # Queue object to append all values to log 
        self.data_list_q     = mp.Queue()

        # Deleting old SharedArrays
        if len(sa.list()) != 0:
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

        # Creating SharedArrays
        self.inp_msg             = sa.create("shm://test",1)
        self.is_write            = sa.create("shm://wr",1)

        self.start_time          = sa.create("shm://start",1)
        self.end_time            = sa.create("shm://end",1)

        self.is_pressed          = sa.create("shm://button",1)
        self.flag_flexion_done   = sa.create("shm://flex",1)
        self.disturbing          = sa.create("shm://dist",1)
        self.trial_counter       = sa.create("shm://trialCount",1)
        self.current_pos         = sa.create("shm://position",1)
        self.error_pos           = sa.create("shm://err_pos",1)
        self.error_seq           = sa.create("shm://err_seq",param_err.num)

        # Process 1 - Orthosis process
        pr_orthosis    = mp.Process(target=self.runOrthosis)

        # Process 2 - Button press process
        pr_button      = mp.Process(target=self.runButton)

        # Process 3 - ZMQ-Socket connection process (not needed for now)
        pr_zmq_client  = mp.Process(target=self.runZmqClient)
        
        # Process 4 - Data logging process
        pr_logger      = mp.Process(target=self.runLogger)

        # Starting the processes
        pr_orthosis.start()
        pr_button.start()
        pr_zmq_client.start()
        pr_logger.start()

    

    def runOrthosis(self):
        orthosis_handle = serial.Serial(port=param.orthosis_port_name, baudrate=param.orthosis_baud_rate)
        param.is_orthosis_running=True
        orthosis_lib.calibrate(orthosis_handle)
        orthosis_lib.generateErrorSequence()
        self.disturbing[0] = False
        self.flag_flexion_done[0] = False
        self.inp_msg[0] = 1
        i = 0
        for i in range(len(param_err.err_sequence)):
            self.error_seq[i] = param_err.err_sequence[i]

        print("Orthosis Process Ready!!")
        self.trial_counter[0] = 0
        while param.trial_count < param.n_trials:
            orthosis_lib.readValues(orthosis_handle)
            orthosis_lib.runExperimentRandomError(orthosis_handle, self.flag_flexion_done, self.disturbing)
            self.trial_counter[0] = param.trial_count
            self.current_pos[0] = param.orthosis_position
            self.error_pos[0] = param_err.err_position
            if param.is_verbose and not self.is_write[0]:
                print(f"Trial Count: {param.trial_count}")
                print(f"Error Count: {param_err.err_count}")
                print(f"Error Seq  : {param_err.err_sequence}")
        print("done!!!")
        self.inp_msg[0] = 2   


    # Old code for button
    # def runButton():
    #     button_handle   = serial.Serial(port=param.button_port_name, baudrate=param.button_baud_rate)
    #     param.is_listener_running= True
    #     print("Button Listener Ready!!")
    #     while param.is_listener_running:
    #         if button_handle.in_waiting > 0:
    #             param.button_val = button_handle.read()
    #             if param.button_val == b'\x01':
    #                 self.is_pressed[0] = True
    #                 print("Button Pressed!!")
    #             elif param.button_val == b'\x00':
    #                 self.is_pressed[0] = False


    def runButton(self):
        def on_release(key):
            if key == Key.esc:
                print("exit run Button")
                m_listener.stop()
                return False   

        def on_click(x, y, button, pressed):
            if pressed:
                self.is_pressed[0] = True
                print("Button Pressed!!")
            else:
                self.is_pressed[0] = False
                print("Button Released")

        with KeyboardListener(on_release=on_release) as k_listener, \
            MouseListener(on_click=on_click) as m_listener:
                k_listener.join()
                m_listener.join()


    def runZmqClient(self):
        param.is_client_running = True
        my_socket = orthosis_lib.establishZMQ()
        print("Waiting for Start Trigger!")
        while param.is_client_running:
            undecoded_msg = my_socket.recv()
            self.inp_msg[0] = int(undecoded_msg[2:])
            if self.inp_msg[0] == 1:
                self.start_time[0] = time.perf_counter()
            elif self.inp_msg[0] == 2:
                self.end_time[0] = time.perf_counter()
            print(f"Server msg received: {self.inp_msg[0]}")


    def mapAngle(angle):
        real_angle = 0.1*angle-90
        return real_angle
    

    def runLogger(self):
        param.is_logger_running = True
        # orthosis_lib.headerFile(error_seq)
        self.is_write[0] = False
        loop_idx    = 0
        loop_freq   = 1000
        dt          = 1/loop_freq
        print("Logger Process Ready!!")
        loop_start_time = time.perf_counter()
        while param.is_logger_running:
            # Increment loop index
            loop_idx += 1
            if self.inp_msg[0] == 1: 
                self.data_list_q.put("Measurement Start!!" + '\n') 
                self.start_time[0] = time.perf_counter()
                self.inp_msg[0]= 3
            elif self.inp_msg[0] == 2: 
                self.data_list_q.put("Measurement End!!" + '\n')
                self.end_time[0] = time.perf_counter()
                self.inp_msg[0] = 4
                self.is_write[0] = True
                print(f"is_write {self.is_write[0]}")
            if self.inp_msg[0] == 3:
                self.data_list_q.put(f" ,{self.trial_counter[0]}")
                self.data_list_q.put(f" ,{self.mapAngle(self.current_pos[0])}")
                self.data_list_q.put(f" ,{self.mapAngle(self.error_pos[0])}")
                #data_list_q.put(time.perf_counter() - start_time[0])
                # Flexion or Extension
                if not self.flag_flexion_done[0]:
                    self.data_list_q.put(' ,F')
                else:
                    self.data_list_q.put(' ,E')
                # Error Introduced or not
                if self.disturbing[0]:
                    self.data_list_q.put(' ,Y')
                else:
                    self.data_list_q.put(' ,N')
                # Button Press Status
                if self.is_pressed[0]:
                    self.data_list_q.put(' ,P\n')
                else:
                    self.data_list_q.put(' ,NP\n')
            
            # Writing to the file
            if self.is_write[0]:
                print("Exiting Logger Loop!")
                print("Entered file condition")
                orthosis_lib.headerFile(self.error_seq)
                f = open("%s.txt" %param.filename, "a+")
                f.write(f"Measurement Duration : {self.end_time[0] - self.start_time[0]}")
                f.write('\n\n')
                for i in range(self.data_list_q.qsize()):
                    f.write(str(self.data_list_q.get()))
                f.close()
                print("All data written to file")
                self.is_write[0] = False
                param.is_logger_running = False

            # Ensuring const. desired loop freq
            while time.perf_counter() - loop_start_time < dt * loop_idx:
                pass