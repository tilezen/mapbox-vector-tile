from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.geometry.polygon import LinearRing
import pyclipper


def _reverse_ring(shape):
    assert shape.geom_type == 'LinearRing'
    return LinearRing(list(shape.coords)[::-1])


def _reverse_polygon(shape):
    assert shape.geom_type == 'Polygon'

    exterior = _reverse_ring(shape.exterior)
    interiors = [_reverse_ring(r) for r in shape.interiors]

    return Polygon(exterior, interiors)


def _coords(shape):
    assert shape.geom_type == 'Polygon'
    coords = [list(shape.exterior.coords)]
    for interior in shape.interiors:
        coords.append(list(interior.coords))
    return coords


def make_valid_pyclipper(shape):
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
    if shape.is_empty:
        return shape

    elif shape.type == 'MultiPolygon':
        shape = make_valid_multipolygon(shape)

    elif shape.type == 'Polygon':
        shape = make_valid_polygon(shape)

    return shape
