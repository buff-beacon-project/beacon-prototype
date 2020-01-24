import falcon
import json
import sqlite3
from beacon_shared.pulse import pulse_to_plain_dict, pulse_from_dict
from beacon_shared.skiplist import SkipLayers
from beacon_shared.config import SKIP_LIST_LAYER_SIZE, SKIP_LIST_NUM_LAYERS

DB_SQL_FILE = '/db/beacon.db'
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

# convert sql row to pulse
def from_row(row):
    global PULSE_KEYS
    d = dict( zip(PULSE_KEYS, row) )

    # unserialize the anchors
    d['skipListAnchors'] = d['skipListAnchors'].split(':')

    return pulse_from_dict( d )

class BeaconResource(object):
    def __init__(self):
        try:
            con = self.dbConnection = sqlite3.connect(DB_SQL_FILE)
        except Exception as e:
            if con:
                con.close()
            raise e

    def fetchPulse(self, chain, pulse):
        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            keys = PULSE_KEYS
            c.execute("""
                SELECT {fields} FROM {tableName} WHERE chainIndex=? AND pulseIndex=? LIMIT 1
            """.format(
                tableName = DB_TABLE,
                fields = ', '.join(keys),
            ), (chain, pulse))
            row = c.fetchone()
            if row == None:
                return None
            return from_row(row)
        except Exception as e:
            raise e
        finally:
            if c:
                c.close()

    def fetchManyPulses(self, chain, pulseIds):
        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            keys = PULSE_KEYS
            c.execute("""
                SELECT {fields} FROM {tableName} WHERE chainIndex=? AND pulseIndex IN ({seq})
            """.format(
                tableName = DB_TABLE,
                fields = ', '.join(keys),
                seq=','.join(['?'] * len(pulseIds))
            ), (chain,) + tuple(pulseIds))
            rows = c.fetchall()
            return [from_row(row) for row in rows]
        except Exception as e:
            raise e
        finally:
            if c:
                c.close()

class PulseResource(BeaconResource):
    def on_get(self, req, resp, chainId, pulseId):
        # resp.status = falcon.HTTP_200  # This is the default status
        try:
            chainId, pulseId = int(chainId), int(pulseId)
            pulse = self.fetchPulse(chainId, pulseId)
            if pulse == None:
                raise falcon.HTTPNotFound()
            result = pulse_to_plain_dict(pulse)
            resp.body = json.dumps(result)
        except Exception as e:
            print(e)
            raise falcon.HTTPNotFound()

class SkipListResource(BeaconResource):
    def __init__(self):
        super().__init__()
        self.skiplayers = SkipLayers(SKIP_LIST_LAYER_SIZE, SKIP_LIST_NUM_LAYERS)

    def on_get(self, req, resp, chainId, pulseIdFrom, pulseIdTo):
        try:
            pulseIds = self.skiplayers.getSkiplistPath(int(pulseIdFrom), int(pulseIdTo))
            if len(pulseIds) == 0:
                resp.body = '[]'
            else:
                pulses = self.fetchManyPulses(chainId, pulseIds)
                result = [pulse_to_plain_dict(p) for p in pulses]
                resp.body = json.dumps(result)
        except Exception as e:
            print(e)
            raise falcon.HTTPNotFound()

api = falcon.API()

# Resources are represented by long-lived class instances
api.add_route('/chain/{chainId}/pulse/{pulseId}', PulseResource())
api.add_route('/chain/{chainId}/skiplist/{pulseIdFrom}/{pulseIdTo}', SkipListResource())
