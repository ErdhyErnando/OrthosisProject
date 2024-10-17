# orthosis_lib Folder

This folder contain all library needed to run both orthosis V1 and V2 program. In this documentation, the Author will focus on how to use the function to establish connection and to publish data to the server of the Web App inside orthosis_v1_lib.py and orthosis_v2_lib_oop.py, since that was what the Author working on during the writing of this documentation. **A modification to this documentation to include all description of the function would be very usefull.**

## orthosis_v1_lib.py

This library is used to run the orthosis V1. It contains all necessary function such as calibrating orthosis, introducing error to the movement, and also move the device. In this documentation, the Author will focus on two functions, namely EstablishZMQPub and ZMQPublish.
- **EstablishZMQPub** <br />
```python
def EstablishZMQPub():
    """
    Function to establish a ZMQ publisher (connection to WebAPP purpose).

    Returns:
        mySocket (SyncSocket): socket object that will be used.
    """
    port = "5001"
    # Creates a socket instance
    context = zmq.Context()
    mySocket = context.socket(zmq.PUB)
    # Binds the socket to a predefined port on localhost
    mySocket.bind(f"tcp://*:{port}")

    return mySocket
```
This function will established a ZMQ connection and return a SyncSocket object which then can be used to publish a data to the server of the web app. The example of the usage can be seen below:

```python
socket = EstablishZMQPub()
```
The working of this will be **explained in detail inside the documentation of the src/students_work/variscia_thesis**

- **ZMQPublish** <br />
```python
def ZMQPublish(datas, labels, stop_flag,mySocket):
    """
    function to publish data from orthosis device to WebApp.

    Parameters:
        Datas (list of float): List of data that will be sent. 
        labels (list of String): Array of label of the data (the arrangement of the label must be correspond to the arrangement of data).
        stop_flag (Bool): Flag to indicate that the data stream already stopped.
        mySocket (SyncSocket): Socket object that wanted to be used.                                                    
    """
    
    if stop_flag == False:

        data_string = ""
        label_idx = 0
        for data in datas :
            data_string += labels[label_idx]
            data_string += f":{data}:"
            label_idx += 1

        print(data_string)
        mySocket.send_string(data_string)

        time.sleep(0.01)

    else :
        time.sleep(0.5)
        mySocket.send_string("STOP")
```
This function will publish the data of the orthosis into the webApp using ZMQ. The parameters and its description of how to use it can be seen in that function. This is the example of the usage taken from the orthosis_error_intro_modified.py inside src/students_work/variscia_thesis/ . **The detail of how this example will be explained on the documentation inside that folder**.
```python
#other lines of code

pubSocket = orthosis_lib.EstablishZMQPub()
myLabels = ["orth_pos","err_pos","flex_ext","distrub_intro","new_trial","is_pressed","err_count"]

#other lines of code

myData = [round(param.orthosis_position,2),round(err_pos,2),flex_ext,round(intro_error,2),new_trial,pressed,param_err.err_count]
orthosis_lib.ZMQPublish(myData,myLabels,myStop_flag,pubSocket)
```
Eventough the users can send data as many as they want with they desired data type, value, and label's name, there are certain data's labels that need to be included with an exact label's name,data type,and range of value. These datas are:

- *flex_ext* <br />
this label and its corresponding value indicate whether the orthosis is on flexion or extension. The data type for this label is **string** and the value will be either **F** for Flexion or **E** for Extension.

- *distrub_intro* <br />
this label and its corresponding value indicate whether there is error introduced during certain movement or not. The data type for this label is **int** and the value will be either **0** which indicate there is no error introduced during that specific time or **100** which shows there is an error.

- *new_trial* <br />
this label and its corresponding value indicate whether the process enter new trial or not. The data type for this label is **int** and the value will be either **0** which indicate the process is still in the old trial or **100** which shows that the process enter new trial. 

- *is_pressed* <br />
This label and its corresponding value indicate whether the button of the Orthosis experiment is pressed or not. The data type for this label is **int** and the value will be either **0** which indicate the button is not pressed or **100** which shows that the button is pressed. 

- *err_count* <br />
This label and its corresponding value show the number of error that already introduced. The data type for this label is **int**.


## orthosis_v2_lib_oop.py
This library is used to run the program of Orthosis V2 that use Object Oriented Programming (orthosis_error_intro_ijcai_oop.py,orthosis_v2.py, and orthosis_v2_modified.py). This file contain necessary classes and their functions such as to run the orthosis, calibrate, introduce error, etc. In this documentation, the Author will only focus on class that is used to publish data of the orthosis to the web App, which is FlaskZMQPub().

- **FlaskZMQPub()** <br />
```python
class FlaskZMQPub():
    def __init__(self):
        """
        This class establish connection between the orthosis device and the web trough ZMQ.                                           
        """
        port = "5001"
        # Creates a socket instance
        context = zmq.Context()
        self.mySocket = context.socket(zmq.PUB)
        # Binds the socket to a predefined port on localhost
        self.mySocket.bind(f"tcp://*:{port}")


    def zmq_publish(self,datas,labels,StopFlag):
        """
        Function to publish data to the JS WebAPP.
        
        Parameters:
            Datas (list of float): List of data that will be sent. 
            Labels (list of String): Array of label of the data (the arrangement of the label must be correspond to the arrangement of data).
            StopFLag (Bool): Flag to indicate that the data stream already stopped.   
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
```
This class is used to send data from the orthosis v2 program to the webApp. It has zmq_publish function that will publish the data to the webApp. The parameters of this function can be seen on the code. This is the example of the usage that is taken from src/ijcai/orthosis_v2_modified.py. The detail of how these lines of code work **will be explained  in the documentation inside src/ijcai/**.
```python
#other lines of code

zmqPub = FlaskZMQPub()
myLabel = ["orth_pos","flex_ext","disturb_intro","new_trial","is_pressed","err_count"]

#other lines of code

myDatas = [orthosis_obj.orthosis_position,flex_ext,disturb,new_trial,pressed,orthosis_obj.err_count]
zmqPub.zmq_publish(myDatas,myLabel,stop_flag)
```
Eventough the users can send data as many as they want with they desired data type, value, and label's name, there are certain data's labels that need to be included with an exact label's name,data type,and range of value. These datas are:

- *flex_ext* <br />
this label and its corresponding value indicate whether the orthosis is on flexion or extension. The data type for this label is **string** and the value will be either **F** for Flexion or **E** for Extension.

- *distrub_intro* <br />
this label and its corresponding value indicate whether there is error introduced during certain movement or not. The data type for this label is **int** and the value will be either **0** which indicate there is no error introduced during that specific time or **100** which shows there is an error.

- *new_trial* <br />
this label and its corresponding value indicate whether the process enter new trial or not. The data type for this label is **int** and the value will be either **0** which indicate the process is still in the old trial or **100** which shows that the process enter new trial. 

- *is_pressed* <br />
This label and its corresponding value indicate whether the button of the Orthosis experiment is pressed or not. The data type for this label is **int** and the value will be either **0** which indicate the button is not pressed or **100** which shows that the button is pressed. 

- *err_count* <br />
This label and its corresponding value show the number of error that already introduced. The data type for this label is **int**.


