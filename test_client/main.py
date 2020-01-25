import urllib.request, json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.exceptions import InvalidSignature
from cryptography import x509
from beacon_shared.pulse import pulse_from_dict, get_pulse_values, pulse_to_plain_dict
import pprint

def fetch(url):
    with urllib.request.urlopen(url) as http:
        return http.read().decode()

def fetch_json(url):
    return json.loads(fetch(url))

def fetchLastPulse():
    dict = fetch_json('http://localhost:8080/pulse/last')
    return pulse_from_dict(dict)


certCache = {}

def fetchCertificate(hashid):
    global certCache
    if hashid in certCache:
        return certCache[hashid]
    data = fetch('http://localhost:8080/certificate/{}'.format(hashid))
    cert = x509.load_pem_x509_certificate(data.encode('utf-8'), default_backend())
    certCache[hashid] = cert
    return cert

def validatePulse(pulse, cert = None):
    if cert == None:
        cert = fetchCertificate(pulse['certificateId'].get_json_value())

    signed_values = get_pulse_values(pulse, 'signatureValue')
    hasher = hashes.Hash(hashes.SHA512(), default_backend())
    for value in signed_values:
        hasher.update(value.serialize())
    digest = hasher.finalize()

    # If the signature does not match, verify() will raise an InvalidSignature exception.
    return cert.public_key().verify(
        pulse['signatureValue'].get(),
        digest,
        padding.PKCS1v15(),
        utils.Prehashed(hashes.SHA512())
    )

def validateSkiplist(src, dest):
    skiplist = fetch_json('http://localhost:8080/chain/0/skiplist/{}/{}'.format(src, dest))
    prev = None

    for dict in skiplist:
        pulse = pulse_from_dict(dict)
        validatePulse(pulse)

        if prev == None:
            prev = pulse
            continue

        anchorValues = [x.get() for x in pulse['skipListAnchors'].get()]
        if prev['outputValue'].get() not in anchorValues:
            raise Exception('Invalid skiplist. No link between pulses {} and {}'.format(prev['pulseIndex'].get(), pulse['pulseIndex'].get()))

        prev = pulse

    return True


if __name__ == '__main__':
    pp = pprint.PrettyPrinter(indent=4)
    pulse = fetchLastPulse()
    cert = fetchCertificate(pulse['certificateId'].get_json_value())
    print('\n*** Latest Pulse ***')
    pp.pprint(pulse_to_plain_dict(pulse))
    print('\n*** Got Cert ***')
    pp.pprint(cert.public_bytes(encoding=serialization.Encoding.PEM))
    print('\n*** Validation ***')
    try:
        validatePulse(pulse, cert)
        print('>>> OK <<<')
    except InvalidSignature as e:
        print('!!!! INVALID PULSE !!!!')


    srcid = 2
    print('\n\n*** Validating skiplist from lastpulse to pulse {} ***'.format(srcid))
    try:
        validateSkiplist(srcid, pulse['pulseIndex'].get())
        print('>>> Valid skiplist <<<')
    except Exception as e:
        print(e)
        print('!!!! INVALID skiplist !!!!')
