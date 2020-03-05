from random import getrandbits
from beacon_shared.types import ByteHash

class RandomnessSources:
    def __init__(self):
        pass

    def fetch(self):
        values = []
        values.append( ByteHash(getrandbits(512).to_bytes(512, byteorder='big', signed=False)) )
        values.append( ByteHash(getrandbits(512).to_bytes(512, byteorder='big', signed=False)) )
        return values
