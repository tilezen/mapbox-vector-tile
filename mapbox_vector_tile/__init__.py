from . import encoder
from . import decoder


def decode(tile, y_coord_down=False):
    vector_tile = decoder.TileData()
    message = vector_tile.getMessage(tile, y_coord_down)
    return message


def encode(layers, quantize_bounds=None, y_coord_down=False, extents=4096,
           on_invalid_geometry=None, round_fn=None,
           check_winding_order=True,
           max_geometry_validate_tries=5):
    vector_tile = encoder.VectorTile(
                     extents,
                     on_invalid_geometry,
                     round_fn=round_fn,
                     check_winding_order=check_winding_order,
                     max_geometry_validate_tries=max_geometry_validate_tries)
    if (isinstance(layers, list)):
        for layer in layers:
            vector_tile.addFeatures(layer['features'], layer['name'],
                                    quantize_bounds, y_coord_down)
    else:
        vector_tile.addFeatures(layers['features'], layers['name'],
                                quantize_bounds, y_coord_down)

    return vector_tile.tile.SerializeToString()
