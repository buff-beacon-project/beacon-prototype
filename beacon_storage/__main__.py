import os
import sys, traceback
import sqlite3
import json
from collections import OrderedDict
from datetime import datetime
import zmq
# from beacon_shared import Test
# Test()
# from sqlite3 import Error
DB_SQL_FILE='beacon.db'
DB_TABLE='beacon_records'

class PulseChainException(Exception):
    pass

def assert_next_in_chain(lastPulse, currentPulse):
    # TODO make this check signatures
    if lastPulse == None:
        if currentPulse['chainIndex'] != 1 or currentPulse['pulseIndex'] != 1:
            raise PulseChainException('Expecting first pulse in first chain but received chain {}, pulse {}'.format(currentPulse['chainIndex'], currentPulse['pulseIndex']))
        return
    if lastPulse['chainIndex'] != currentPulse['chainIndex']:
        if currentPulse['pulseIndex'] != 1:
            raise PulseChainException('Received pulse has new chain index but is not first pulse')
    else:
        if currentPulse['pulseIndex'] != lastPulse['pulseIndex'] + 1:
            raise PulseChainException('Received pulse is not next in chain')

    if lastPulse['outputValue'] != currentPulse['previous']:
        raise PulseChainException('Received pulse "previous" value does not match last pulse "outputValue"')

def from_row(row):
    # convert sql row to pulse
    (
        id,
        uri,
        version,
        cypherSuite,
        period,
        certificateId,
        chainIndex,
        pulseIndex,
        timeStamp,
        localRandomValue,

        previousValue,
        hourValue,
        dayValue,
        monthValue,
        yearValue,
        precommitmentValue,
        statusCode,
        signatureValue,
        outputValue
    ) = row
    return OrderedDict([
        ('uri', uri),
        ('version', version),
        ('cypherSuite', cypherSuite),
        ('period', period),
        ('certificateId', certificateId),
        ('chainIndex', chainIndex),
        ('pulseIndex', pulseIndex),
        ('timeStamp', timeStamp),
        ('localRandomValue', localRandomValue),
        # TODO external sources
        # ...
        ('previous', previousValue),
        ('hour', hourValue),
        ('day', dayValue),
        ('month', monthValue),
        ('year', yearValue),
        ('precommitmentValue', precommitmentValue),
        ('statusCode', statusCode),
        ('signatureValue', signatureValue),
        ('outputValue', outputValue)
    ])

def to_row( pulse ):
    return (
        pulse['uri'],
        pulse['version'],
        pulse['cypherSuite'],
        pulse['period'],
        pulse['certificateId'],
        pulse['chainIndex'],
        pulse['pulseIndex'],
        pulse['timeStamp'],
        pulse['localRandomValue'],

        pulse['previousValue'],
        pulse['hour'],
        pulse['day'],
        pulse['month'],
        pulse['year'],
        pulse['precommitmentValue'],
        pulse['statusCode'],
        pulse['signatureValue'],
        pulse['outputValue']
    )

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
        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            c.execute("""
                SELECT * FROM {tableName} ORDER BY timeStamp DESC LIMIT 1
            """.format(
                tableName=DB_TABLE
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
        assert_next_in_chain(self.lastPulse, pulse)
        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            keys = pulse.keys()
            c.execute(
                "INSERT INTO {tableName}({fields}) VALUES ({placeholders})".format(
                    tableName = DB_TABLE,
                    fields = ', '.join(keys),
                    placeholders = ':' + ', :'.join(keys)
                ),
                pulse
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
            pulse = socket.recv_json()
            print("received pulse {pulseIndex}, chain {chainIndex}".format(**pulse))
            print(json.dumps(pulse, sort_keys=True, indent=4))
            store.add_pulse(pulse)
            print("stored successfully")
            socket.send(b'{"ok":true}')
        except Exception as e:
            print(e)
            traceback.print_exc(file=sys.stdout)
            socket.send_json({ "error": { "message": str(e) } })
