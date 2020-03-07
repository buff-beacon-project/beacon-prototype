from random import getrandbits
from beacon_shared.types import ByteHash
from simple_rsa_rng import SimpleRSARNG
from yubihsm import YubiHsm

def to_byte_hash(n):
    if type(n) is not bytes:
        n = n.to_bytes(512, byteorder='big', signed=False)
    return ByteHash(n)

class RandomnessSources:
    def __init__(self, use_hsm = True):
        self.simpleRSA = SimpleRSARNG(2048, 3)
        self.hsm_session = None

        if use_hsm:
            # using the default port
            hsm_port = 12345
            # Return a YubiHsm connected to the backend specified by the URL
            # In this case, the HSM is connected to a connector running on localhost.
            hsm = YubiHsm.connect("http://yubihsm:%s" % hsm_port)
            # Create an authenticated session with the HSM
            self.hsm_session = hsm.create_session_derived(1, 'password')

    def fetch(self):
        values = []
        values.append( getrandbits(512) )
        values.append( self.simpleRSA.get_rng() )

        if self.hsm_session:
            values.append( self.hsm_session.get_pseudo_random(512) )

        # convert to ByteHash
        return map(
            to_byte_hash,
            values
        )
