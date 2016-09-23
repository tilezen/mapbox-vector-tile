from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.geometry.polygon import LinearRing
from shapely.ops import cascaded_union
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


def _drop_degenerate_inners(shape):
    """
    Drop degenerate (zero-size) inners from the polygon.

    This is implemented as dropping anything with a size less than 0.5, as the
    polygon is in integer coordinates and the smallest valid inner would be a
    triangle with height and width 1.
    """

    assert shape.geom_type == 'Polygon'

    new_inners = []
    for inner in shape.interiors:
        if abs(inner.area) >= 0.5:
            new_inners.append(inner)

    return Polygon(shape.exterior, new_inners)


def make_valid_pyclipper(shape):
    """
    Use the pyclipper library to "union" a polygon on its own. This operation
    uses the even-odd rule to determine which points are in the interior of
    the polygon, and can reconstruct the orientation of the polygon from that.
    The pyclipper library is robust, and uses integer coordinates, so should
    not produce any additional degeneracies.

    Before cleaning the polygon, we remove all degenerate inners. This is
    useful to remove inners which have collapsed to points or lines, which can
    interfere with the cleaning process.
    """

    # drop all degenerate inners
    clean_shape = _drop_degenerate_inners(shape)

    pc = pyclipper.Pyclipper()

    try:
        pc.AddPaths(_coords(clean_shape), pyclipper.PT_SUBJECT, True)

        result = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_EVENODD)

    except pyclipper.ClipperException:
        return MultiPolygon([])


    if len(result) == 0:
        shape = MultiPolygon([])

    elif len(result) == 1:
        shape = Polygon(result[0])

    else:
        polys = []
        for r in result:
            p = Polygon(r)
            # buffer polygons to remove self-touching outers, which clipper
            # considers valid, but OGC doesn't.
            polys.append(p.buffer(0))

        # use cascaded union in case any of the outers intersect
        shape = cascaded_union(polys)

    return shape


def make_valid_polygon(shape):
    """
    Make a polygon valid. Polygons can be invalid in many ways, such as
    self-intersection, self-touching and degeneracy. This process attempts to
    make a polygon valid while retaining as much of its extent or area as
    possible.

    First, we call pyclipper to robustly union the polygon. Using this on its
    own appears to be good for "cleaning" the polygon.

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
