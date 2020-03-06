from datetime import timedelta

BEACON_VERSION='1.0'
CYPHER_SUITE=0 # '0: SHA512 hashing and RSA signatures with PKCSv1.5 padding'
SKIP_LIST_LAYER_SIZE=27
SKIP_LIST_NUM_LAYERS=5

TIMINGS={
    "period": timedelta(seconds=10),
    "anticipation": timedelta(seconds=1),
    "delay": timedelta(seconds=1),
    "max_local_skew_behind": timedelta(seconds=0.5),
    "max_local_skew_ahead": timedelta(seconds=0.5)
}
