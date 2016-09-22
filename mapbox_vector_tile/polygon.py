from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.geometry.polygon import LinearRing
import pyclipper


def _reverse_ring(shape):
    """
    Reverse a LinearRing. A counter-clockwise ring given as input would return
    a clockwise ring as output. This should reverse the sign of the ring.
    """

    assert shape.geom_type == 'LinearRing'
    return LinearRing(list(shape.coords)[::-1])


def _reverse_polygon(shape):
    """
    Reverse a Polygon, returning a polygon with the same coordinates in the
    reverse order. This means the returned polygon should have an area equal to
    the negative area of the input polygon.
    """

    assert shape.geom_type == 'Polygon'

    exterior = _reverse_ring(shape.exterior)
    interiors = [_reverse_ring(r) for r in shape.interiors]

    return Polygon(exterior, interiors)


def _coords(shape):
    """
    Return a list of lists of coordinates of the polygon. The list consists
    firstly of the list of exterior coordinates followed by zero or more lists
    of any interior coordinates.
    """

    assert shape.geom_type == 'Polygon'
    coords = [list(shape.exterior.coords)]
    for interior in shape.interiors:
        coords.append(list(interior.coords))
    return coords


def make_valid_pyclipper(shape):
    """
    Use the pyclipper library to union a polygon with its reversed polygon. The
    result should contain all parts of the polygon and be consistently
    oriented. The pyclipper library is robust, and uses integer coordinates, so
    should not produce any additional degeneracies.
    """

    pc = pyclipper.Pyclipper()

    try:
        r_shape = _reverse_polygon(shape)

        pc.AddPaths(_coords(shape), pyclipper.PT_CLIP, True)
        pc.AddPaths(_coords(r_shape), pyclipper.PT_SUBJECT, True)

        result = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_EVENODD,
                            pyclipper.PFT_EVENODD)

    except pyclipper.ClipperException:
        return MultiPolygon([])

    if len(result) == 1:
        shape = Polygon(result[0])
    else:
        shape = MultiPolygon(result)

    return shape


def make_valid_polygon(shape):
    """
    Make a polygon valid. Polygons can be invalid in many ways, such as
    self-intersection, self-touching and degeneracy. This process attempts to
    make a polygon valid while retaining as much of its extent or area as
    possible.

    First, we call pyclipper to robustly union the polygon with its reverse.
    This might result in polygons which still have degeneracies according to
    the OCG standard of validity - as pyclipper does not consider these to be
    invalid. Therefore we follow by using the `buffer(0)` technique to attempt
    to remove any remaining degeneracies.
    """

    assert shape.geom_type == 'Polygon'

    clipped_shape = make_valid_pyclipper(shape)
    new_shape = clipped_shape.buffer(0)

    assert new_shape.is_valid, \
        'buffer(0) did not make geometry valid. old shape: %s' % shape.wkt
    return new_shape


def make_valid_multipolygon(shape):
    new_g = []

    for g in shape.geoms:
        if g.is_empty:
            continue

        valid_g = make_valid_polygon(g)

        if valid_g.type == 'MultiPolygon':
            new_g.extend(valid_g.geoms)
        else:
            new_g.append(valid_g)

    return MultiPolygon(new_g)


def make_it_valid(shape):
    """
    Attempt to make any polygon or multipolygon valid.
    """

    if shape.is_empty:
        return shape

    elif shape.type == 'MultiPolygon':
        shape = make_valid_multipolygon(shape)

    elif shape.type == 'Polygon':
        shape = make_valid_polygon(shape)

    return shape
