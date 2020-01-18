import unittest
from ..skiplist import SkipLayers
import pprint

class TestSkiplist(unittest.TestCase):
    def setUp(self):
        self.skiplayers = SkipLayers(4, 27)

    def testToLayerIndicies(self):
        indicies = self.skiplayers.toLayerIndicies(2)
        self.assertEqual(indicies, [0, 0, 0, 2])

        indicies = self.skiplayers.toLayerIndicies(28)
        self.assertEqual(indicies, [0, 0, 1, 1])

        indicies = self.skiplayers.toLayerIndicies(27 * 28)
        self.assertEqual(indicies, [0, 1, 1, 0])

        indicies = self.skiplayers.toLayerIndicies(2 * 27 ** 4 + 1)
        self.assertEqual(indicies, [54, 0, 0, 1])

    def testFromLayerIndicies(self):
        idx = self.skiplayers.fromLayerIndicies([0, 0, 0, 2])
        self.assertEqual(idx, 2)

        idx = self.skiplayers.fromLayerIndicies([0, 0, 1, 1])
        self.assertEqual(idx, 28)

        idx = self.skiplayers.fromLayerIndicies([0, 1, 1, 0])
        self.assertEqual(idx, 27 * 28)

        idx = self.skiplayers.fromLayerIndicies([54, 0, 0, 1])
        self.assertEqual(idx, 2 * 27 ** 4 + 1)


    def testSkiplist(self):
        skiplist = self.skiplayers.getSkiplistPath([0, 0, 2, 0], [0, 4, 1, 1])
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(skiplist)


if __name__ == '__main__':
    unittest.main()
