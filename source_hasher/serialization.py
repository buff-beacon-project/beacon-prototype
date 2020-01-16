import numpy as np
from datetime import datetime, timedelta

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
    # dateStr
    if isinstance(value, datetime):
        return encode_str(value.isoformat())
    # string
    if isinstance(value, str):
        return encode_str(value)
    # uint64
    if isinstance(value, np.uint64):
        return encode_uint64(int(value))
    # uint32
    if isinstance(value, np.uint32):
        return encode_uint32(int(value))
    # duration... for period
    if isinstance(value, timedelta):
        return encode_uint32(int(value.total_seconds() * 1000))

    t = type(value)
    # builtin int type
    if t is int:
        return encode_uint64(value)

    # for hashes
    if t is bytes:
        return encode_bytes(value)

    raise TypeError('Serialize is not implemented for type {}'.format(t))

# serialize the values and then concatenate them
def concat_serialize(values):
    serialized = map(serialize_field_value, values)
    return b"".join(serialized)
