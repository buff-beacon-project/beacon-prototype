from math import log
from functools import reduce

"""
Get the highest layer for which this (pulse) index
is an anchor for.
For example: in base 10, for the following indicies...
1560 => 1
1264 => 0
3000 => 3
3070 => 2
"""
def getHighestLayerPower(layerSize, numLayers, index):
    n = layerSize
    p = numLayers - 1
    if index % n != 0:
        return 0
    pow = 1
    while pow <= p and index % (n ** pow) == 0:
        pow += 1
    return pow - 1


"""
Gives a list of layer indicies in increasing order
that represents the shortest skiplist between two indicies
for a given layer size and number of layers.
"""
def getSkiplistPath(layerSize, numLayers, src, dst):
    n = layerSize
    p = numLayers - 1

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

    path = [curr, dst] if curr != dst else [dst]

    # start at current power, decrement to zero
    for q in range(startq, -1, -1):
        if curr < src:
            break

        pow = n ** q
        while curr - pow > src:
            # decrease by one base power each time and add to list
            curr -= pow
            path.insert(0, curr)

    path.insert(0, src)
    return path

class SkipLayers:
    def __init__(self, layerSize, numLayers):
        self.numLayers = numLayers
        self.layerSize = layerSize
        self.powers = [layerSize ** m for m in range(numLayers - 1, -1, -1)]

    def toLayerIndicies(self, index):
        n = self.layerSize
        mod = index
        result = []
        for power in self.powers:
            result.append(mod // power)
            mod = mod % power
        return result

    def fromLayerIndicies(self, layerIndicies):
        return reduce(
            lambda out, els: out + els[0] * els[1],
            zip(layerIndicies, self.powers),
            0
        )

    def getHighestLayerPower(self, index):
        index = index if type(index) == int else self.fromLayerIndicies(index)
        return getHighestLayerPower(self.layerSize, self.numLayers, index)

    """
    Gives a list of layer indicies in increasing order
    that represents the shortest skiplist between two indicies
    """
    def getSkiplistPath(self, src, dst):
        # convert layer indicies to integers if necessary
        src = src if type(src) == int else self.fromLayerIndicies(src)
        dst = dst if type(dst) == int else self.fromLayerIndicies(dst)

        return getSkiplistPath(self.layerSize, self.numLayers, src, dst)
