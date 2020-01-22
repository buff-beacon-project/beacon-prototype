from math import floor, log
from functools import reduce

class SkipLayers:
    def __init__(self, numLayers, layerSize):
        self.numLayers = numLayers
        self.layerSize = layerSize
        self.powers = [layerSize ** m for m in range(numLayers - 1, -1, -1)]

    def toLayerIndicies(self, index):
        n = self.layerSize
        mod = index
        result = []
        for power in self.powers:
            result.append(floor(mod / power))
            mod = mod % power
        return result

    def fromLayerIndicies(self, layerIndicies):
        return reduce(
            lambda out, els: out + els[0] * els[1],
            zip(layerIndicies, self.powers),
            0
        )

    """
    Gives a list of layer indicies in increasing order
    that represents the shortest skiplist between two indicies
    """
    def getSkiplistPath(self, src, dst):
        n = self.layerSize
        p = self.numLayers - 1

        # convert layer indicies to integers if necessary
        src = src if type(src) == int else self.fromLayerIndicies(src)
        dst = dst if type(dst) == int else self.fromLayerIndicies(dst)

        if src < 0 or dst < 0:
            raise Error('Invalid indicies src: {}, dst: {}'.format(src, dst))

        # no path... they are the same
        if src == dst:
            return []

        if src > dst:
            raise Error('First index is greater than second index')

        # get the highest common base power
        # ex: in base 10... 1483 and 1534 would be 1530
        diff = dst - src # ex: this would be 51
        startq = int(min(log(diff) // log(n), p)) # ex: this would be 1
        curr = (dst // n ** startq) * (n ** startq) # ex: this would be (1534 // 10^1) * 10^1 => 1530

        # start at this value (ex: 1530)
        path = [curr]

        # start at current power, decrement to zero
        for q in range(startq, -1, -1):
            if curr < src:
                break

            pow = n ** q
            while curr - pow > src:
                # decrease by one base power each time and add to list
                curr -= pow
                path.insert(0, curr)

        return path
