from math import floor
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
    def getSkiplistPath(self, index1, index2):
        # get to layer indicies
        orig = self.toLayerIndicies(index1) if type(index1) == int else index1
        dest = self.toLayerIndicies(index2) if type(index2) == int else index2

        # convert to plain index if needed
        index1 = self.fromLayerIndicies(index1) if type(index1) != int else index1
        index2 = self.fromLayerIndicies(index2) if type(index2) != int else index2

        path = []

        # no path
        if index1 == index2:
            return path

        if index2 < index1:
            #swap
            index2, index1 = index1, index2
            dest, orig = orig, dest

        prev = [0] * self.numLayers # zeros index
        startAt = 0
        fromIndex = 0
        for layer in range(self.numLayers):
            destIndex = dest[layer]
            origIndex = orig[layer]

            prev[layer] = destIndex

            # start at the largest layer down
            if destIndex > 0 and destIndex > origIndex:
                startAt = layer
                fromIndex = destIndex
                break

        print('startAt {}'.format(startAt))

        for layer in range(startAt, self.numLayers):
            print('layer {}'.format(layer))
            destIndex = dest[layer]
            origIndex = orig[layer]

            if destIndex == origIndex:
                prev[layer] = destIndex
                continue

            for idx in range(fromIndex, origIndex, -1):
                prev[layer] = idx
                path.insert(0, prev[:]) # prepend clone

            prev[layer] -= 1
            fromIndex = self.layerSize

        return path
