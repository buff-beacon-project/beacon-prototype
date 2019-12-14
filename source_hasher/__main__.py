import os
import time
from datetime import datetime
import zmq
import pulse
import hasher
from threading import Timer
from config import MAX_TIMEDELTA

class BeaconException(Exception):
    pass

class LatePulseException(BeaconException):
    pass

def get_zmq_pub_socket(port):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)
    return socket

class Controller:
    def __init__(self):
        pub_port = os.getenv('ZMQ_BROADCAST_PORT', 5050)
        use_hsm = os.getenv('USE_HSM', 0) == 1

        self.socket = get_zmq_pub_socket(pub_port)
        self.hasher = hasher.Hasher(use_hsm)

    """
    note: https://github.com/zeromq/pyzmq/issues/957
    subscriber needs:
        socket.setsockopt_string(zmq.SUBSCRIBE, topic)
    The subscriber will have to eat the topic with an extra receive:
        topic = socket.recv_string()
        data = socket.recv_json()
    """
    def send(self, data):
        topic = "pulse"
        socket = self.socket
        socket.send_string(topic, zmq.SNDMORE)
        socket.send_json(data)

    def prepare_next_pulse(self):
        chain_index = 1

        TEST_HASH = self.hasher.hash(1).hex()
        hour_value = TEST_HASH
        day_value = TEST_HASH
        month_value = TEST_HASH
        year_value = TEST_HASH

        self.next_pulse = pulse.init_pulse(
            self.hasher,
            chain_index,
            self.current_pulse,
            hour_value,
            day_value,
            month_value,
            year_value
        )

    def emit_pulse(self):
        self.prepare_next_pulse()
        pulse.finalize_pulse(self.hasher, self.current_pulse, self.next_pulse)
        print('pulse')
        print(self.current_pulse, flush=True)
        # self.send(self.current_pulse)
        self.current_pulse = self.next_pulse
        self.next_pulse = None

    def wait_and_emit_next_pulse(self):
        target = self.current_pulse['timeStamp']
        now = datetime.today()
        if now >= target:
            lateness = now - target
            if lateness >= MAX_TIMEDELTA:
                raise LatePulseException
            else:
                # still ok... emit right away
                self.emit_pulse()
                return
        else:
            delay = target - now
            # wait until timestamp time
            print(delay.total_seconds())
            t = Timer(delay.total_seconds(), self.emit_pulse)
            t.start()
            t.join()


    def start(self):
        chain_index = 1
        self.current_pulse = None
        self.prepare_next_pulse()
        self.current_pulse = self.next_pulse
        self.next_pulse = None

        while True:
            self.wait_and_emit_next_pulse()


if __name__ == '__main__':
    ctrl = Controller()
    ctrl.start()
