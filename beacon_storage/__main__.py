import os
import sys, traceback
import sqlite3
import json
from collections import OrderedDict
from datetime import datetime
import zmq
from beacon_shared.pulse import pulse_from_dict, pulse_to_plain_dict

DB_SQL_FILE = 'beacon.db'
DB_TABLE = 'beacon_records'

PULSE_KEYS = [
    'uri',
    'version',
    'cypherSuite',
    'period',
    'certificateId',
    'chainIndex',
    'pulseIndex',
    'timeStamp',
    'localRandomValue',
    # TODO external sources
    # ...
    'skipListLayerSize',
    'skipListNumLayers',
    'skipListAnchors',
    'precommitmentValue',
    'statusCode',
    'signatureValue',
    'outputValue'
]

class PulseChainException(Exception):
    pass

def assert_next_in_chain(lastPulse, currentPulse):
    # TODO make this check signatures
    if lastPulse is None:
        if currentPulse['chainIndex'].get() != 0 or currentPulse['pulseIndex'].get() != 0:
            raise PulseChainException('Expecting first pulse in first chain but received chain {}, pulse {}'.format(currentPulse['chainIndex'].get(), currentPulse['pulseIndex'].get()))
        return
    if lastPulse['chainIndex'].get() != currentPulse['chainIndex'].get():
        if currentPulse['pulseIndex'].get() != 0:
            raise PulseChainException('Received pulse has new chain index but is not first pulse')
    else:
        if currentPulse['pulseIndex'].get() != lastPulse['pulseIndex'].get() + 1:
            raise PulseChainException('Received pulse is not next in chain')

    if lastPulse['outputValue'].get() != currentPulse['skipListAnchors'].get()[0].get():
        raise PulseChainException('Received pulse previous pulse value does not match current pulse "outputValue"')

# convert sql row to pulse
def from_row(row):
    global PULSE_KEYS
    d = dict( zip(PULSE_KEYS, row) )

    # unserialize the anchors
    d['skipListAnchors'] = d['skipListAnchors'].split(':')

    return pulse_from_dict( d )

def to_row( pulse ):
    global PULSE_KEYS
    get_pulse_val = lambda k: pulse[k].get_json_value()
    ret = list(map(get_pulse_val, PULSE_KEYS))

    n = PULSE_KEYS.index('skipListAnchors')
    # serialize the anchors
    ret[n] = ':'.join(ret[n])

    return tuple(ret)

class BeaconStorage:
    def __init__(self):
        self.initDB()
        self.lastPulse = self.fetchLatestPulse()

    def initDB(self):
        con = None
        try:
            con = self.dbConnection = sqlite3.connect(DB_SQL_FILE)
            c = con.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS {tableName}
                (
                    ID integer PRIMARY KEY AUTOINCREMENT,
                    uri text NOT NULL,
                    version text NOT NULL,
                    cypherSuite text NOT NULL,
                    period integer NOT NULL,
                    certificateId text NOT NULL,
                    chainIndex integer NOT NULL,
                    pulseIndex integer NOT NULL,
                    timeStamp text NOT NULL,
                    localRandomValue text NOT NULL,

                    skipListLayerSize integer NOT NULL,
                    skipListNumLayers integer NOT NULL,
                    skipListAnchors text NOT NULL,
                    precommitmentValue text NOT NULL,
                    statusCode integer NOT NULL,
                    signatureValue text NOT NULL,
                    outputValue text NOT NULL
                )
            """.format(
                tableName=DB_TABLE
            ))
            c.execute('CREATE INDEX IF NOT EXISTS {tableName}_ts ON {tableName} (timeStamp)'.format(tableName=DB_TABLE))
            con.commit()
        except Exception as e:
            if con:
                con.close()
            raise e
        finally:
            c.close()

    def fetchLatestPulse(self):
        global PULSE_KEYS
        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            keys = PULSE_KEYS
            c.execute("""
                SELECT {fields} FROM {tableName} ORDER BY timeStamp DESC LIMIT 1
            """.format(
                tableName = DB_TABLE,
                fields = ', '.join(keys),
            ))
            row = c.fetchone()
            if row == None:
                return None
            return from_row(row)
        except Exception as e:
            raise e
        finally:
            if c:
                c.close()

    def add_pulse(self, pulse):
        global PULSE_KEYS
        assert_next_in_chain(self.lastPulse, pulse)
        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            keys = PULSE_KEYS
            c.execute(
                "INSERT INTO {tableName}({fields}) VALUES ({placeholders})".format(
                    tableName = DB_TABLE,
                    fields = ', '.join(keys),
                    placeholders = ', '.join(['?'] * len(keys))
                ),
                to_row(pulse)
            )
            con.commit()
            self.lastPulse = pulse
        except Exception as e:
            raise e
        finally:
            if c:
                c.close()

def get_zmq_socket(port):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:%s" % port)
    return socket


class ZMQServer:
    def __init__(self, handlers):
        self.handlers = handlers
        self.socket = None

    def start(self, port):
        if self.socket:
            raise Exception('ZMQ server already started')

        self.socket = get_zmq_socket(port)
        # zmq requests come in as { command: '<string>', data: {} }
        while True:
            try:
                request = self.socket.recv_json()
                response = self.handle_request(request)
                self.socket.send_json(response)
            except Exception as e:
                print(e)
                traceback.print_exc(file=sys.stdout)
                self.socket.send_json({ "error": { "message": str(e) } })

    def handle_request(self, req):
        if not 'command' in req:
            raise Exception('Request malformed. Lacking a "command" property.')

        command = req['command']
        if not command in self.handlers:
            raise Exception('Ho handler defined for command "{}"'.format(command))

        handler = self.handlers[command]
        response = handler(req['data'])
        if not response:
            return { "ok": True }
        else:
            return { "ok": True, "data": response }


if __name__ == '__main__':
    store = BeaconStorage()

    def add_pulse(data):
        print("received pulse {pulseIndex}, chain {chainIndex}".format(**data))
        print(json.dumps(data, sort_keys=True, indent=4))
        store.add_pulse(pulse_from_dict(data))

    def get_last_pulse(data):
        return pulse_to_plain_dict(store.lastPulse)

    server = ZMQServer({
        # commands the server is listening to.
        'add_pulse': add_pulse,
        'get_last_pulse': get_last_pulse
    })

    pub_port = os.getenv('ZMQ_LISTEN_PORT', 5050)
    # listens...
    server.start(pub_port)
