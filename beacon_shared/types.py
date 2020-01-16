"""
Types used in a pulse
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

"""
base abstract class
"""
class BeaconType(ABC):
    def __init__(self, value):
        self.set(value)
        super().__init__()

    """
    Default set method
    """
    def set(self, value):
        self.value = value

    """
    Default get method
    """
    def get(self):
        return value

    """
    Get a json-ready value for conversion.
    This should also be a value accepted by the set() method
    """
    def get_json_value(self):
        return self.value

    """
    Get the serialized value for this type (abstract)
    """
    @abstractmethod
    def serialize(self):
        pass

from .serialization import *

"""
Type representing a 32 bit integer
"""
class UInt32(BeaconType):
    def set(self, value):
        self.value = int(value)
    def serialize(self):
        return encode_uint32(self.value)

"""
Type representing a 64 bit integer
"""
class UInt64(BeaconType):
    def set(self, value):
        self.value = int(value)
    def serialize(self):
        return encode_uint64(self.value)

"""
Type representing a character string
"""
class String(BeaconType):
    def serialize(self):
        return encode_str(self.value)

"""
Type representing a datetime
Note: Does not match specs. Length is 16 and does not have "Z"
as terminating value. This is ISO standard.
"""
class DateTime(BeaconType):
    def set(self, value):
        DATETIME_RESOLUTION = timedelta(microseconds=1000)
        if isinstance(value, datetime):
            self.value = value
            return
        if type(value) is int or type(value) is float:
            self.value = datetime.utcfromtimestamp(value)
            return
        if isinstance(value, str):
            self.value = datetime.fromisoformat(value)
            return
        raise TypeError('Can not set beacon DateTime type from value provided')

    def get_json_value(self):
        return self.value.isoformat()

    def serialize(self):
        return encode_str(self.value.isoformat())

"""
Type representing a duration (eg: period)
"""
class Duration(BeaconType):
    def set(self, value):
        if isinstance(value, timedelta):
            self.value = value
            return
        if type(value) is int:
            self.value = timedelta(milliseconds=value)
            return
        raise TypeError('Can not set beacon Duration type from value provided')

    def get_json_value(self):
        return int(self.value.total_seconds() * 1000)

    def serialize(self):
        return encode_uint32(int(self.value.total_seconds() * 1000))

"""
Type representing a bytehash (eg: signature, randOut, ...)
"""
class ByteHash(BeaconType):
    def set(self, value):
        if isinstance(value, str):
            value = bytes.fromhex(value)

        if type(value) is not bytes:
            raise TypeError('Can not set beacon ByteHash type from value provided')

        self.value = value

    def get_json_value(self):
        return self.value.hex()

    def serialize(self):
        return encode_bytes(self.value)
