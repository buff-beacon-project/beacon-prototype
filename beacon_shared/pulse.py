import json
from datetime import datetime
from collections import OrderedDict
from .status_codes import *
from .types import *
from .config import BEACON_VERSION, CYPHER_SUITE, TIMINGS, SKIP_LIST_LAYER_SIZE, SKIP_LIST_NUM_LAYERS
from .skiplist import getHighestLayerPower
from .hashing import hash, hash_many

PERIOD = TIMINGS["period"]

EMPTY_HASH = '0'*128
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
        ('skipListLayerSize', UInt32(fields['skipListLayerSize'])),
        ('skipListNumLayers', UInt32(fields['skipListNumLayers'])),
        ('skipListAnchors', SkipAnchors(fields['skipListAnchors'])),
        ('precommitmentValue', ByteHash(fields['precommitmentValue'])),
        ('statusCode', UInt32(fields['statusCode'])),
        ('signatureValue', ByteHash(fields['signatureValue'])),
        ('outputValue', ByteHash(fields['outputValue']))
    ])

# get values from the pulse, in order, up until specified field
def get_pulse_values(pulse, until_field = None):
    pulse_values = []
    for key, value in pulse.items():
        if key == until_field:
            break
        pulse_values.append(value)
    return pulse_values

def get_pulse_hash(pulse, until_field = None):
    return hash_many(get_pulse_values(pulse, until_field))

def get_skip_list_anchors(previous_pulse):

    if previous_pulse is None:
        return SkipAnchors([EMPTY_HASH] * SKIP_LIST_NUM_LAYERS)

    n = 1 + getHighestLayerPower(
        previous_pulse['skipListLayerSize'].get(),
        previous_pulse['skipListNumLayers'].get(),
        previous_pulse['pulseIndex'].get()
    )

    # first n values are previous pulse's output value
    hashes = [ previous_pulse['outputValue'] ] * n
    # the rest are the existing layer anchors
    hashes += (previous_pulse['skipListAnchors'].get())[n:]
    return SkipAnchors(hashes)

def set_pulse_status(pulse, *statuses):
    code = pulse['statusCode'].get()
    for s in statuses:
        code = code | s
    pulse['statusCode'].set(code)

def init_pulse(hasher, chain_index, previous_pulse):
    global EMPTY_HASH
    # meta information
    # Pulse index starts at zero
    pulse_index = 0
    last_time = datetime.now() - PERIOD
    status_code = STATUS_NO_PRIOR_PRECOMMIT

    if previous_pulse != None:
        if previous_pulse['chainIndex'].get() != chain_index:
            raise Error('Chain index provided does not match previous pulse!')

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
        'certificateId': hasher.get_certificate_id(),
        'chainIndex': chain_index,
        'pulseIndex': pulse_index,
        'timeStamp': time_stamp,
        'localRandomValue': local_random_value,
        # TODO external sources
        # ...
        'skipListLayerSize': SKIP_LIST_LAYER_SIZE,
        'skipListNumLayers': SKIP_LIST_NUM_LAYERS,
        'skipListAnchors': [], # set later
        'precommitmentValue': EMPTY_HASH, # set later
        'statusCode': status_code,
        'signatureValue': EMPTY_HASH, # set later
        'outputValue': EMPTY_HASH # set later
    })

    return pulse

def finalize_pulse(hasher, pulse, previous_pulse, next_pulse):
    pulse['skipListAnchors'] = get_skip_list_anchors(previous_pulse)
    pulse['precommitmentValue'] = ByteHash(hasher.hash(next_pulse['localRandomValue']))
    # sign the hash of all
    values_to_sign = get_pulse_values(pulse, 'signatureValue')
    pulse['signatureValue'] = ByteHash(hasher.sign_values(values_to_sign))
    pulse['outputValue'] = ByteHash(get_pulse_hash(hasher, pulse, 'outputValue'))
    return pulse

def get_pulse_output_value(pulse):
    """
    Get the pulse output value.
    TODO: this should apply recommendation 8.3.1
    """
    return ByteHash(get_pulse_hash(pulse, 'outputValue'))

def assemble_pulse(signer, chain_index, local_random_value, next_local_random_value, previous_pulse):
    """
    Fully assemble a pulse based on the previous pulse, provided random value,
    and the chain index.
    """
    global EMPTY_HASH
    # meta information
    # Pulse index starts at zero
    pulse_index = 0
    last_time = datetime.now() - PERIOD
    status_code = STATUS_NO_PRIOR_PRECOMMIT

    if previous_pulse != None and previous_pulse['chainIndex'].get() == chain_index:
        pulse_index = previous_pulse['pulseIndex'].get() + 1
        last_time = previous_pulse['timeStamp'].get()
        status_code = STATUS_OK
        # otherwise this should be the start of a new chain
    else:
        raise ValueError("Chain index provided does not match previous pulse!")

    time_stamp = last_time + PERIOD

    certId = signer.get_certificate_id()

    pulse = pulse_from_dict({
        'uri': get_pulse_uri(chain_index, pulse_index),
        'version': BEACON_VERSION,
        'cypherSuite': CYPHER_SUITE,
        'period': PERIOD,
        'certificateId': certId,
        'chainIndex': chain_index,
        'pulseIndex': pulse_index,
        'timeStamp': time_stamp,
        'localRandomValue': local_random_value,
        # TODO external sources
        # ...
        'skipListLayerSize': SKIP_LIST_LAYER_SIZE,
        'skipListNumLayers': SKIP_LIST_NUM_LAYERS,
        'skipListAnchors': get_skip_list_anchors(previous_pulse),
        'precommitmentValue': ByteHash(hash(next_local_random_value)),
        'statusCode': status_code,
        'signatureValue': EMPTY_HASH, # set later
        'outputValue': EMPTY_HASH # set later
    })

    if previous_pulse != None and previous_pulse['certificateId'].get() != certId:
        # different cert id, so set status
        set_pulse_status(pulse, STATUS_CERT_ID_CHANGE)

    values_to_sign = get_pulse_values(pulse, 'signatureValue')
    pulse['signatureValue'] = ByteHash(signer.sign_values(values_to_sign))
    pulse['outputValue'] = get_pulse_output_value(pulse)

    return pulse

# helpful for preparing a pulse for transit, or encoding to json
def pulse_to_plain_dict(pulse):
    return { key: value.get_json_value() for key, value in pulse.items() }

class PulseJSONEncoder(json.JSONEncoder):
    def default(self, value):
        if isinstance(value, BeaconType):
            return value.get_json_value()

        return json.JSONEncoder.default(self, value)

def pulse_to_json(pulse, **kwargs):
    return json.dumps(pulse, cls=PulseJSONEncoder, **kwargs)


###############
# Verification
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
