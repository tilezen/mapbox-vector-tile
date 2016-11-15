#!/usr/bin/python
# -*- coding: utf-8 -*-

import cProfile
from itertools import islice
from mapbox_vector_tile.encoder import VectorTile, on_invalid_geometry_ignore
from mapbox_vector_tile import encode
from shapely.wkt import loads as loads_wkt
import sys


def make_layers(shapes):
    print ("Creating layers with 10 shapes each")
    layers = []
    i = 0
    features = []
    for shape in shapes:
        try:
            geom = loads_wkt(shape.strip())
            feature = {"geometry": geom, "properties": {}}
            features.append(feature)
            if i >= 10:
                layers.append(features)
                features = []
                i = 0
            i += 1
        except:
            pass
    return layers

def run_test(layers):
    print ("Running perf test")
    i = 0
    profiler = cProfile.Profile()
    for layer in layers:
        layer_description = {
            'features' : layer,
            'name': 'bar'
        }
        profiler.enable()
        res = encode(layer_description, on_invalid_geometry=on_invalid_geometry_ignore, round_fn=round)
        profiler.disable()
        if i % 100 == 0:
            print "{} tiles produced".format(i)
        i += 1

    print ("Perf result :")
    profiler.print_stats()


if __name__ == '__main__':
    print "Usage : zcat fgeoms.wkt.zip | head -10000 | python bench_encode.py"
    shapes = sys.stdin
    layers = make_layers(shapes)
    run_test(layers)
