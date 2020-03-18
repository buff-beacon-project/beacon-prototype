import traceback
import sys
import falcon
import json
from datetime import datetime
from beacon_shared.pulse import pulse_to_plain_dict
from beacon_shared.store import BeaconStore
from beacon_shared.skiplist import SkipLayers
from beacon_shared.config import SKIP_LIST_LAYER_SIZE, SKIP_LIST_NUM_LAYERS, BEACON_VERSION
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography import x509

class BeaconResource(object):
    def __init__(self):
        self.store = BeaconStore()

class PulseResource(BeaconResource):
    def on_get(self, req, resp, chainId, pulseId):
        # resp.status = falcon.HTTP_200  # This is the default status
        chainId, pulseId = int(chainId), int(pulseId)
        pulse = self.store.fetchPulse(chainId, pulseId)
        if pulse == None:
            raise falcon.HTTPNotFound()
        result = pulse_to_plain_dict(pulse)
        resp.body = json.dumps(result)

    def on_get_by_time(self, req, resp, isotimestr):
        d = None
        try:
            d = datetime.fromisoformat(isotimestr)
        except ValueError as e:
            raise falcon.HTTPBadRequest('Invalid date string. Must be a valid ISO date string.') from e

        pulse = self.store.fetchPulseByGeaterEqualTime(d)
        if pulse == None:
            raise falcon.HTTPNotFound()
        result = pulse_to_plain_dict(pulse)
        resp.body = json.dumps(result)

    def on_get_by_next_time(self, req, resp, isotimestr):
        d = None
        try:
            d = datetime.fromisoformat(isotimestr)
        except ValueError as e:
            raise falcon.HTTPBadRequest('Invalid date string. Must be a valid ISO date string.') from e

        pulse = self.store.fetchNextPulseByTime(d)
        if pulse == None:
            raise falcon.HTTPNotFound()
        result = pulse_to_plain_dict(pulse)
        resp.body = json.dumps(result)

    def on_get_by_previous_time(self, req, resp, isotimestr):
        d = None
        try:
            d = datetime.fromisoformat(isotimestr)
        except ValueError as e:
            raise falcon.HTTPBadRequest('Invalid date string. Must be a valid ISO date string.') from e

        pulse = self.store.fetchPreviousPulseByTime(d)
        if pulse == None:
            raise falcon.HTTPNotFound()
        result = pulse_to_plain_dict(pulse)
        resp.body = json.dumps(result)

    def on_get_last(self, req, resp):
        pulse = self.store.fetchLatestPulse()
        if pulse == None:
            raise falcon.HTTPNotFound()
        result = pulse_to_plain_dict(pulse)
        resp.body = json.dumps(result)


class SkipListResource(BeaconResource):
    def __init__(self):
        super().__init__()
        self.skiplayers = SkipLayers(SKIP_LIST_LAYER_SIZE, SKIP_LIST_NUM_LAYERS)

    def on_get(self, req, resp, chainId, pulseIdFrom, pulseIdTo):
        pulseIds = self.skiplayers.getSkiplistPath(int(pulseIdFrom), int(pulseIdTo))
        if len(pulseIds) == 0:
            resp.body = '[]'
        else:
            pulses = self.store.fetchManyPulses(chainId, pulseIds)
            result = [pulse_to_plain_dict(p) for p in pulses]
            resp.body = json.dumps(result)

    def on_get_by_timestamps(self, req, resp, isotimestr_from, isotimestr_to):
        dfrom = None
        dto = None
        try:
            dfrom = datetime.fromisoformat(isotimestr_from)
            dto = datetime.fromisoformat(isotimestr_to)
        except ValueError as e:
            raise falcon.HTTPBadRequest('Invalid date string. Must be a valid ISO date string.') from e

        pulse_from = self.store.fetchPulseByExactTime(dfrom)
        pulse_to = self.store.fetchPulseByExactTime(dto)

        if pulse_from is None:
            raise falcon.HTTPBadRequest('Could not find "from" pulse')

        if pulse_to is None:
            raise falcon.HTTPBadRequest('Could not find "to" pulse')

        pulseIdFrom = pulse_from["pulseIndex"].get()
        pulseIdTo = pulse_to["pulseIndex"].get()
        chainId = pulse_from["chainIndex"].get()
        if chainId is not pulse_to["chainIndex"].get():
            raise falcon.HTTPBadRequest('Can not generate skiplist. Timestamps span multiple chains.')

        pulseIds = self.skiplayers.getSkiplistPath(int(pulseIdFrom), int(pulseIdTo))
        if len(pulseIds) == 0:
            resp.body = '[]'
        else:
            pulses = self.store.fetchManyPulses(chainId, pulseIds)
            result = [pulse_to_plain_dict(p) for p in pulses]
            resp.body = json.dumps(result)

class CertificateResource(BeaconResource):
    def on_get(self, req, resp, id):
        # resp.status = falcon.HTTP_200  # This is the default status
        pem_data = self.store.fetchCertificateBytes(id)
        if pem_data == None:
            raise falcon.HTTPNotFound()

        cert = x509.load_pem_x509_certificate(pem_data, default_backend())
        resp.body = cert.public_bytes(
            encoding=serialization.Encoding.PEM
        )
        resp.content_type = falcon.MEDIA_TEXT


class ServerStatusResource():
    def on_get(self, req, resp):
        result = {
            "status": {
                "code": 0,
                "message": "OK"
            },
            "version": BEACON_VERSION
        }
        resp.body = json.dumps(result)

# Resources are represented by long-lived class instances
api = falcon.API()

api.add_route('/', ServerStatusResource())

api.add_route('/chain/{chainId}/pulse/{pulseId}', PulseResource())
api.add_route('/pulse/time/{isotimestr}', PulseResource(), suffix='by_time')
api.add_route('/pulse/time/next/{isotimestr}', PulseResource(), suffix='by_next_time')
api.add_route('/pulse/time/previous/{isotimestr}', PulseResource(), suffix='by_previous_time')
api.add_route('/pulse/last', PulseResource(), suffix='last')

api.add_route('/skiplist/chain/{chainId}/{pulseIdFrom}/{pulseIdTo}', SkipListResource())
api.add_route('/skiplist/time/{isotimestr_from}/{isotimestr_to}', SkipListResource(), suffix='by_timestamps')

api.add_route('/certificate/{id}', CertificateResource())

def format_err_json(err):
    return json.dumps({
        "error": {
            "title": err.title,
            "status": err.status,
        }
    })

def json_server_error_response(req, resp, err, params):
    exc_type, exc_value, exc_tb = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_tb)
    resp.body = format_err_json(falcon.HTTPNotFound())

api.add_error_handler(Exception, json_server_error_response)

def json_error_response(req, resp, err, params):
    resp.body = format_err_json(err)

api.add_error_handler(falcon.HTTPError, json_error_response)
