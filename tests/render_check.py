"""Pixel ownership for the hex stamp test."""

import collections


def pixel_owners(g, w, h):
    return collections.Counter(g.at(x, y) for x in range(w)
                               for y in range(h))
