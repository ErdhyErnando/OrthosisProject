import zmq
import SharedArray as sa
from ZMQ_pub import zmq_publisher
import multiprocessing as mp
import time
from ZMQ_pub import FlaskZMQPub




def dummy():
    n_trial = 0
    degree = 0
    ittr_deg = 0
    ittr_pub = 0
    ittr_press = 0
    go_pressed = False
    prev_trial = 0
    stopFlag = False
    err_count = 0
    err_ittr = 0
    new_state = "F"
    current_state = "F"
    labels = ["orth_pos","flex_ext","disturb_intro","new_trial","is_pressed","err_count"]
    error_introduced = False 
    zmqPub = FlaskZMQPub()
    while n_trial < 4:
        if ittr_deg == 10 and current_state == "F":
            degree = degree + 1
            ittr_deg = 0
        elif ittr_deg == 10 and current_state == "E":
            degree = degree-1
            ittr_deg = 0
        else:
            ittr_deg += 1
        
        disturb = None
        if n_trial == 2 and error_introduced == False:
            error_introduced = True
            go_pressed = True
            err_count += 1
        elif n_trial != prev_trial:
            error_introduced = False
            err_ittr = 0

        if error_introduced == True and err_ittr<5:
            disturb = 100
            err_ittr +=1


        new_trial = None
        if n_trial != prev_trial:
            new_trial = 100

        is_pressed = None
        if go_pressed:
            is_pressed = True
            ittr_press += 1


        if ittr_pub == 150 or disturb != None or new_trial != None or is_pressed != None:
            datas = [degree,current_state,disturb,new_trial,is_pressed,err_count]
            zmqPub.zmq_publish(datas,labels,stopFlag)
            ittr_pub = 0

        else:
            ittr_pub += 1


        if degree >= 90 and current_state == "F":
            new_state = "E"

        elif degree <= 0 and current_state =="E":
            new_state = "F"


        prev_trial = n_trial

        if current_state != new_state:
            n_trial += 1

        if ittr_press > 7:
            ittr_press = 0
            go_pressed = False

        current_state = new_state
        time.sleep(0.01)

    zmqPub.zmq_publish(datas,labels,False)




              



if __name__ == "__main__" :

    dummy()

