#!/usr/bin/python

import cProfile
import sys

from shapely.geometry import mapping
from shapely.wkt import loads as loads_wkt

from mapbox_vector_tile import encode
from mapbox_vector_tile.encoder import on_invalid_geometry_ignore


def make_layers(shapes, geom_dicts=False):
    print("Creating layers with 10 shapes each")
    layers = []
    i = 0
    features = []
    for shape in shapes:
        try:
            geom = loads_wkt(shape.strip())
            if geom_dicts:
                feature = {"geometry": mapping(geom), "properties": {}}
            else:
                feature = {"geometry": geom, "properties": {}}
            features.append(feature)
            if i >= 10:
                layers.append(features)
                features = []
                i = 0
            i += 1
        except Exception:
            pass
    layers.append(features)
    return layers


def run_test(layers):
    print("Running perf test")
    i = 0
    profiler = cProfile.Profile()
    for layer in layers:
        layer_description = {"features": layer, "name": "bar"}
        profiler.enable()
        encode(layer_description, default_options={"on_invalid_geometry": on_invalid_geometry_ignore})
        profiler.disable()
        if i % 100 == 0:
            print(f"{i} tiles produced")
        i += 1

    print("Perf result :")
    profiler.print_stats()


if __name__ == "__main__":
    print("Usage : ")
    print("wget https://gist.githubusercontent.com/lexman/c759d1007e520040cb9f1e41b7af85c2/raw/fgeoms.wkt.zip")
    print("zcat fgeoms.wkt.zip | head -10000 | python bench_encode.py")
    shapes = sys.stdin
    if not shapes.isatty():
        layers = make_layers(shapes, geom_dicts=False)
        run_test(layers)
