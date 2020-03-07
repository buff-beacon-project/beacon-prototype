from datetime import datetime, timedelta

from yubihsm import YubiHsm
from yubihsm.defs import CAPABILITY, ALGORITHM
from yubihsm.objects import AsymmetricKey

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.asymmetric import padding, ec, rsa, utils   #for signing

from cryptography import x509
from cryptography.x509.oid import NameOID

from beacon_shared.serialization import concat_serialize
from beacon_shared.types import ByteHash
from beacon_shared.hashing import hash

# Utility class for signing, with or without HSM support
class Signer:
    def __init__(self, use_hsm = True):
        self.use_hsm = use_hsm
        self.signing_hash_strategy = hashes.SHA512()

        self.generate_private_key()
        self.store_certificate()

        if self.use_hsm:
            self.init_hsm()

        self.store_public_key()


    def generate_private_key(self):
        self.private_key = rsa.generate_private_key(public_exponent=0x10001, key_size=2048, backend=default_backend())

    def get_public_key(self):
        return self.public_key

    def get_public_key_bytes(self):
        return self.public_key.public_bytes(Encoding.PEM, PublicFormat.PKCS1)

    def store_public_key(self):
        self.public_key = self.hsm_asym_key.get_public_key() if self.use_hsm else self.private_key.public_key()

    def get_certificate_id(self):
        if self.use_hsm:
            return self.hsm_key_cert_id
        return self.certificate_id

    def get_certificate(self):
        if self.use_hsm:
            return self.hsm_key_cert_bytes
        return self.certificate_bytes

    def store_certificate(self):
        key = self.private_key
        """
        Ref: line 1582

        Base 64 encoded PEM formatted file (X.509 ASN.1
        encoding), following the RFC 5280 [CSF+ 1583 08] specification, containing the certificate(s)
        of the public counter-part of the Beacon signing key used to produce the value in the
        signatureValue field of the pulse. The signing key must always have a corresponding
        certificate, even if it is self-signed. However, it is recommended that certificates be attested
        by some external entity (a certification authority, the Certificate Transparency log, etc.).
        """
        # this is self signed but specs recommend an external signed key
        # TODO: change cert information
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u'US'),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u'Colorado'),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u'Boulder'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'CHANGE ME'),
            x509.NameAttribute(NameOID.COMMON_NAME, u'example.com'),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            # Our certificate will be valid for 10 days
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName(u'localhost')]),
            critical=False,
        ).sign(key, self.signing_hash_strategy, default_backend())

        self.certificate = cert
        self.certificate_bytes = cert.public_bytes(serialization.Encoding.PEM)
        self.certificate_id = hash(ByteHash(self.certificate_bytes))

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

        self.hsm_asym_key = None
        self.hsm_asym_key_self = None

        # print([ x.get_info() for x in self.hsm_session.list_objects() ])

        objs = self.hsm_session.list_objects(object_id=2)
        if len(objs) > 0:
            key = objs[0]
            if key.get_info().label == 'Beacon Generated RSA pkcs1v15':
                self.hsm_asym_key_self = key
            else:
                for key in objs:
                    key.delete()

        if not self.hsm_asym_key_self:
            self.hsm_asym_key_self = AsymmetricKey.put(
                self.hsm_session, 2,
                'Beacon Generated RSA pkcs1v15',
                0xffff,
                CAPABILITY.SIGN_ATTESTATION_CERTIFICATE,
                self.private_key
            )
            self.hsm_asym_key_self.put_certificate(
                'Beacon signing certificate',
                0xffff,
                CAPABILITY.SIGN_PKCS,
                self.certificate
            )

        objs = self.hsm_session.list_objects(object_id=3)
        if len(objs) > 0:
            key = objs[0]
            if key.get_info().label == 'HSM Generated RSA pkcs1v15':
                self.hsm_asym_key = objs[0]
            else:
                for key in objs:
                    key.delete()

        if not self.hsm_asym_key:
            self.hsm_asym_key = AsymmetricKey.generate(
                self.hsm_session, 3,
                'HSM Generated RSA pkcs1v15',
                0xffff,
                CAPABILITY.SIGN_PKCS,
                ALGORITHM.RSA_2048
            )

        self.hsm_key_cert = self.hsm_asym_key.attest(2)
        self.hsm_key_cert_bytes = self.hsm_key_cert.public_bytes(serialization.Encoding.PEM)
        self.hsm_key_cert_id = hash(ByteHash(self.hsm_key_cert_bytes))

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
