import datetime

BEACON_VERSION='1.0'
CYPHER_SUITE=0 # '0: SHA512 hashing and RSA signatures with PKCSv1.5 padding'
PERIOD=datetime.timedelta(seconds=10)
# The maximum time the pulse can be late
MAX_TIMEDELTA=datetime.timedelta(seconds=1)
