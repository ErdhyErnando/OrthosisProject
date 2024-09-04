import random
import time
import serial
from motor_driver.canmotorlib import CanMotorController
import zmq
import SharedArray as sa

class OrthosisLib():
    """
    This class contains all the methods used for the functioning of the orthosis v2.
    """

    def __init__(self, can_socket="can0", motor_id=0x01, motor_type="AK80_6_V1p1", socket_timeout=0.05):
        # Initialise the motor controller attributes
        self.orthosis_can_socket    = can_socket
        self.orthosis_motor_id      = motor_id
        self.orthosis_motor_type    = motor_type
        self.orthosis_socket_timeout= socket_timeout
        # Instantiate the orthosis can handle
        self.orthosis_handle = CanMotorController(can_socket=self.orthosis_can_socket, motor_id=self.orthosis_motor_id, motor_type=self.orthosis_motor_type, socket_timeout=self.orthosis_socket_timeout)
        # Initialise error attributes
        self.init_error_attr()
        # Initialise orthosis attributes
        self.init_orthosis_attr()
    
    
    def init_error_attr(self):
        """
        This method initialises the error attributes
        """
        self.n_err                  = 6             # Total number of errors to be introduced
        self.duration               = 0.25          # Duration of introduced error in sec. (0.075 or 0.25)
        self.err_position           = -50.0         # Exact raw position when error will be introduced
        self.buffer_pos             = 3.0           # Buffer for introducing errors
        self.err_min_pos            = -55.0         # Start limit for error range
        self.err_max_pos            = -45.0         # End limit for error range
        self.err_count              = 0             # Total number of errors introduced
        self.start_num              = 2             # Start idx for generating random error samples
        self.gap_desired            = 3             # Desired gap between consecutive error trials

        self.is_err_introduced      = False         # Flag to check if error has been introduced
        self.err_sequence           = []            # List of trial numbers where error needs to be introduced

        self.err_gen_idx            = 0             # Index to ensure that the random error position is only generated once every trial


    def init_orthosis_attr(self):
        """
        This method initialises the orthosis attributes
        """
        ## Feedback Variables ##
        self.orthosis_force             = 0.0
        self.orthosis_position          = 0.0
        self.orthosis_pose_desired      = 0.0       # Desired position to send to motor

        ## Status booleans ##
        self.is_orthosis_running        = False
        self.is_calibrated              = False
        self.is_disturbing              = False
        self.is_verbose                 = True
        self.dist_onset                 = time.time()
        self.intro_errors               = False
        self.is_flexion_done            = False
        self.is_flexion_started         = False
        self.is_enough_force_for_motion = False
        self.safe_interrupt             = False     # Bool to check KeyboardInterrupt

        ## Experiment variables ##
        self.fully_flexed_pos           = -90.0     # Position when the arm is fully flexed
        self.fully_extended_pos         = -10.0     # Position when the arm is fully extended
        self.n_trials                   = 30        # Total number of trials 
        self.eff_thresh_ext             = 1.2       # Effort threshold to detect extension
        self.eff_thresh_flex            = 1.0       # Effort threshold to detect flexion
        self.trial_count                = 0         # Total number of trials executed
        self.step_inc                   = 0.0       # Step increment for the v2 motor
        self.prev_cmd_time              = time.time()
        self.kp                         = 100.0     # PID controller Proportional Gain
        self.kd                         = 1.5       # PID controller Derivative Gain 1.5
        self.tau_ff                     = 0         # Torque offset
        self.motor_loop_freq            = 0.01      # 100 Hz motor loop frequency
        self.step_size                  = 0.3       # Step size for step inc
        ## Visualisation variables ##
        self.is_triggered               = False     # Bool to check if the orthosis is triggered by EMG onset

        
         

    def runExperimentRandomError(self, flag_flexion_done, disturbing, flag_flexion_started, flag_normal_trigger):
        """
        This is the main method for the random error introduction with orthosis experiment.
        This is a modified version of the one created during Variscia's Thesis and used by Patrick and Sophia (stud_group_2) for the project
        Evaluation of Error Potential from EEG by error introduction on orthosis.

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
            flag_flexion_started: 
                (sa float) bool to check if flexion has started
            flag_normal_trigger: 
                (sa float) bool to check if the centre of movement has been reached during non-error execution
        """  
        if not self.n_err == 0:      
            if not disturbing[0] and not self.is_err_introduced:
                for i in self.err_sequence:
                    if i == self.trial_count:
                        if not self.err_gen_idx:
                            self.chooseErrorPosition()
                            self.err_gen_idx = 1
                        self.setErrorFlags(disturbing)
                            
            if disturbing[0] and not self.is_err_introduced:
                self.checkErrorDuration(disturbing)

        # Check if enough force is applied for starting flexion
        if not flag_flexion_done[0] and not flag_flexion_started[0]:
            self.checkFlexionStart()
        # Check if enough force is applied for starting extension
        elif flag_flexion_done[0] and flag_flexion_started[0]:        
            self.checkExtensionStart()

        # Check if flexion is supposed to be executed
        if self.is_enough_force_for_motion and not flag_flexion_done[0]:
            flag_flexion_started[0] = True
            if not disturbing[0]:
                self.executeFlexion()
                if not self.trial_count in self.err_sequence:
                    self.setNormalTrigger(flag_normal_trigger)
            elif disturbing[0]:
                print(f"Error intro at {self.err_position} angle")
                self.executeExtension()
            # Check if arm is fully flexed
            self.checkFlexionEnd(flag_flexion_done)

        # Check if extension is supposed to be executed
        elif not self.is_enough_force_for_motion and flag_flexion_done[0]:
            flag_flexion_started[0] = False
            if not disturbing[0]:
                self.executeExtension()
                if not self.trial_count in self.err_sequence:
                    self.setNormalTrigger(flag_normal_trigger)
            elif disturbing[0]: 
                print(f"Error intro at {self.err_position} angle")
                self.executeFlexion()
            # Check if arm is fully extended
            self.checkExtensionEnd(flag_flexion_done)
        # Default condition
        else:
            self.stopMotion()
        # Hard limit check
        if self.orthosis_position >= self.fully_extended_pos or self.orthosis_position <= self.fully_flexed_pos:
            self.stopMotion()
    
    def triggeredMotion(self, onset_detected):
        """
        This function performs the main functions of the experiment
                - detect the onset to start the motion 
                - complete the full episode (flexion and execution)
                - provide direciton commands for motion
        """
        # condition to check if there is an onset_detected
        if onset_detected[0] == True:
            self.is_triggered = True
            onset_detected[0] = False

        # Logic for episodic motion
        if self.is_triggered:
            # Doing a Flexion movement
            if not self.is_flexion_done and self.orthosis_position >= self.fully_flexed_pos:
                self.executeFlexion()
            # Reached upper limit and hence stop
            elif not self.is_flexion_done and self.orthosis_position <= self.fully_flexed_pos:
                self.stopMotion()
                self.is_flexion_done = True
                time.sleep(0.3) # small delay when on upper position before extension 
            # Doing an Extension movement 
            elif self.is_flexion_done and self.orthosis_position <= self.fully_extended_pos:
                self.executeExtension()
            # Reached lower limit. End of the episode
            elif self.is_flexion_done and self.orthosis_position >= self.fully_extended_pos:
                self.stopMotion()
                self.is_flexion_done = False
                self.is_triggered = False
        else:
            self.stopMotion()

        # Hard limit check
        if self.orthosis_position > self.fully_extended_pos+5 or self.orthosis_position < self.fully_flexed_pos-5:
            self.stopMotion()


    def move_to_start_position(self, start_pos): 
        """
        This method moves the orthosis to a start position starting from the initial position at angle 0.0. 

        Args:
            start_pos: 
                the start position where to move (target angle)
        """
        moved_to_start_pos = False 
        if not moved_to_start_pos: 
            while self.orthosis_position >= start_pos: 
                self.readValues()
                self.executeFlexion()
            # if start position reached 
            moved_to_start_pos = True
            self.stopMotion()


    def readValues(self):
        """
        This method sends motion command to the motor and receives the current position and effort feedback.

        Returns:
            orthosis_force: 
                (pseudo) force feedback
            orthosis_position: 
                (pseudo) position feedback
        """

        if time.time() - self.prev_cmd_time >= self.motor_loop_freq:
            self.orthosis_pose_desired = self.orthosis_pose_desired + self.step_inc
            self.orthosis_position, _, self.orthosis_force = self.orthosis_handle.send_deg_command(self.orthosis_pose_desired, 
                                                                                            0,
                                                                                            kp=self.kp,
                                                                                            kd=self.kd,
                                                                                            tau_ff=self.tau_ff)
            # print(f"position: {self.orthosis_position}")
            self.prev_cmd_time = time.time()
    

    def generateErrorSequence(self):
        """
        This method generates a list of random error trial positions.
        Conditions:
            - There should be a gap of atleast 2 between consecutive numbers.

        Returns:
            err_sequence: 
                (list) list of random trial positions
        """
        chk_flag = False
        if self.n_err != 0:
            while not chk_flag:
                # Generate a random list of integers containing "n_errors" elements betwen the specified range
                self.err_sequence = random.sample(range(self.start_num, self.n_trials), self.n_err)
                # Sort the list in ascending order
                self.err_sequence.sort()
                # Check the user defined conditions 
                ele_counter = 0
                for i in range(1,len(self.err_sequence)):
                    if(self.err_sequence[i] - self.err_sequence[i-1] < self.gap_desired):
                        continue
                    else:
                        ele_counter += 1

                if ele_counter == len(self.err_sequence)-1:
                    chk_flag = True
        elif self.n_err == 0:
            chk_flag = True


    def checkFlexionStart(self):
        """
        This method checks if enough force is applied by the wearer to start flexion.
        """
        if self.orthosis_force > self.eff_thresh_flex and self.orthosis_position <= self.fully_extended_pos:
            self.is_enough_force_for_motion = True


    def executeFlexion(self):
        """
        This method sends direction codes to the motor controller to move up.
        """
        self.step_inc = -self.step_size


    def checkFlexionEnd(self, flag_flexion_done):
        """
        This method checks if the arm is fully flexed.
        """
        if self.orthosis_position <= self.fully_flexed_pos:
            flag_flexion_done[0] = True
            self.trial_count +=1
            self.is_err_introduced = False
            self.err_gen_idx = 0


    def checkExtensionStart(self):
        """
        This method checks if enough force is applied by the wearer to start extension.
        """
        if self.orthosis_force < -self.eff_thresh_ext and self.orthosis_position >= self.fully_flexed_pos :
            self.is_enough_force_for_motion = False


    def executeExtension(self):
        """
        This method sends direction codes to the motor controller to move down.
        """
        self.step_inc = self.step_size


    def checkExtensionEnd(self, flag_flexion_done):
        """
        This method checks if the arm is fully extended.
        """
        if self.orthosis_position >= self.fully_extended_pos:
            flag_flexion_done[0] = False
            self.trial_count += 1
            self.is_err_introduced = False
            self.err_gen_idx = 0


    def stopMotion(self):
        """
        This method sends direction codes to the motor controller to halt.
        """
        self.step_inc = 0.0


    def setNormalTrigger(self, flag_normal_trigger):
        """
        This method checks if the orthosis is near the middle of its range of motion and 
        sets the normal trigger flag accordingly.
        """
        if self.orthosis_position >= self.err_min_pos and \
                                self.orthosis_position <= self.err_max_pos:
            flag_normal_trigger[0] = 1.0
        else:
            flag_normal_trigger[0] = 0.0


    def chooseErrorPosition(self):
        """
        This method generates a random number (position error) between the acceptable error range.
        """
        self.err_position = random.randint(self.err_min_pos, self.err_max_pos)


    def setErrorFlags(self, disturbing):
        """
        This method checks if the orthosis is near the middle of its range of motion and
        sets the disturbing flag and initialises the dist_onset timer.
        """
        if (self.orthosis_position >= self.err_position - self.buffer_pos) and \
                                (self.orthosis_position <= self.err_position + self.buffer_pos):
            disturbing[0] = True
            self.dist_onset = time.time()


    def checkErrorDuration(self, disturbing):
        """
        This method checks the error duration and if it is exceeded, sets the error flags to False 
        indicating that the error will no more be introduced in the movement. 
        """
        if(time.time()-self.dist_onset > self.duration):
            disturbing[0] = False
            self.is_err_introduced = True
            self.err_count += 1


    def signalHandler(self, signal,frame):
        """
        This method handles the keyboard interrupt signal and shuts down the resp. process safely.
        """
        self.safe_interrupt = True


