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
            '4dff4ea340f0a823f15d3f4f01ab62eae0e5da579ccb851f8db9dfe84c58b2b37b89903a740e1ee172da793a6e79d560e5f7f9bd058a12a280433ed6fa46510a'
        )

if __name__ == '__main__':
    unittest.main()
