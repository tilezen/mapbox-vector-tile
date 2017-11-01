#!/usr/bin/env python

import json
import sys

import mapbox_vector_tile

if __name__ == '__main__':
    buffer = sys.stdin.buffer.read()
    layers = mapbox_vector_tile.decode(buffer)
    print(json.dumps(layers))
