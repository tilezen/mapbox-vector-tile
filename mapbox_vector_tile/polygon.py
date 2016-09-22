from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.geometry.polygon import LinearRing


def reverse_ring(shape):
    assert shape.type == 'LinearRing'
    return LinearRing(list(shape.coords)[::-1])


def reverse_polygon(shape):
    assert shape.type == 'Polygon'

    exterior = reverse_ring(shape.exterior)
    interiors = [reverse_ring(r) for r in shape.interiors]

    return Polygon(exterior, interiors)


def make_valid_polygon_flip(shape):
    assert shape.type == 'Polygon'
    # to handle cases where the area of the polygon is zero, we need to
    # manually reverse the coords in the polygon, then buffer(0) it to make it
    # valid in reverse, then reverse them again to get back to the original,
    # intended orientation.

    flipped = reverse_polygon(shape)
    fixed = flipped.buffer(0)

    if fixed.is_empty:
        return None
    else:
        if fixed.type == 'Polygon':
            return reverse_polygon(fixed)
        elif fixed.type == 'MultiPolygon':
            flipped_geoms = []
            for geom in fixed.geoms:
                reversed_geom = reverse_polygon(geom)
                flipped_geoms.append(reversed_geom)
            return MultiPolygon(flipped_geoms)


def area_bounds(shape):
    if shape.is_empty:
        return 0

    elif shape.type == 'MultiPolygon':
        area = 0
        for geom in shape.geoms:
            area += area_bounds(geom)
        return area

    elif shape.type == 'Polygon':
        minx, miny, maxx, maxy = shape.bounds
        area = (maxx - minx) * (maxy - miny)
        return area

    else:
        assert 'area_bounds: invalid shape type: %s' % shape.type


def make_valid_polygon(shape):
    prev_area = area_bounds(shape)
    new_shape = shape.buffer(0)
    assert new_shape.is_valid, \
        'buffer(0) did not make geometry valid. old shape: %s' % shape.wkt
    new_area = area_bounds(new_shape)

    if new_area < 0.9 * prev_area:
        alt_shape = make_valid_polygon_flip(shape)
        if alt_shape:
            new_shape = new_shape.union(alt_shape)

    return new_shape


def make_valid_multipolygon(shape):
    new_g = []

    for g in shape.geoms:
        if g.is_empty:
            continue

        valid_g = on_invalid_geometry_make_valid(g)

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
