import os
import time
from datetime import datetime
import zmq
import .beacon_shared.pulse
import hasher
from threading import Timer
from .beacon_shared.config import MAX_TIMEDELTA
from exceptions import LatePulseException, PulseTimeException

def get_zmq_socket(port):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://beacon-storage:%s" % port)
    return socket

class Controller:
    def __init__(self):
        pub_port = os.getenv('ZMQ_BROADCAST_PORT', 5050)
        use_hsm = int(os.getenv('USE_HSM', 0)) == 1

        self.socket = get_zmq_socket(pub_port)
        self.hasher = hasher.Hasher(use_hsm)

    def send(self, data, as_string=False):
        socket = self.socket
        if as_string:
            socket.send_string(data)
        else:
            socket.send_json(data)

        response = socket.recv_json()
        if 'ok' in response and response['ok']:
            return True
        if 'error' in response:
            print(response['error'])
            raise Exception(response['error']['message'])

    def prepare_next_pulse(self):
        chain_index = 1

        TEST_HASH = self.hasher.hash(1)
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
        delta = (self.current_pulse['timeStamp'] - datetime.today()).total_seconds()
        if delta > 0:
            # We need to do this because the Timer object from multi-threading
            # is not exact. It sometimes releases it a bit before the time specified
            time.sleep(delta)

        # TODO: check if i really need this...
        if delta < 0 and abs(delta) > MAX_TIMEDELTA.total_seconds():
            raise LatePulseException

        self.prepare_next_pulse()
        pulse.finalize_pulse(self.hasher, self.current_pulse, self.previous_pulse, self.next_pulse)
        self.send(pulse.pulse_to_json(self.current_pulse), True)
        self.previous_pulse = self.current_pulse
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
        self.previous_pulse = None
        self.current_pulse = None
        self.prepare_next_pulse()
        self.current_pulse = self.next_pulse
        self.next_pulse = None

        while True:
            self.wait_and_emit_next_pulse()


if __name__ == '__main__':
    ctrl = Controller()
    ctrl.start()
