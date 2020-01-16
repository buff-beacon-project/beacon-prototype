import unittest
from beacon_shared.pulse import get_pulse_uri

class TestPulse(unittest.TestCase):

    def test_uri(self):
        url = get_pulse_uri(1, 1)
        self.assertEqual('https://beacon-prototype.nist.gov/api/1.0/chain/1/pulse/1', url)

if __name__ == '__main__':
    unittest.main()
