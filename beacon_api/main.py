import falcon
import json
from beacon_shared.store import BeaconStore
from beacon_shared.skiplist import SkipLayers
from beacon_shared.config import SKIP_LIST_LAYER_SIZE, SKIP_LIST_NUM_LAYERS

class BeaconResource(object):
    def __init__(self):
        self.store = BeaconStore()

class PulseResource(BeaconResource):
    def on_get(self, req, resp, chainId, pulseId):
        # resp.status = falcon.HTTP_200  # This is the default status
        try:
            chainId, pulseId = int(chainId), int(pulseId)
            pulse = self.store.fetchPulse(chainId, pulseId)
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
                pulses = self.store.fetchManyPulses(chainId, pulseIds)
                result = [pulse_to_plain_dict(p) for p in pulses]
                resp.body = json.dumps(result)
        except Exception as e:
            print(e)
            raise falcon.HTTPNotFound()

api = falcon.API()

# Resources are represented by long-lived class instances
api.add_route('/chain/{chainId}/pulse/{pulseId}', PulseResource())
api.add_route('/chain/{chainId}/skiplist/{pulseIdFrom}/{pulseIdTo}', SkipListResource())
