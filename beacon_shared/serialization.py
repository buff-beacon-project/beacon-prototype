from datetime import datetime, timedelta
from .types import *

def encode_uint64(n):
    # big endian byte encoding
    # 8 bytes
    return n.to_bytes(8, byteorder='big', signed=False)

def encode_uint32(n):
    # big endian byte encoding
    # 4 bytes
    return n.to_bytes(4, byteorder='big', signed=False)

def encode_bytes(bstr):
    l = len(bstr) # number of bytes
    # return: encode(size, <bytes>) || encode(value, <bytes>)
    return encode_uint64(l) + bstr

def encode_str(str):
    # variable length types will have their byte length prefixed
    return encode_bytes(str.encode('utf-8')) # to byte string

# Ref: 4.1.2 Byte serialization of fields
def serialize_field_value(value):
    if not isinstance(value, BeaconType):
        raise TypeError('Serialization is only defined for types that inherit BeaconType')
    return value.serialize()

# serialize the values and then concatenate them
def concat_serialize(values):
    serialized = map(serialize_field_value, values)
    return b"".join(serialized)
