#
# Geometry manipulation
#
# Command size
CMD_BITS = 3

# Commands
CMD_MOVE_TO = 1
CMD_LINE_TO = 2
CMD_SEG_END = 7
CMD_FAKE = 0

# Geometry types
UNKNOWN = 0
POINT = 1
LINESTRING = 2
POLYGON = 3


#
# zig-zag encoder and decoder
#
def zig_zag_encode(n):
    """Return the "zig-zag" encoded unsigned integer corresponding to the signed input integer. This encoding is
    used for MVT geometry deltas."""
    return (n << 1) ^ (n >> 31)


def zig_zag_decode(n):
    """Return the signed integer corresponding to the "zig-zag" encoded unsigned input integer. This encoding is
    used for MVT geometry deltas."""
    return (n >> 1) ^ (-(n & 1))


#
# Options management
#

DEFAULT_ENCODE_OPTIONS = {
    "y_coord_down": False,
    "transformer": None,
    "quantize_bounds": None,
    "extents": 4096,
    "on_invalid_geometry": None,
    "check_winding_order": True,
    "max_geometry_validate_tries": 5,
}

DEFAULT_DECODE_OPTIONS = {"y_coord_down": False, "transformer": None, "geojson": True}


def _get_options(layer_options, default_options, global_default_options, operation_name):
    """Get the entire options dictionary filled using: first, the provided `layer_options`, then the provided
    `default_options` and finally filled using the provided `global_default_options`.

    Args:
        layer_options:
            The options for the current layer.

        default_options:
            The default options of the operation.

        global_default_options:
            The global default options for the operation.

        operation_name:
            The name of the current operation.

    Returns:
        The options to use to operate the layer.
    """
    if default_options is None:
        default_options = global_default_options

    if layer_options is None:
        layer_options = default_options

    result = global_default_options.copy()
    result.update(default_options)
    result.update(layer_options)

    result_keys = set(result.keys())
    expected_keys = set(global_default_options.keys())
    extra_keys = result_keys.difference(expected_keys)
    if extra_keys:
        extra_keys_msg = ", ".join(f"{str(x)!r}" for x in sorted(extra_keys))
        raise ValueError(f"The following options are not allowed for {operation_name} a tile: {extra_keys_msg}.")

    return result


def get_encode_options(layer_options, default_options):
    """Get the entire encoding options dictionary filled using: first, the provided `layer_options`, then the provided
    `default_options` and finally filled using the global default options

    Args:
        layer_options:
            The options for the current layer.

        default_options:
            The default options of the encoding operation.

    Returns:
        The options to use for encoding the layer.
    """
    result = _get_options(
        layer_options=layer_options,
        default_options=default_options,
        global_default_options=DEFAULT_ENCODE_OPTIONS,
        operation_name="encoding",
    )

    # Checks on final values
    extents = result["extents"]
    max_geometry_validate_tries = result["max_geometry_validate_tries"]
    if extents <= 0:
        raise ValueError(f"The extents must be positive. {extents} provided.")
    if max_geometry_validate_tries <= 0:
        raise ValueError(f"The max_geometry_validate_tries must be positive. {max_geometry_validate_tries} provided.")

    return result


def get_decode_options(layer_options, default_options):
    """Get the entire decoding options dictionary filled using: first, the provided `layer_options`, then the provided
    `default_options` and finally filled using the global default options

    Args:
        layer_options:
            The options for the current layer.

        default_options:
            The default options of the decoding operation.

    Returns:
        The options to use for decoding the layer.
    """
    return _get_options(
        layer_options=layer_options,
        default_options=default_options,
        global_default_options=DEFAULT_DECODE_OPTIONS,
        operation_name="decoding",
    )
