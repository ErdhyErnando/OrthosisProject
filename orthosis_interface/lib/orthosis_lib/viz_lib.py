#!/usr/bin/env python3

## This library contains all the methods being used for a pseudo online EMG demonstration ##

# Imports 
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, filtfilt
# Appending the relative path of the root folder
import sys, os
# sys.path.append('../')
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..')))

import param.pseudo_viz_param as param_viz

def loadAndProcessEMGData(): 
    """
    This method is used for loading and preprocessing example EMG-signals and calculate the onsets for a demo

    """

    # Read data 
    #TODO: Move the read data function to the main source file.
    # data = np.loadtxt("../../data/EMG_TIR.txt")
    data = np.loadtxt("/home/experiment/Dokumente/Repos/student_project/OrthosisProject/orthosis_interface/data/EMG_TIR.txt")

    # Get EMG data channels used 
    emg_data = data[:,0:-2]
    samples = data[:,-1]


    # Preprocessing 
    nyq = 0.5 * 500.0 # fsample 500 Hz 
    cutoff_hp = 30.0 / nyq
    b, a = butter(1, cutoff_hp, btype='high', analog=False)
    emg_hp = filtfilt(b, a, emg_data[:,2])

    # Init tkeo operator
    emg_tkeo = np.zeros_like(emg_hp)
    end = len(emg_hp)

    # TKEO formular 
    emg_tkeo[2:end-1] = emg_hp[2:end-1]**2 - emg_hp[1:end-2]*emg_hp[3:end]

    # Abs the values from tkeo 
    emg_abs = abs(emg_tkeo)

    # Lowpassfilter on the data 
    cutoff_lp = 50.0 / nyq
    b, a = butter(1, cutoff_lp, btype='low', analog=False)
    emg_lp = filtfilt(b, a, emg_abs)

    ## Onset Method (tkeo and threshold)
    emg_norm = (emg_lp[2100:] - emg_lp[2100:].min()) / (emg_lp[2100:].max() - emg_lp[2100:].min())

    ## Apply fixed Threshold
    onset_sample = []        
    onset_value = 0.2
    time_limit = 330 
    onset = False
    counter = 0

    for i in range(len(emg_norm)):
        if not onset:
            if emg_norm[i] > onset_value:
                onset = True
                onset_sample.append(i)
                counter = 0
        else:
            if emg_norm[i] <= onset_value:
                counter += 1
            else:
                counter = 0

            if counter >= time_limit:
                onset = False


    # prepare data slice 
    onset_sample = np.array(onset_sample)-param_viz.start_index
    onset_sample_indices = onset_sample > 0 
    onset_sample_shown = onset_sample[onset_sample_indices]

    # Visualization pseudo online 
    emg_pseudo_online = emg_norm[param_viz.start_index:]

    return emg_pseudo_online, onset_sample_shown, onset_value, emg_norm


def updateViz(i, emg_pseudo_online, onset_sample_shown, onset_value, emg_norm, onset_detected):

    plt.cla() # clear the previous image
    plt.plot(emg_pseudo_online[:i*param_viz.tval])
    plt.ylabel("EMG Daten nach TKEO (M. biceps brachii links)")
    plt.hlines(onset_value, 0, len(emg_norm[param_viz.start_index:]), color = 'g')  

    # onset indizes that are already detected in pseudo online case 
    onset_sample_indizes_currently = onset_sample_shown < len(emg_pseudo_online[:i*param_viz.tval])
    onsets_detected_currently = onset_sample_shown[onset_sample_indizes_currently]

    plt.vlines(onsets_detected_currently, 0, 1, colors = 'r') 

    plt.xlim([0, len(emg_pseudo_online)]) # fix the x axis
    plt.ylim(0, 1.4) # fix the y axis
    plt.legend(["Verarbeitetes EMG (TKEO, normiert)", "Schwellenwert", "Bewegungsbeginn"])
    plt.title("Darstellung von EMG-Signalen (verarbeitet) mit Bewegungsgebinn")

    # *** Set some flag when onset detected (how long ?) *** 

    # is current onset lies in the "buffer" of the new plot   
    # at least one onset is detected 
    if (len(onsets_detected_currently) > 0): 
        if(onsets_detected_currently[len(onsets_detected_currently)-1] < i*param_viz.tval and onsets_detected_currently[len(onsets_detected_currently)-1]  > i*param_viz.tval-param_viz.tval):
            onset_detected[0] = True 
        else: 
            pass
    #TODO: we need some feedback from the orthosis when it reads the flag --> is true for 100 ms, is that enough ? 
    #TODO: maybe let it be true until the orthosis sets it back by itself or gives feedback ? 
    #TODO: make the duration of onset_detected either time independent or a longer duration so that the change is detected.


