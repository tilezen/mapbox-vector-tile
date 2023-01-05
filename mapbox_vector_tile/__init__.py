from mapbox_vector_tile import decoder, encoder


def decode(tile, y_coord_down=False, transformer=None, geojson=True):
    vector_tile = decoder.TileData(pbf_data=tile, y_coord_down=y_coord_down, transformer=transformer, geojson=geojson)
    message = vector_tile.get_message()
    return message


def encode(
    layers,
    quantize_bounds=None,
    y_coord_down=False,
    extents=4096,
    on_invalid_geometry=None,
    check_winding_order=True,
    transformer=None,
):
    vector_tile = encoder.VectorTile(
        extents=extents,
        on_invalid_geometry=on_invalid_geometry,
        check_winding_order=check_winding_order,
        quantize_bounds=quantize_bounds,
        y_coord_down=y_coord_down,
        transformer=transformer,
    )
    if isinstance(layers, list):
        for layer in layers:
            vector_tile.add_layer(features=layer["features"], name=layer["name"])
    else:
        vector_tile.add_layer(features=layers["features"], name=layers["name"])

    return vector_tile.tile.SerializeToString()
