from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.ops import cascaded_union
from shapely.validation import explain_validity
import pyclipper


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
        # need to make a polygon of the linearring to get the _filled_ area of
        # the closed ring.
        if abs(Polygon(inner).area) >= 0.5:
            new_inners.append(inner)

    return Polygon(shape.exterior, new_inners)


def _contour_to_poly(contour, asserted):
    poly = Polygon(contour)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if asserted:
        assert poly.is_valid, \
            "Contour %r did not make valid polygon %s because %s" \
            % (contour, poly.wkt, explain_validity(poly))
    return poly


def _polytree_node_to_shapely(node, asserted):
    """
    Recurses down a Clipper PolyTree, extracting the results as Shapely
    objects.

    Returns a tuple of (list of polygons, list of children)
    """

    polygons = []
    children = []
    for ch in node.Childs:
        p, c = _polytree_node_to_shapely(ch, asserted)
        polygons.extend(p)
        children.extend(c)

    if node.IsHole:
        # check expectations: a node should be a hole, _or_ return children.
        # this is because children of holes must be outers, and should be on
        # the polygons list.
        assert len(children) == 0
        if node.Contour:
            children = [node.Contour]
        else:
            children = []

    elif node.Contour:
        poly = _contour_to_poly(node.Contour, asserted)
        for ch in children:
            inner = _contour_to_poly(ch, asserted)
            diff = poly.difference(inner)
            if not diff.is_valid:
                diff = diff.buffer(0)

            # keep this for when https://trac.osgeo.org/geos/ticket/789 is
            # resolved.
            #
            #  assert diff.is_valid, \
            #      "Difference of %s and %s did not make valid polygon %s " \
            #      " because %s" \
            #      % (poly.wkt, inner.wkt, diff.wkt, explain_validity(diff))
            #
            # NOTE: this throws away the inner ring if we can't produce a
            # valid difference. not ideal, but we'd rather produce something
            # that's valid than nothing.
            if diff.is_valid:
                poly = diff

        if asserted:
            assert poly.is_valid
        if poly.type == 'MultiPolygon':
            polygons.extend(poly.geoms)
        else:
            polygons.append(poly)
        children = []

    else:
        # check expectations: this branch gets executed if this node is not a
        # hole, and has no contour. in that situation we'd expect that it has
        # no children, as it would not be possible to subtract children from
        # an empty outer contour.
        assert len(children) == 0

    return (polygons, children)


def _polytree_to_shapely(tree, asserted):
    polygons, children = _polytree_node_to_shapely(tree, asserted)

    # expect no left over children - should all be incorporated into polygons
    # by the time recursion returns to the root.
    assert len(children) == 0

    union = cascaded_union(polygons)
    if asserted:
        assert union.is_valid
    return union


def make_valid_pyclipper(shape, asserted):
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

        # note: Execute2 returns the polygon tree, not the list of paths
        result = pc.Execute2(pyclipper.CT_UNION, pyclipper.PFT_EVENODD)

    except pyclipper.ClipperException:
        return MultiPolygon([])

    return _polytree_to_shapely(result, asserted)


def make_valid_polygon(shape, asserted):
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

    shape = make_valid_pyclipper(shape, asserted)
<<<<<<< HEAD
    if asserted: 
=======
    if asserted:
>>>>>>> on_invalid_geometry_make_valid_and_clean
        assert shape.is_valid
    return shape


def make_valid_multipolygon(shape, asserted):
    new_g = []

    for g in shape.geoms:
        if g.is_empty:
            continue

        valid_g = make_valid_polygon(g, asserted)

        if valid_g.type == 'MultiPolygon':
            new_g.extend(valid_g.geoms)
        else:
            new_g.append(valid_g)

    return MultiPolygon(new_g)


def make_it_valid(shape, asserted=True):
    """
    Attempt to make any polygon or multipolygon valid.
    """
    
    if shape.is_empty:
        return shape

    elif shape.type == 'MultiPolygon':
        shape = make_valid_multipolygon(shape, asserted)

    elif shape.type == 'Polygon':
        shape = make_valid_polygon(shape, asserted)

    return shape


<<<<<<< HEAD
def split_multi(shape):
    """
    Separate multipolygon into 1 polygon per row
    """
    polygons = []
    pnum = 1 # polygon number
    for p in shape:
        polygons.append( (p, pnum) )
        pnum += 1
    return polygons 


def split_line(polygons):
    """
    Break each polygon into linestrings
    """
    linestrings = []
    for p, pnum in polygons:
        lnum = 0 # line number
        boundary = p.boundary
        if boundary.type == 'LineString':
            linestrings.append( (boundary, pnum, lnum) )
        else:
            for ls in boundary:
                linestrings.append( (ls, pnum, lnum) )
                lnum += 1
    return linestrings


def line_exterior(linestrings):
    """
    Get the linestrings that make up the exterior of each 
    """
    exterior_lines = []
    for l, pnum, lnum in linestrings:
        if lnum == 0: 
           exterior_lines.append( (l, pnum) )
    return exterior_lines


def line_interior(linestrings):
    """
    Get an array of all the linestrings that make up the
    interior of each polygon
    """
    interior_lines = []
    for l, pnum, lnum in linestrings:
        if lnum > 0: 
           interior_lines.append( (l, pnum) )
    return interior_lines


def get_line_polygon(p_linestrings, p_num):
    lines = []
    for l, pnum in p_linestrings:
        if pnum == p_num:
            lines.append(l)
    return lines


def poly_geom(exterior_linestrings, interior_linestrings):
    """
    Rebuild the polygons
    """
    polygons = []
    for el, pnum in exterior_linestrings :
        lines = get_line_polygon(interior_linestrings, pnum)
        if len(lines) == 0 : # no interior line
            polygons.append(Polygon(el).buffer(0))
        else:
            for l in lines:
                polygons.append(Polygon(el, Polygon(l).interiors).buffer(0)) 
    return MultiPolygon(polygons)


def clean_multi(shape):
    """
    Remove self- and ring-selfintersections from input Polygon geometries
    """
    polygons = split_multi(shape)
    linestrings = split_line(polygons)
    exterior_lines = line_exterior(linestrings)
    interior_lines = line_interior(linestrings)
    poly = poly_geom(interior_lines, exterior_lines)
    assert poly.is_valid, \
        "Not valid polygon %s because %s" \
=======
def clean_multi(shape):
    """
    Remove self- and ring-selfintersections from input Polygon geometries
    """
    polygons = []
    exterior_lines = []
    interior_lines = []
    for p in shape:
        exterior_lines = []
        interior_lines = []
        lnum = 0
        boundary = p.boundary
        if boundary.type == 'LineString':
            if lnum == 0:
                exterior_lines.append(boundary)
        else:
            for ls in boundary:
                if lnum == 0:
                    exterior_lines.append(ls)
                else:
                    interior_lines.append(ls)
                lnum += 1
    for el in exterior_lines:
        if len(interior_lines) == 0:
            polygons.append(Polygon(el).buffer(0))
        else:
            for il in interior_lines:
                polygons.append(Polygon(el, Polygon(il).interiors).buffer(0))
    poly = MultiPolygon(polygons)
    assert poly.is_valid, \
        "Not valid multipolygon %s because %s" \
>>>>>>> on_invalid_geometry_make_valid_and_clean
        % (poly.wkt, explain_validity(poly))
    return poly
