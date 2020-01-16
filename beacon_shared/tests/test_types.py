import unittest
from ..types import *

class TestPulse(unittest.TestCase):

    def test_datetime(self):
        input = '2019-04-03T13:34:23.234234'
        v = DateTime(input)
        self.assertEqual(
            v.get_json_value(),
            input
        )
        self.assertEqual(
            v.serialize(),
            b'\x00\x00\x00\x00\x00\x00\x00\x1a2019-04-03T13:34:23.234234'
        )

    def test_string(self):
        input = 'test'
        v = String(input)
        self.assertEqual(
            v.get_json_value(),
            input
        )
        self.assertEqual(
            v.serialize()
            , b'\x00\x00\x00\x00\x00\x00\x00\x04test'
        )

    def test_duration(self):
        input = 2000
        v = Duration(input) # ms
        self.assertEqual(
            v.get_json_value(),
            input
        )
        self.assertEqual(
            v.serialize()
            ,  b'\x00\x00\x07\xd0'
        )

    def test_bytes(self):
        input = '4dff4ea340f0a823f15d3f4f01ab62eae0e5da579ccb851f8db9dfe84c58b2b37b89903a740e1ee172da793a6e79d560e5f7f9bd058a12a280433ed6fa46510a'
        v = ByteHash(input)
        self.assertEqual(
            v.get_json_value(),
            input
        )
        self.assertEqual(
            v.serialize()
            , b''.join([(64).to_bytes(8, byteorder='big'), bytes.fromhex(input)])
        )


if __name__ == '__main__':
    unittest.main()
