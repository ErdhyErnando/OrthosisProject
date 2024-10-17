# lib Folder

This folder contain all library needed to run both orthosis V1 and V2 program. In this documentation, the Author will focus on how to use the function to establish connection and to publish data to the server of the Web App inside orthosis_v1_lib.py and orth, since that was what the Author working on during the writing of this documentation. A modification to this documentation to include all description of the function would be very usefull.

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




