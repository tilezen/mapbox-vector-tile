from mapbox_vector_tile import decoder, encoder


def decode(tile, options=None, default_options=None):
    vector_tile = decoder.TileData(pbf_data=tile, options=options, default_options=default_options)
    message = vector_tile.get_message()
    return message


def encode(layers, options=None, default_options=None):
    vector_tile = encoder.VectorTile(default_options=default_options)
    if options is None:
        options = dict()
    if isinstance(layers, list):
        for layer in layers:
            layer_name = layer["name"]
            layer_options = options.get(layer_name, None)
            vector_tile.add_layer(features=layer["features"], name=layer_name, options=layer_options)
    else:
        layer_name = layers["name"]
        layer_options = options.get(layer_name, None)
        vector_tile.add_layer(features=layers["features"], name=layer_name, options=layer_options)

    return vector_tile.tile.SerializeToString()
