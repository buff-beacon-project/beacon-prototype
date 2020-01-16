import os
import sys, traceback
import sqlite3
import json
from collections import OrderedDict
from datetime import datetime
import zmq
from beacon_shared.pulse import pulse_from_dict

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
    'previous',
    'hour',
    'day',
    'month',
    'year',
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
        if currentPulse['chainIndex'].get() != 1 or currentPulse['pulseIndex'].get() != 1:
            raise PulseChainException('Expecting first pulse in first chain but received chain {}, pulse {}'.format(currentPulse['chainIndex'], currentPulse['pulseIndex']))
        return
    if lastPulse['chainIndex'].get() != currentPulse['chainIndex'].get():
        if currentPulse['pulseIndex'].get() != 1:
            raise PulseChainException('Received pulse has new chain index but is not first pulse')
    else:
        if currentPulse['pulseIndex'].get() != lastPulse['pulseIndex'].get() + 1:
            raise PulseChainException('Received pulse is not next in chain')

    if lastPulse['outputValue'].get() != currentPulse['previous'].get():
        raise PulseChainException('Received pulse "previous" value does not match last pulse "outputValue"')

# convert sql row to pulse
def from_row(row):
    global PULSE_KEYS
    return pulse_from_dict( dict( zip(PULSE_KEYS, row) ) )

def to_row( pulse ):
    global PULSE_KEYS
    get_pulse_val = lambda k: pulse[k].get_json_value()
    return tuple( map(get_pulse_val, PULSE_KEYS) )

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
                    timeStamp real NOT NULL,
                    localRandomValue text NOT NULL,

                    previous text NOT NULL,
                    hour text NOT NULL,
                    day text NOT NULL,
                    month text NOT NULL,
                    year text NOT NULL,
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

if __name__ == '__main__':
    store = BeaconStorage()

    pub_port = os.getenv('ZMQ_LISTEN_PORT', 5050)
    socket = get_zmq_socket(pub_port)

    while True:
        try:
            dict = socket.recv_json()
            print("received pulse {pulseIndex}, chain {chainIndex}".format(**dict))
            print(json.dumps(dict, sort_keys=True, indent=4))

            pulse = pulse_from_dict(dict)
            store.add_pulse(pulse)
            print("stored successfully")
            socket.send(b'{"ok":true}')
        except Exception as e:
            print(e)
            traceback.print_exc(file=sys.stdout)
            socket.send_json({ "error": { "message": str(e) } })
