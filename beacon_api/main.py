import falcon
import json
from datetime import datetime
from beacon_shared.pulse import pulse_to_plain_dict
from beacon_shared.store import BeaconStore
from beacon_shared.skiplist import SkipLayers
from beacon_shared.config import SKIP_LIST_LAYER_SIZE, SKIP_LIST_NUM_LAYERS
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key

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

    def on_get_by_time(self, req, resp, isotimestr):
        d = None
        try:
            d = datetime.fromisoformat(isotimestr)
        except ValueError as e:
            raise falcon.HTTPBadRequest('Invalid date string. Must be a valid ISO date string.') from e
        try:
            pulse = self.store.fetchPulseByGeaterEqualTime(d)
            if pulse == None:
                raise falcon.HTTPNotFound()
            result = pulse_to_plain_dict(pulse)
            resp.body = json.dumps(result)
        except Exception as e:
            print(e)
            raise falcon.HTTPNotFound()

    def on_get_by_next_time(self, req, resp, isotimestr):
        d = None
        try:
            d = datetime.fromisoformat(isotimestr)
        except ValueError as e:
            raise falcon.HTTPBadRequest('Invalid date string. Must be a valid ISO date string.') from e
        try:
            pulse = self.store.fetchNextPulseByTime(d)
            if pulse == None:
                raise falcon.HTTPNotFound()
            result = pulse_to_plain_dict(pulse)
            resp.body = json.dumps(result)
        except Exception as e:
            print(e)
            raise falcon.HTTPNotFound()

    def on_get_by_previous_time(self, req, resp, isotimestr):
        d = None
        try:
            d = datetime.fromisoformat(isotimestr)
        except ValueError as e:
            raise falcon.HTTPBadRequest('Invalid date string. Must be a valid ISO date string.') from e
        try:
            pulse = self.store.fetchPreviousPulseByTime(d)
            if pulse == None:
                raise falcon.HTTPNotFound()
            result = pulse_to_plain_dict(pulse)
            resp.body = json.dumps(result)
        except Exception as e:
            print(e)
            raise falcon.HTTPNotFound()

    def on_get_last(self, req, resp):
        try:
            pulse = self.store.fetchLatestPulse()
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

class CertificateResource(BeaconResource):
    def on_get(self, req, resp, id):
        # resp.status = falcon.HTTP_200  # This is the default status
        try:
            bytehash = self.store.fetchCertificateByteHash(id)
            if bytehash == None:
                raise falcon.HTTPNotFound()

            key = load_pem_public_key(bytehash.get(), backend=default_backend())
            resp.body = key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            resp.content_type = falcon.MEDIA_TEXT
        except Exception as e:
            print(e)
            raise falcon.HTTPNotFound()

# Resources are represented by long-lived class instances
api = falcon.API()
api.add_route('/chain/{chainId}/pulse/{pulseId}', PulseResource())
api.add_route('/pulse/time/{isotimestr}', PulseResource(), suffix='by_time')
api.add_route('/pulse/time/next/{isotimestr}', PulseResource(), suffix='by_next_time')
api.add_route('/pulse/time/previous/{isotimestr}', PulseResource(), suffix='by_previous_time')
api.add_route('/pulse/last', PulseResource(), suffix='last')

api.add_route('/chain/{chainId}/skiplist/{pulseIdFrom}/{pulseIdTo}', SkipListResource())

api.add_route('/certificate/{id}', CertificateResource())
