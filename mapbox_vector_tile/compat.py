import sys
from builtins import map

PY3 = sys.version_info[0] == 3

if PY3:
    from .Mapbox import vector_tile_pb2_p3
    vector_tile = vector_tile_pb2_p3
else:
    from .Mapbox import vector_tile_pb2
    vector_tile = vector_tile_pb2


def apply_map(fn, x):
    return list(map(fn, x))
