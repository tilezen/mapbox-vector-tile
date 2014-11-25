import tile
import data

# coordindates are scaled to this range within tile
extents = 4096

def decode(tile):
    vector_tile = data.TileData(extents)
    message = vector_tile.getMessage(tile)
    return message

def encode(layers):
    ''' Retrieve a list of GeoJSON tile responses and merge them into one.
    
        get_tiles() retrieves data and performs basic integrity checks.
    '''
    vector_tile = tile.VectorTile(extents)
    if (isinstance(layers, list)):
        for layer in layers:
            vector_tile.addFeatures(layer['features'], layer['name'])
    else:
        vector_tile.addFeatures(layers['features'], layers['name'])

    return vector_tile.tile.SerializeToString()