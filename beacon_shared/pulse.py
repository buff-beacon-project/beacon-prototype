import json
from datetime import datetime, timedelta
from time import time
from collections import OrderedDict
from .status_codes import *
from .types import *
from .config import BEACON_VERSION, CYPHER_SUITE, PERIOD

EMPTY_HASH = '0'*128

def get_pulse_uri(chain_index, pulse_index):
    return "https://{domain}{path}/{version}/chain/{chain_index}/pulse/{pulse_index}".format(
        domain='beacon-prototype.nist.gov',
        path='/api',
        version=BEACON_VERSION,
        chain_index=chain_index,
        pulse_index=pulse_index
    )

def pulse_from_dict(fields):
    return OrderedDict([
        ('uri', String(fields['uri'])),
        ('version', String(fields['version'])),
        ('cypherSuite', UInt32(fields['cypherSuite'])),
        ('period', Duration(fields['period'])),
        ('certificateId', ByteHash(fields['certificateId'])),
        ('chainIndex', UInt64(fields['chainIndex'])),
        ('pulseIndex', UInt64(fields['pulseIndex'])),
        ('timeStamp', DateTime(fields['timeStamp'])),
        ('localRandomValue', ByteHash(fields['localRandomValue'])),
        # TODO external sources
        # ...
        ('previous', ByteHash(fields['previous'])),
        ('hour', ByteHash(fields['hour'])),
        ('day', ByteHash(fields['day'])),
        ('month', ByteHash(fields['month'])),
        ('year', ByteHash(fields['year'])),
        ('precommitmentValue', ByteHash(fields['precommitmentValue'])),
        ('statusCode', UInt32(fields['statusCode'])),
        ('signatureValue', ByteHash(fields['signatureValue'])),
        ('outputValue', ByteHash(fields['outputValue']))
    ])

def init_pulse(hasher, chain_index, previous_pulse, hour_value, day_value, month_value, year_value):
    global EMPTY_HASH
    # meta information
    pulse_index = 1
    last_time = datetime.today() - PERIOD
    status_code = STATUS_FIRST_PULSE

    if previous_pulse != None:
        pulse_index = previous_pulse['pulseIndex'].get() + 1
        last_time = previous_pulse['timeStamp'].get()
        status_code = STATUS_OK

    uri = get_pulse_uri(chain_index, pulse_index)
    time_stamp = last_time + PERIOD

    # random values
    local_random_value = hasher.get_local_random_value()

    pulse = pulse_from_dict({
        'uri': uri,
        'version': BEACON_VERSION,
        'cypherSuite': CYPHER_SUITE,
        'period': PERIOD,
        'certificateId': hasher.get_public_key_id(),
        'chainIndex': chain_index,
        'pulseIndex': pulse_index,
        'timeStamp': time_stamp,
        'localRandomValue': local_random_value,
        # TODO external sources
        # ...
        'previous': EMPTY_HASH,
        'hour': hour_value,
        'day': day_value,
        'month': month_value,
        'year': year_value,
        'precommitmentValue': EMPTY_HASH,
        'statusCode': status_code,
        'signatureValue': EMPTY_HASH,
        'outputValue': EMPTY_HASH
    })

    return pulse

# get values from the pulse, in order, up until specified field
def get_pulse_values(pulse, until_field = None):
    pulse_values = []
    for key, value in pulse.items():
        if key == until_field:
            break
        pulse_values.append(value)
    return pulse_values

def get_pulse_hash(hasher, pulse, until_field = None):
    return hasher.hash_many(get_pulse_values(pulse, until_field))

def finalize_pulse(hasher, pulse, previous_pulse, next_pulse):
    global EMPTY_HASH
    pulse['previous'] = previous_pulse['outputValue'] if previous_pulse != None else ByteHash(EMPTY_HASH)
    pulse['precommitmentValue'] = ByteHash(hasher.hash(next_pulse['localRandomValue']))
    # sign the hash of all
    values_to_sign = get_pulse_values(pulse, 'signatureValue')
    pulse['signatureValue'] = ByteHash(hasher.sign_values(values_to_sign))
    pulse['outputValue'] = ByteHash(get_pulse_hash(hasher, pulse, 'outputValue'))
    return pulse

class PulseJSONEncoder(json.JSONEncoder):
    def default(self, value):
        if isinstance(value, BeaconType):
            return value.get_json_value()

        return json.JSONEncoder.default(self, value)

def pulse_to_json(pulse, **kwargs):
    return json.dumps(pulse, cls=PulseJSONEncoder, **kwargs)
