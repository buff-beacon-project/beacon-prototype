from datetime import datetime
from time import time
from collections import OrderedDict
import status_codes
from config import BEACON_VERSION, CYPHER_SUITE, PERIOD

EMPTY_HASH = '0'*128

def get_pulse_uri(chain_index, pulse_index):
    return "https://{domain}{path}/{version}/chain/{chain_index}/pulse/{pulse_index}".format(
        domain='beacon-prototype.nist.gov',
        path='/api',
        version=BEACON_VERSION,
        chain_index=chain_index,
        pulse_index=pulse_index
    )

def init_pulse(hasher, chain_index, previous_pulse, hour_value, day_value, month_value, year_value):
    # meta information
    pulse_index = 1
    last_time = datetime.today() - PERIOD
    status_code = status_codes.FIRST_PULSE

    if previous_pulse != None:
        pulse_index = previous_pulse['pulseIndex'] + 1
        last_time = previous_pulse['timeStamp']
        status_code = status_codes.OK

    uri = get_pulse_uri(chain_index, pulse_index)
    period_ms = PERIOD.total_seconds() * 1000 # period in ms
    time_stamp = last_time + PERIOD

    # random values
    local_random_value = hasher.get_local_random_value()

    pulse = OrderedDict([
        ('uri', uri),
        ('version', BEACON_VERSION),
        ('cypherSuite', CYPHER_SUITE),
        ('period', period_ms),
        ('certificateId', hasher.get_public_key_id()),
        ('chainIndex', chain_index),
        ('pulseIndex', pulse_index),
        ('timeStamp', time_stamp),
        ('localRandomValue', local_random_value.hex()),
        # TODO external sources
        # ...
        ('previous', None),
        ('hour', hour_value),
        ('day', day_value),
        ('month', month_value),
        ('year', year_value),
        ('precommitmentValue', None),
        ('statusCode', status_code),
        ('signatureValue', None),
        ('outputValue', None)
    ])

    return pulse

def get_pulse_hash(hasher, pulse, until_field = None):
    pulse_values = []
    for key, value in pulse.items():
        if key == until_field:
            break
        pulse_values.append(value)
    return hasher.hash_many(pulse_values)

def finalize_pulse(hasher, pulse, previous_pulse, next_pulse):
    global EMPTY_HASH
    pulse['previous'] = previous_pulse['outputValue'] if previous_pulse != None else EMPTY_HASH
    pulse['precommitmentValue'] = hasher.hash(next_pulse['localRandomValue']).hex()
    # sign the hash of all
    sig_hash = get_pulse_hash(hasher, pulse, 'signatureValue')
    pulse['signatureValue'] = hasher.sign_hash(sig_hash).hex()
    pulse['outputValue'] = get_pulse_hash(hasher, pulse, 'outputValue').hex()
    return pulse
