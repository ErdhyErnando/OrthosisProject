#!/usr/bin/python

# *** imports ****
import itertools
from time import perf_counter
#from datetime import datetime
import os
import eego_sdk
import keyboard
import zmq
import time
import stat
import matplotlib.pyplot as plt
import datetime
import argparse
import serial

#####################################################################################
Baudrate = 115200

ser = serial.Serial('/dev/ttyUSB0', Baudrate)
time.sleep(3)
#####################################################################################

###################################################factory############################
def amplifier_to_id(amplifier):
  return '{}-{:06d}-{}'.format(amplifier.getType(), amplifier.getFirmwareVersion(), amplifier.getSerialNumber())
###############################################################################
def test_impedance(amplifier):
  stream = amplifier.OpenImpedanceStream()

  print('stream:')
  print('  channels.... {}'.format(stream.getChannelList()))
  print('  impedances.. {}'.format(list(stream.getData())))
###############################################################################
def test_eeg(amplifier):
  rates = amplifier.getSamplingRatesAvailable()

  ref_ranges = amplifier.getReferenceRangesAvailable()
  bip_ranges = amplifier.getBipolarRangesAvailable()
  isMeasurementRunning = False


  #start measurement with keyboard event "s"
  print("Type s to start the measurement and e to stop it afterwards")

  while (not isMeasurementRunning): 
    if (keyboard.is_pressed('s')): # start event is "s" on keyboard 
      print("starting measurement")
      isMeasurementRunning = True
	
  #create stream object for getting EMG/EEG data 
  stream = amplifier.OpenEegStream(rates[2], ref_ranges[0], bip_ranges[0])
  time.sleep(0.15) # after that it starts writing data to the buffer 1_60sTestFinalVersion
  ser.write(b's')
  tStart = perf_counter()
  #my_socket.send(topic+codeStart) # send "marker" over tcp connection

  print('stream:')
  print('  channels:   {}'.format(stream.getChannelList()))

  stream_channel_count = len(stream.getChannelList())

  #bufferLength = []
  with open(filename, 'a') as eeg_file:
    # get data for measurementTime seconds, 0.25 seconds in between
    #time inits
 
    t0 = time.perf_counter()
    interval = 0.100
    tnext = t0
    #countBufferReads = 0
    #tHole = 0
    startTime = perf_counter()
    index = 0

    while isMeasurementRunning:

      index = index+1
      tnext = tnext + interval

      while(perf_counter() - startTime < interval*index):
        pass


      try:
        data = stream.getData() # read EMG/EEG data out of buffer

        #stop measurement with "e" on keyboard 
        if(keyboard.is_pressed('e')):
          
          ser.write(b'e')
          tHole = perf_counter()-tStart
          #my_socket.send(topic+codeStop) # send "marker" over tcp connection
          isMeasurementRunning = False
          
          #os.seteuid(1000)
        #bufferLength.append(data.getSampleCount())

        # use only the buffer reads after the first one, first one is unclear to which timepoints the data relates ! 

        print('  [{:04.4f}] buffer, channels: {:03} samples: {:03}'.format(perf_counter() - t0, data.getChannelCount(), data.getSampleCount()))
        

        for s in range(data.getSampleCount()):
          for c in range(data.getChannelCount()):
            eeg_file.write(' %f' % (data.getSample(c, s)))
            #eeg_file.write(' %f' % (data.getSampleCount()))
          eeg_file.write('\n')

        #countBufferReads = countBufferReads+1

      except Exception as e:
        print('error: {}'.format(e))

    for i in range(data.getChannelCount()):
      if(i == 0): 
        eeg_file.write(str(tHole)+" ")
      else: 
        eeg_file.write(str(0)+" ")


    #print("Measurement Time: ", tHole)
    #plt.plot(bufferLength)
    #plt.show()

    #eeg_file.close()

###############################################################################
def test_amplifier(amplifier):
  rates = amplifier.getSamplingRatesAvailable()
  ref_ranges = amplifier.getReferenceRangesAvailable()
  bip_ranges = amplifier.getBipolarRangesAvailable()
  print('amplifier: {}'.format(amplifier_to_id(amplifier)))
  print('  rates....... {}'.format(rates))
  print('  ref ranges.. {}'.format(ref_ranges))
  print('  bip ranges.. {}'.format(bip_ranges))
  print('  channels.... {}'.format(amplifier.getChannelList()))
  
  #
  # test impedance stream
  #
  try:
    test_impedance(amplifier)
  except Exception as e:
    print('stream error: {}'.format(e))

  #
  # test eeg stream
  #
  try:
    test_eeg(amplifier)
  except Exception as e:
    print('stream error: {}'.format(e))
