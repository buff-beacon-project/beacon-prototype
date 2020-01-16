import unittest
from hasher import Hasher
from sys import getsizeof

class TestHasher(unittest.TestCase):

    def setUp(self):
        self.hasher = Hasher(False) # no hsm

    def test_hashing(self):
        hash = self.hasher.hash(1)
        self.assertEqual(
            hash.hex(),
            # hash of "1" with SHA512
            'df9c478c05321087b50a1d239b4aab290e9b793252758e706e24312aed21c29072285e436a20c3c6227f99b73638f0414fba5835586fee4e19231c1ec56d58ee'
        )

if __name__ == '__main__':
    unittest.main()
