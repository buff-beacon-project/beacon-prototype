import unittest
from ..skiplist import SkipLayers
import pprint

EXPECTED_SKIP_LIST = [
    [0, 0, 2, 7],
    [0, 0, 2, 8],
    [0, 0, 2, 9],
    [0, 0, 2, 10],
    [0, 0, 2, 11],
    [0, 0, 2, 12],
    [0, 0, 2, 13],
    [0, 0, 2, 14],
    [0, 0, 2, 15],
    [0, 0, 2, 16],
    [0, 0, 2, 17],
    [0, 0, 2, 18],
    [0, 0, 2, 19],
    [0, 0, 2, 20],
    [0, 0, 2, 21],
    [0, 0, 2, 22],
    [0, 0, 2, 23],
    [0, 0, 2, 24],
    [0, 0, 2, 25],
    [0, 0, 2, 26],
    [0, 0, 3, 0],
    [0, 0, 4, 0],
    [0, 0, 5, 0],
    [0, 0, 6, 0],
    [0, 0, 7, 0],
    [0, 0, 8, 0],
    [0, 0, 9, 0],
    [0, 0, 10, 0],
    [0, 0, 11, 0],
    [0, 0, 12, 0],
    [0, 0, 13, 0],
    [0, 0, 14, 0],
    [0, 0, 15, 0],
    [0, 0, 16, 0],
    [0, 0, 17, 0],
    [0, 0, 18, 0],
    [0, 0, 19, 0],
    [0, 0, 20, 0],
    [0, 0, 21, 0],
    [0, 0, 22, 0],
    [0, 0, 23, 0],
    [0, 0, 24, 0],
    [0, 0, 25, 0],
    [0, 0, 26, 0],
    [0, 1, 0, 0],
    [0, 2, 0, 0],
    [0, 3, 0, 0],
    [0, 4, 0, 0],
    [0, 5, 0, 0],
    [0, 6, 0, 0],
    [0, 7, 0, 0],
    [0, 8, 0, 0],
    [0, 9, 0, 0],
    [0, 10, 0, 0],
    [0, 11, 0, 0],
    [0, 12, 0, 0],
    [0, 13, 0, 0],
    [0, 14, 0, 0],
    [0, 15, 0, 0],
    [0, 16, 0, 0],
    [0, 17, 0, 0],
    [0, 18, 0, 0],
    [0, 19, 0, 0],
    [0, 20, 0, 0],
    [0, 21, 0, 0],
    [0, 22, 0, 0],
    [0, 23, 0, 0],
    [0, 24, 0, 0],
    [0, 25, 0, 0],
    [0, 26, 0, 0],
    [1, 0, 0, 0],
    [2, 0, 0, 0],
    [3, 0, 0, 0],
    [4, 0, 0, 0],
    [5, 0, 0, 0],
    [6, 0, 0, 0],
    [7, 0, 0, 0],
    [8, 0, 0, 0],
    [9, 0, 0, 0],
    [10, 0, 0, 0],
    [11, 0, 0, 0],
    [12, 0, 0, 0],
    [13, 0, 0, 0],
    [14, 0, 0, 0],
    [15, 0, 0, 0],
    [16, 0, 0, 0],
    [17, 0, 0, 0],
    [18, 0, 0, 0],
    [19, 0, 0, 0],
    [20, 0, 0, 0],
    [21, 0, 0, 0],
    [22, 0, 0, 0],
    [23, 0, 0, 0],
    [24, 0, 0, 0],
    [25, 0, 0, 0],
    [26, 0, 0, 0],
    [27, 0, 0, 0],
    [28, 0, 0, 0],
    [29, 0, 0, 0],
    [30, 0, 0, 0]
]

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
        global EXPECTED_SKIP_LIST
        skiplist = self.skiplayers.getSkiplistPath([0, 0, 2, 6], [30, 4, 2, 1])
        pp = pprint.PrettyPrinter(indent=4)
        skiplist = [self.skiplayers.toLayerIndicies(x) for x in skiplist]
        self.assertEqual(skiplist, EXPECTED_SKIP_LIST)


if __name__ == '__main__':
    unittest.main()
