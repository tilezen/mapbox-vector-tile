from Mapbox import vector_tile_pb2

cmd_bits = 3

CMD_MOVE_TO = 1
CMD_LINE_TO = 2
CMD_SEG_END = 7

UNKNOWN = 0
POINT   = 1
LINESTRING = 2
POLYGON = 3

class TileData:
    """
    """
    def __init__(self, extents=4096):
        self.tile    = vector_tile_pb2.tile()
        self.extents = extents

    def getMessage(self, pbf_data):
        self.tile.ParseFromString(pbf_data)
        
        features_by_layer = {}
        for layer in self.tile.layers:
            features_for_layer = features_by_layer.setdefault(layer.name, [])
            keys = layer.keys
            vals = layer.values
            for feature in layer.features:
                tags = feature.tags
                props = {}
                assert len(tags) % 2 == 0, 'Unexpected number of tags'
                for key_idx, val_idx in zip(tags[::2], tags[1::2]):
                    key = keys[key_idx]
                    val = vals[val_idx]
                    value = self.parse_value(val)
                    props[key] = value
                
                geometry = self.parse_geometry(feature.geometry, feature.type)
                new_feature = {"geometry": geometry, 
                    "properties": props, 
                    "id": feature.id
                }
                features_for_layer.append(new_feature)
        return features_by_layer

    def parse_value(self, val):
        for candidate in ('bool_value', 'double_value', 'float_value', 'int_value',
                          'sint_value', 'string_value', 'uint_value'):
            if val.HasField(candidate):
                return getattr(val, candidate)
        raise ValueError('%s is an unknown value')

    def zig_zag_decode(self, n):
        return (n >> 1) ^ (-(n & 1))

    def parse_geometry(self, geom, ftype):
        # [9 0 8192 26 0 10 2 0 0 2 15]
        i = 0
        coords = []
        dx = 0
        dy = 0

        while(i!=len(geom)):
            item = bin(geom[i])
            ilen = len(item)
            cmd  = int(item[(ilen-cmd_bits):ilen], 2)
            cmd_len = int(item[:ilen-cmd_bits], 2)

            i = i + 1

            if cmd == CMD_SEG_END:
                break;

            if (cmd == CMD_MOVE_TO or cmd == CMD_LINE_TO):
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

                    coords.append([x,4096-y])
        
        if ftype == POLYGON and len(coords) > 0:
            coords.append(coords[0])
        return coords


