import sys

PY3 = sys.version_info[0] == 3

if PY3:
    from .Mapbox import vector_tile_pb2_p3 as vector_tile
    xrange = range
else:
    from .Mapbox import vector_tile_pb2 as vector_tile

cmd_bits = 3

CMD_MOVE_TO = 1
CMD_LINE_TO = 2
CMD_SEG_END = 7

UNKNOWN = 0
POINT = 1
LINESTRING = 2
POLYGON = 3


class TileData:
    """
    """
    def __init__(self):
        self.tile = vector_tile.tile()

    def getMessage(self, pbf_data):
        self.tile.ParseFromString(pbf_data)

        tile = {}
        for layer in self.tile.layers:
            keys = layer.keys
            vals = layer.values

            features = []
            for feature in layer.features:
                tags = feature.tags
                props = {}
                assert len(tags) % 2 == 0, 'Unexpected number of tags'
                for key_idx, val_idx in zip(tags[::2], tags[1::2]):
                    key = keys[key_idx]
                    val = vals[val_idx]
                    value = self.parse_value(val)
                    props[key] = value

                geometry = self.parse_geometry(feature.geometry, feature.type,
                                               layer.extent)
                new_feature = {
                    "geometry": geometry,
                    "properties": props,
                    "id": feature.id,
                    "type": feature.type
                }
                features.append(new_feature)

            tile[layer.name] = {
                "extent": layer.extent,
                "version": layer.version,
                "features": features,
            }
        return tile

    def zero_pad(self, val):
        return '0' + val if val[0] == 'b' else val

    def parse_value(self, val):
        for candidate in ('bool_value',
                          'double_value',
                          'float_value',
                          'int_value',
                          'sint_value',
                          'string_value',
                          'uint_value'):
            if val.HasField(candidate):
                return getattr(val, candidate)
        raise ValueError('%s is an unknown value')

    def zig_zag_decode(self, n):
        return (n >> 1) ^ (-(n & 1))

    def parse_geometry(self, geom, ftype, extent):
        # [9 0 8192 26 0 10 2 0 0 2 15]
        i = 0
        coords = []
        dx = 0
        dy = 0
        parts = []  # for multi linestrings and multi polygons

        while i != len(geom):
            item = bin(geom[i])
            ilen = len(item)
            cmd = int(self.zero_pad(item[(ilen-cmd_bits):ilen]), 2)
            cmd_len = int(self.zero_pad(item[:ilen-cmd_bits]), 2)

            i = i + 1

            def _ensure_polygon_closed(coords):
                if coords and coords[0] != coords[-1]:
                    coords.append(coords[0])

            if cmd == CMD_SEG_END:
                if ftype == POLYGON:
                    _ensure_polygon_closed(coords)
                parts.append(coords)
                coords = []

            elif cmd == CMD_MOVE_TO or cmd == CMD_LINE_TO:

                if coords and cmd == CMD_MOVE_TO:
                    if ftype in (LINESTRING, POLYGON):
                        # multi line string or polygon
                        # our encoder includes CMD_SEG_END to denote
                        # the end of a polygon ring, but this path
                        # would also handle the case where we receive
                        # a move without a previous close on polygons

                        # for polygons, we want to ensure that it is
                        # closed
                        if ftype == POLYGON:
                            _ensure_polygon_closed(coords)
                        parts.append(coords)
                        coords = []

                for point in xrange(0, cmd_len):
                    x = geom[i]
                    i = i + 1

                    y = geom[i]
                    i = i + 1

                    # zipzag decode
                    x = self.zig_zag_decode(x)
                    y = self.zig_zag_decode(y)

                    x = x + dx
                    y = y + dy

                    dx = x
                    dy = y

                    coords.append([x, extent-y])

        if ftype == POINT:
            return coords
        elif ftype in (LINESTRING, POLYGON):
            if parts:
                if coords:
                    parts.append(coords)
                return parts[0] if len(parts) == 1 else parts
            else:
                return coords
        else:
            raise ValueError('Unknown geometry type: %s' % ftype)