class ButtonLib():
    """
    This class contains all the methods for setting up and reading the button press states.
    """

    def __init__(self, port_name='/dev/ttyUSB0', baud_rate=9600):
        # Initialise button handle attributes
        self.button_port_name = port_name
        self.button_baud_rate = baud_rate
        # Instantiate the button handle
        self.button_handle   = serial.Serial(port=self.button_port_name, baudrate=self.button_baud_rate)
        # Initialise button listener attributes
        self.button_val         = bytes(0)
        self.is_listener_running= False
        self.safe_interrupt     = False     # Bool to check KeyboardInterrupt
    
    
    def getButtonState(self, is_pressed):
        """
        This method reads the button state continuously. 
        If the button is pressed, it will set the is_pressed attribute to True.

        Args:
            is_pressed: 
                (sa_float) bool to check if the button is pressed
        """
        if self.button_handle.in_waiting > 0:
            self.button_val = self.button_handle.read().decode("utf-8")
            if self.button_val == '-':
                is_pressed[0] = True
                print("Button Pressed!!")
            elif self.button_val == ',':
                is_pressed[0] = False
    

    def signalHandler(self,signal,frame):
        """
        This method handles the keyboard interrupt signal and shuts down the resp. process safely.
        """
        self.safe_interrupt = True



