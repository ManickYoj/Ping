"""
util.py
-------
Includes utility functions for working with
vectors.
"""

import math


def distance(point1, point2):
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** .5


def magnitude(self, vec):
        return (vec[0] ** 2 + vec[1] ** 2) ** .5


def vectorAdd(vec1, vec2):
    if not len(vec1) == len(vec2):
        raise ValueError("Tried to add two vectors of unequal length.")

    return tuple(vec1[i] + vec2[i] for i in range(len(vec1)))


def vectorSub(vec1, vec2):
    if not len(vec1) == len(vec2):
        raise ValueError("Tried to add two vectors of unequal length.")

    return tuple(vec1[i] - vec2[i] for i in range(len(vec1)))


def vectorMul(vec, scalar):
    return tuple(x * scalar for x in vec)


def inBounds(value, bounds, min_bound=0):
    if not isinstance(bounds, list) and not isinstance(value, list):
        return value < bounds and min_bound < value
    elif not len(value) == len(bounds):
        raise ValueError("Tried to compare values and bounds of unequal lengths.")
    else:
        return bool([x for x in range(len(value)) if value[x] > bounds[x]] and min_bound < value[x])


def calcVel(speed, heading):
    heading = math.radians(heading+90)
    return speed * math.cos(heading), speed * math.sin(heading)
