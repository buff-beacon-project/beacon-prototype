from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from beacon_shared.serialization import serialize_field_value

DEFAULT_HASH_STRATEGY = hashes.SHA512()

def hash_many(fields, hash_strategy = DEFAULT_HASH_STRATEGY):
    hasher = hashes.Hash(hash_strategy, default_backend())
    for value in fields:
        hasher.update(serialize_field_value(value))
    return hasher.finalize()

def hash(value, hash_strategy = DEFAULT_HASH_STRATEGY):
    hasher = hashes.Hash(hash_strategy, default_backend())
    hasher.update(serialize_field_value(value))
    return hasher.finalize()