class TrigLib():
    """
    This class sets up the serial port for sending trigger bytes to the Event Trigger board.
    """

    def __init__(self, port_name='/dev/ttyUSB1', baud_rate=9600):
        # Initialise arduino handle attributes
        self.arduino_port_name = port_name
        self.arduino_baud_rate = baud_rate
        # Instantiate the arduino handle
        self.arduino_handle = serial.Serial(port=self.arduino_port_name, baudrate=self.arduino_baud_rate)
        # Initialise trigger booleans
        self.is_trigger_running = False
        self.safe_interrupt     = False
    
    def signalHandler(self,signal,frame):
        """
        This method handles the keyboard interrupt signal and shuts down the resp. process safely.
        """
        self.safe_interrupt = True



class FlaskZMQPub():
    """
    Object that connect the orthosis device to the web trough ZMQ                                           
    """

    def __init__(self):
        """
        Initialize ZMQ Publisher connection
        """
        
        port = "5001"
        # Creates a socket instance
        context = zmq.Context()
        self.mySocket = context.socket(zmq.PUB)
        # Binds the socket to a predefined port on localhost
        self.mySocket.bind(f"tcp://*:{port}")


    def zmq_publish(self,datas,labels,StopFlag):
        """
        Publish data to the JS WebAPP
        input :
            Arr Datas (Float)   : Array of data that will be sent
            Arr Labels (String) : Array of label of the data (the arrangement of the label must be correspond to the arrangement of data)
            StopFLag (Bool)     : Flag to indicate that the data stream already stopped   
        """
        
        if StopFlag == False:

            data_string = ""
            label_idx = 0
            for data in datas:
                data_string += labels[label_idx]
                data_string += f":{data}:"
                label_idx += 1

            print(data_string)
            self.mySocket.send_string(data_string)

            time.sleep(0.03)

        else :
            time.sleep(0.5)
            self.mySocket.send_string("STOP")



