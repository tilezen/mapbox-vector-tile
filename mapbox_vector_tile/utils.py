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
