import pyclipper
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.ops import unary_union
from shapely.validation import explain_validity


def _coords(shape):
    """
    Return a list of lists of coordinates of the polygon. The list consists firstly of the list of exterior
    coordinates followed by zero or more lists of any interior coordinates.
    """

    assert shape.geom_type == "Polygon"
    coords = [list(shape.exterior.coords)]
    for interior in shape.interiors:
        coords.append(list(interior.coords))
    return coords


def _drop_degenerate_inners(shape):
    """
    Drop degenerate (zero-size) inners from the polygon.

    This is implemented as dropping anything with a size less than 0.5, as the polygon is in integer coordinates and
    the smallest valid inner would be a triangle with height and width 1.
    """
    assert shape.geom_type == "Polygon"

    new_inners = []
    for inner in shape.interiors:
        # need to make a polygon of the linearring to get the _filled_ area of
        # the closed ring.
        if abs(Polygon(inner).area) >= 0.5:
            new_inners.append(inner)

    return Polygon(shape.exterior, new_inners)


def _contour_to_poly(contour):
    poly = Polygon(contour)
    if not poly.is_valid:
        poly = poly.buffer(0)
    assert poly.is_valid, f"Contour {contour!r} did not make valid polygon {poly.wkt} because {explain_validity(poly)}"
    return poly


def _union_in_blocks(contours, block_size):
    """
    Generator which yields a valid shape for each block_size multiple of input contours. This merges together the
    contours for each block before yielding them.
    """
    n_contours = len(contours)
    for i in range(0, n_contours, block_size):
        j = min(i + block_size, n_contours)

        inners = []
        for c in contours[i:j]:
            p = _contour_to_poly(c)
            if p.geom_type == "Polygon":
                inners.append(p)
            elif p.geom_type == "MultiPolygon":
                inners.extend(p.geoms)
        holes = unary_union(inners)
        assert holes.is_valid

        yield holes


def _generate_polys(contours):
    """
    Generator which yields a valid polygon for each contour input.
    """
    for c in contours:
        p = _contour_to_poly(c)
        yield p


def _polytree_node_to_shapely(node):
    """
    Recurses down a Clipper PolyTree, extracting the results as Shapely objects.

    Returns a tuple of (list of polygons, list of children)
    """
    polygons = []
    children = []
    for ch in node.Childs:
        p, c = _polytree_node_to_shapely(ch)
        polygons.extend(p)
        children.extend(c)

    if node.IsHole:
        # Check expectations: a node should be a hole, _or_ return children. This is because children of holes must
        # be outers, and should be on the polygons list.
        assert len(children) == 0
        children = [node.Contour] if node.Contour else []

    elif node.Contour:
        poly = _contour_to_poly(node.Contour)

        # We add each inner one-by-one so that we can reject them individually if they cause the polygon to become
        # invalid. If the shape has lots of inners, then this can mean a proportional amount of work, and may take
        # 1,000s of seconds. Instead, we can group inners together, which reduces the number of times we call the
        # expensive 'difference' method.
        block_size = 200
        inners = _union_in_blocks(children, block_size) if len(children) > block_size else _generate_polys(children)

        for inner in inners:
            # The difference of two valid polygons may fail, and in this  situation we'd like to be able to display
            # the polygon anyway. So we discard the bad inner and continue.
            #
            # See test_polygon_inners_crossing_outer for a test case.
            try:
                diff = poly.difference(inner)
            except Exception:
                continue

            if not diff.is_valid:
                diff = diff.buffer(0)

            # Keep this for when https://trac.osgeo.org/geos/ticket/789 is resolved.
            #
            # assert diff.is_valid, (
            #     f"Difference of {poly.wkt} and {inner.wkt} did not make valid polygon {diff.wkt} "
            #     f" because {explain_validity(diff)}"
            # )
            # NOTE: this throws away the inner ring if we can't produce a valid difference. Not ideal, but we'd
            # rather produce something that's valid than nothing.
            if diff.is_valid:
                poly = diff

        assert poly.is_valid
        if poly.geom_type == "MultiPolygon":
            polygons.extend(poly.geoms)
        else:
            polygons.append(poly)
        children = []

    else:
        # Check expectations: this branch gets executed if this node is not a hole, and has no contour. In that
        # situation we'd expect that it has no children, as it would not be possible to subtract children from
        # an empty outer contour.
        assert len(children) == 0

    return polygons, children


def _polytree_to_shapely(tree):
    polygons, children = _polytree_node_to_shapely(tree)

    # expect no left over children - should all be incorporated into polygons by the time recursion returns to the root.
    assert len(children) == 0

    union = unary_union(polygons)
    assert union.is_valid
    return union


def make_valid_pyclipper(shape):
    """
    Use the pyclipper library to "union" a polygon on its own. This operation uses the even-odd rule to determine
    which points are in the interior of the polygon, and can reconstruct the orientation of the polygon from that.
    The pyclipper library is robust, and uses integer coordinates, so should not produce any additional degeneracies.

    Before cleaning the polygon, we remove all degenerate inners. This is useful to remove inners which have
    collapsed to points or lines, which can interfere with the cleaning process.
    """

    # drop all degenerate inners
    clean_shape = _drop_degenerate_inners(shape)

    pc = pyclipper.Pyclipper()

    try:
        pc.AddPaths(_coords(clean_shape), pyclipper.PT_SUBJECT, True)

        # note: Execute2 returns the polygon tree, not the list of paths
        result = pc.Execute2(pyclipper.CT_UNION, pyclipper.PFT_EVENODD)

    except pyclipper.ClipperException:
        return MultiPolygon([])

    return _polytree_to_shapely(result)


def make_valid_polygon(shape):
    """
    Make a polygon valid. Polygons can be invalid in many ways, such as self-intersection, self-touching and
    degeneracy. This process attempts to make a polygon valid while retaining as much of its extent or area as possible.

    First, we call pyclipper to robustly union the polygon. Using this on its own appears to be good for "cleaning"
    the polygon.

    This might result in polygons which still have degeneracies according to the OCG standard of validity - as
    pyclipper does not consider these to be invalid. Therefore, we follow by using the `buffer(0)` technique to
    attempt to remove any remaining degeneracies.
    """
    assert shape.geom_type == "Polygon"

    shape = make_valid_pyclipper(shape)
    assert shape.is_valid
    return shape


def make_valid_multipolygon(shape):
    new_g = []

    for g in shape.geoms:
        if g.is_empty:
            continue

        valid_g = make_valid_polygon(g)

        if valid_g.geom_type == "MultiPolygon":
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

    elif shape.geom_type == "MultiPolygon":
        shape = make_valid_multipolygon(shape)

    elif shape.geom_type == "Polygon":
        shape = make_valid_polygon(shape)

    return shape
