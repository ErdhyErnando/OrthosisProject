import zmq
import random
import sys
import time

port = "34761"
host = "192.168.217.112"

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind(f"tcp://*:{port}")
while True:
    messagedata = str(random.randrange(1, 215) - 80)
    socket.send_string("10: " + messagedata)
    print("Sent: ", messagedata)
    time.sleep