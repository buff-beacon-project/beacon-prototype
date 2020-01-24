import os
import json
from beacon_shared.pulse import pulse_from_dict, pulse_to_plain_dict
from beacon_shared.store import BeaconStore
from beacon_shared.zmq_server import ZMQServer

if __name__ == '__main__':
    store = BeaconStore()
    store.initDB()

    def add_pulse(data):
        print("received pulse {pulseIndex}, chain {chainIndex}".format(**data))
        print(json.dumps(data, sort_keys=True, indent=4))
        store.add_pulse(pulse_from_dict(data))

    def get_last_pulse(data):
        return pulse_to_plain_dict(store.fetchLatestPulse())

    server = ZMQServer({
        # commands the server is listening to.
        'add_pulse': add_pulse,
        'get_last_pulse': get_last_pulse
    })

    pub_port = os.getenv('ZMQ_LISTEN_PORT', 5050)
    # listens...
    server.start(pub_port)
