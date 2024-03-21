import zmq
import random
import sys
import time

port = "34761"
host = "192.168.217.112"


context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.connect("tcp://{}:{}".format(host,port))
while True:
    messagedata = random.randrange(1,215) - 80
    socket.send(messagedata)
    time.sleep(1)