###############################################################################
def test_cascaded(amplifiers):
  n = 2
  while n <= len(amplifiers):
    for l in itertools.permutations(amplifiers):
      selected_amplifiers=[]
      print('cascading permutation:')
      for amplifier in l[:n]:
        selected_amplifiers.append(amplifier)
        print('  amplifier: {}'.format(amplifier_to_id(amplifier)))
      test_amplifier(factory.createCascadedAmplifier(selected_amplifiers))
    n += 1
###############################################################################

# def run_tcp_publisher(port):

#   my_context = zmq.Context()
#   my_socket = my_context.socket(zmq.PUB)
#   my_socket.bind("tcp://*:"+port)
#   print("Publisher ready")
#   return my_socket

###############################################################################

# def readSerial():
#   global isSending
#   global messageIn
#   global messageOut

#    start connection to client to 
#   my_socket = run_tcp_publisher(port)
#   while True:
#     print("isSending:", isSending)
#     time.sleep(0.01)

#     if(isSending == False): 
#       message = my_socket.recv()
#       messageInt = int(message)
#       print("Message received: ", messageInt)
#       messageIn = messageInt
#       isSending = True

    # elif isSending:
    #   #print("message out: ", messageOut)
    #   if(messageOut == 1):
    #     isSending = False # you are sending dont do it again
    #     print("sending")
    #     my_socket.send(codeStartStop) 



###############################################################################

if __name__ == '__main__':
 # os.nice(-20)


  filename = '20230504_AQ59D_orthosisErrorIjcai_multi_' 

  # sub_name = "XYZ" 
  # expt_scenario = "A"
  # expt_seq = "0"
  # expt_suffix = "H"
  # set_num = "1"
  # today = datetime.date.today()
  parser = argparse.ArgumentParser("Custom Error: ")

  # parser.add_argument('-sn','--sub_name', help='Subject Pseudo name')
  # parser.add_argument('-es','--expt_scenario', help='Experiment Scenario')
  # parser.add_argument('-eseq','--expt_seq', help='Experiment Sequence')
  # parser.add_argument('-esuf','--expt_suffix', help='Experiment Suffix')
  # parser.add_argument('-set','--set_num', help='Set number')

  # parser.add_argument('-n','--n_errors', help='No of errors to introduce')
  # parser.add_argument('-d','--duration', help='Duration of error in microseconds')

  parser.add_argument('-s','--set', help='Filename specification')



  args = vars(parser.parse_args())




  if args['set'] is not None:
    filenameInput = args['set']
  # if args['expt_scenario'] is not None:
  #     expt_scenario = args['expt_scenario']
  # if args['expt_seq'] is not None:
  #     expt_seq = args['expt_seq']
  # if args['expt_suffix'] is not None:
  #     expt_suffix = args['expt_suffix']
  # if args['set_num'] is not None:
  #     set_num = args['set_num']
  # if args['n_errors'] is not None:
  #     no_of_error = int(args['n_errors'])
  # if args['duration'] is not None:
  #     error_duration = float(args['duration'])

    filename = filename+filenameInput+'.txt' #expt_data/' + str(today.strftime("%d%m%Y")) +'_' +sub_name+'_'+expt_scenario+'_'+expt_seq+'_'+expt_suffix+'_'+ set_num+'.txt'
    

  #socket settings (TCP connection) 
  # port = "34761"
  # codeStart = b"1" #message to send when EMG starts 
  # codeStop = b"2"
  # topic = b"10" # topic to publish 

  # create tcp socket connection
  #my_socket = run_tcp_publisher(port)

  time.sleep(1)

  # experiment parameters 
  #measurementTime = 10 # in seconds 

  #starting and init 
  factory = eego_sdk.factory()
  v = factory.getVersion()
  print('version: {}.{}.{}.{}'.format(v.major, v.minor, v.micro, v.build))
  print('delaying to allow slow devices to attach...')
  time.sleep(1)

  amplifiers=factory.getAmplifiers()
  cascaded={}
  

  #starting test measurement 
  for amplifier in amplifiers:
    try:
      test_amplifier(amplifier)

      # add to cascaded dictionary
      if amplifier.getType() not in cascaded:
        cascaded[amplifier.getType()]=[]
      cascaded[amplifier.getType()].append(amplifier)
    except Exception as e:
      print('amplifier({}) error: {}'.format(amplifier_to_id(amplifier), e))

  for key in cascaded:
    n=len(cascaded[key])
    print('cascaded({}) has {} amplifiers: {}'.format(key, n, ', '.join(amplifier_to_id(a) for a in cascaded[key])))
    try:
      if n>1 and hasattr(factory, "createCascadedAmplifier"):
        test_cascaded(cascaded[key])
    except Exception as e:
      print('cascading({}) error: {}'.format(key, e))

    

  
