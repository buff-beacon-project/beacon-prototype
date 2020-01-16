from random import getrandbits

from yubihsm import YubiHsm
from yubihsm.defs import CAPABILITY, ALGORITHM
from yubihsm.objects import AsymmetricKey

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes       #for signing
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.asymmetric import padding, ec, rsa, utils   #for signing

from beacon_shared.serialization import serialize_field_value, concat_serialize
from beacon_shared.types import ByteHash

# Utility class for hashing and signing, with or without HSM support
class Hasher:
    def __init__(self, use_hsm = True):
        self.use_hsm = use_hsm
        self.hash_strategy = hashes.SHA512()
        self.signing_hash_strategy = hashes.SHA512()

        self.generate_private_key()
        if self.use_hsm:
            self.init_hsm()

        self.store_public_key()

    def generate_private_key(self):
        self.private_key = rsa.generate_private_key(public_exponent=0x10001, key_size=2048, backend=default_backend())

    def get_public_key(self):
        return self.public_key

    def get_public_key_bytes(self):
        return self.public_key.public_bytes(Encoding.PEM, PublicFormat.PKCS1)

    def get_public_key_id(self):
        return self.public_key_id

    def store_public_key(self):
        self.public_key = self.hsm_asym_key.get_public_key() if self.use_hsm else self.private_key.public_key()
        self.public_key_id = self.hash(ByteHash(self.get_public_key_bytes()))
        # TODO: send message to store public key using public key hash

    # TODO: make this better
    # ref: https://thekernel.com/wp-content/uploads/2018/11/YubiHSM2-EN.pdf
    def init_hsm(self):
        # using the default port
        hsm_port = 12345
        # Return a YubiHsm connected to the backend specified by the URL
        # In this case, the HSM is connected to a connector running on localhost.
        hsm = YubiHsm.connect("http://yubihsm:%s" % hsm_port)
        # Create an authenticated session with the HSM
        self.hsm_session = hsm.create_session_derived(1, 'password')

        #asymkey = AsymmetricKey.generate(session, 0, 'Generate BP R1 Sign', 0xffff, CAPABILITY.SIGN_ECDSA, ALGORITHM.EC_BP256)
        self.hsm_asym_key = AsymmetricKey.put(self.hsm_session, 0, 'RSA pkcs1v15', 0xffff, CAPABILITY.SIGN_PKCS, self.private_key)

    def get_local_random_value(self):
        values = []
        values.append( getrandbits(512).to_bytes(512, byteorder='big', signed=False) )
        values.append( getrandbits(512).to_bytes(512, byteorder='big', signed=False) )
        return self.hash_many(values)

    def hash_many(self, fields):
        hasher = hashes.Hash(self.hash_strategy, default_backend())
        for value in fields:
            hasher.update(serialize_field_value(value))
        return hasher.finalize()

    def hash(self, value):
        hasher = hashes.Hash(self.hash_strategy, default_backend())
        hasher.update(serialize_field_value(value))
        return hasher.finalize()

    def sign_values_hsm(self, values):
        # Line 579-583  The hashing is not repeated inside the illustrated Signing module
        #
        # however, the python yubihsm hashes locally, before sending the
        # value to the HSM, so this is fine... and why we pass unhashed bytes
        data = concat_serialize(values)
        return self.hsm_asym_key.sign_pkcs1v1_5(
            data,
            self.signing_hash_strategy
        )

    # NOT WITH HSM...
    def sign_values_no_hsm(self, values):
        data = concat_serialize(values)
        return self.private_key.sign(
            data,
            padding.PKCS1v15(),
            self.signing_hash_strategy
        )

    def sign_values(self, values):
        if self.use_hsm:
            return self.sign_values_hsm(values)
        else:
            return self.sign_values_no_hsm(values)
