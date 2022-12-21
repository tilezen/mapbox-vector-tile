from mapbox_vector_tile import decoder, encoder


def decode(tile, y_coord_down=False):
    vector_tile = decoder.TileData()
    message = vector_tile.get_message(tile, y_coord_down)
    return message


def encode(
    layers,
    quantize_bounds=None,
    y_coord_down=False,
    extents=4096,
    on_invalid_geometry=None,
    check_winding_order=True,
):
    vector_tile = encoder.VectorTile(extents, on_invalid_geometry, check_winding_order=check_winding_order)
    if isinstance(layers, list):
        for layer in layers:
            vector_tile.add_features(layer["features"], layer["name"], quantize_bounds, y_coord_down)
    else:
        vector_tile.add_features(layers["features"], layers["name"], quantize_bounds, y_coord_down)

    return vector_tile.tile.SerializeToString()
