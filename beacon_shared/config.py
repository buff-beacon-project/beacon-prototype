import os
import datetime

BEACON_VERSION='1.0'
CYPHER_SUITE=0 # '0: SHA512 hashing and RSA signatures with PKCSv1.5 padding'
PERIOD=datetime.timedelta(seconds=10)
# The maximum time the pulse can be late
MAX_TIMEDELTA=datetime.timedelta(seconds=1)
SKIP_LIST_LAYER_SIZE=27
SKIP_LIST_NUM_LAYERS=5
BEACON_DB_PATH=os.getenv('BEACON_DB_PATH', './beacon.db')
BEACON_DB_TABLE = 'beacon_records'

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
