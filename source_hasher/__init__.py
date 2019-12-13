import os
import zmq
from .pulse import *
from .hasher import *

def get_zmq_pub_socket(port):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://localhost:%s" % port)
    return socket

class Controller:
    def __init__(self, pub_port, use_hsm):
        pub_port = os.getenv('ZMQ_BROADCAST_PORT')
        use_hsm = os.getenv('USE_HSM')

        self.socket = get_zmq_pub_socket(pub_port)
        self.hasher = hasher.Hasher(use_hsm)

    ####
    # note: https://github.com/zeromq/pyzmq/issues/957
    # subscriber needs:
    #   socket.setsockopt_string(zmq.SUBSCRIBE, topic)
    # The subscriber will have to eat the topic with an extra receive:
    #   topic = socket.recv_string()
    #   data = socket.recv_json()
    def send(self, data):
        topic = "pulse"
        socket = self.socket
        socket.send_string(topic, zmq.SNDMORE)
        socket.send_json(data)


    def start(self):
        chain_index = 1
        previous_pulse = None

        TEST_HASH = self.hasher.hash(1)
        hour_value = TEST_HASH
        day_value = TEST_HASH
        month_value = TEST_HASH
        year_value = TEST_HASH

        while True:
            current_pulse = init_pulse(
                self.hasher,
                chain_index,
                previous_pulse,
                hour_value,
                day_value,
                month_value,
                year_value
            )


if __name__ == '__main__':
    ctrl = Controller()
    ctrl.start()
