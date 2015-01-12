import encoder
import decoder

# coordindates are scaled to this range within tile
extents = 4096

def decode(tile):
    vector_tile = decoder.TileData(extents)
    message = vector_tile.getMessage(tile)
    return message

def encode(layers, encode_floats_big_endian=True):
    vector_tile = encoder.VectorTile(
        extents, encode_floats_big_endian=encode_floats_big_endian)
    if (isinstance(layers, list)):
        for layer in layers:
            vector_tile.addFeatures(layer['features'], layer['name'])
    else:
        vector_tile.addFeatures(layers['features'], layers['name'])

    return vector_tile.tile.SerializeToString()
