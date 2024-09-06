#!/usr/bin/env python3
import zmq
import SharedArray as sa
import time


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

            time.sleep(0.01)

        else :
            time.sleep(0.5)
            self.mySocket.send_string("STOP")



