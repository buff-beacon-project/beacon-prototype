import zmq
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes       #for signing
from cryptography.hazmat.primitives.asymmetric import padding, ec, rsa   #for signing

def get_zmq_pub_socket(port):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://localhost:%s" % port)
    return socket

class Hasher:
    def __init__(self, pub_port, use_hsm = True):
        self.outSocket = get_zmq_pub_socket(pub_port)
        self.use_hsm = use_hsm
        self.hash_strategy = hashes.SHA512()
        self.signing_hash_strategy = hashes.SHA512()

        self.generate_private_key()
        if self.use_hsm:
            self.init_hsm()

    def generate_private_key(self):
        self.private_key = rsa.generate_private_key(public_exponent=0x10001, key_size=2048, backend=default_backend())


    # TODO: make this better
    # ref: https://thekernel.com/wp-content/uploads/2018/11/YubiHSM2-EN.pdf
    def init_hsm(self):
        # using the default port
        hsm_port = 12345
        # Return a YubiHsm connected to the backend specified by the URL
        # In this case, the HSM is connected to a connector running on localhost.
        hsm = YubiHsm.connect("http://localhost:%s" % hsm_port)
        # Create an authenticated session with the HSM
        self.hsm_session = hsm.create_session_derived(1, 'password')

        #asymkey = AsymmetricKey.generate(session, 0, 'Generate BP R1 Sign', 0xffff, CAPABILITY.SIGN_ECDSA, ALGORITHM.EC_BP256)
        self.hsm_asym_key = AsymmetricKey.put(self.hsm_session, 0, 'RSA pkcs1v15', 0xffff, CAPABILITY.SIGN_PKCS, self.private_key)

    def fetch_random_values(self):
        # for now just pretend...
        values = []
        values.append( randrange(0, 2 ** 512) )
        values.append( randrange(0, 2 ** 512) )
        return values

    def hash_together(self, values):
        hasher = hashes.Hash(self.hash_strategy, default_backend())
        for val in values:
            hasher.update(str(val).encode('utf8'))
        return hasher.finalize()

    def sign_hash_hsm(self, hash_digest):
        return self.hsm_asym_key.sign_pkcs1v1_5(hash_digest, self.signing_hash_strategy)

    # NOT WITH HSM...
    def sign_hash_no_hsm(self, hash_digest):
        return private_key.sign(
            hash_digest,
            padding.PKCS1v15,
            self.signing_hash_strategy # NOTE: this will hash it (again) as part of the signing. do we want this?
        )

    def sign_hash(self, hash_digest):
        if self.use_hsm:
            return self.sign_hash_hsm(hash_digest)
        else:
            return self.sign_hash_no_hsm(hash_digest)

    def assemble_pulse(self):
        source_values = self.fetch_random_values()
        digest = self.hash_together(source_values)
        digest_signed = self.sign_hash(digest)

        return dict(source_values=source_values, digest=digest, digest_signed=digest_signed)

    ####
    # note: https://github.com/zeromq/pyzmq/issues/957
    # subscriber needs:
    #   socket.setsockopt_string(zmq.SUBSCRIBE, topic)
    # The subscriber will have to eat the topic with an extra receive:
    #   topic = socket.recv_string()
    #   data = socket.recv_json()
    def send_pulse(self, pulse)
        topic = "pulse"
        socket = self.get_zmq_pub_socket
        socket.send_string(topic, zmq.SNDMORE)
        socket.send_json(pulse)
