from mapbox_vector_tile.polygon import make_it_valid
from numbers import Number
from past.builtins import long
from past.builtins import unicode
from past.builtins import xrange
from shapely.geometry.base import BaseGeometry
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import orient
from shapely.geometry.polygon import Polygon
from shapely.ops import transform
from shapely.wkb import loads as load_wkb
from shapely.wkt import loads as load_wkt
import decimal
from .compat import PY3, vector_tile, apply_map
from .geom_encoder import GeometryEncoder


def on_invalid_geometry_raise(shape):
    raise ValueError('Invalid geometry: %s' % shape.wkt)


def on_invalid_geometry_ignore(shape):
    return None


def on_invalid_geometry_make_valid(shape):
    return make_it_valid(shape)


class VectorTile:
    """
    """

    def __init__(self, extents, on_invalid_geometry=None,
                 max_geometry_validate_tries=5, round_fn=None):
        self.tile = vector_tile.tile()
        self.extents = extents
        self.on_invalid_geometry = on_invalid_geometry
        self.max_geometry_validate_tries = max_geometry_validate_tries
        self.round_fn = round_fn

    def _round(self, val):
        # Prefer provided round function.
        if self.round_fn:
            return self.round_fn(val)

        # round() has different behavior in python 2/3
        # For consistency between 2 and 3 we use quantize, however
        # it is slower than the built in round function.
        d = decimal.Decimal(val)
        rounded = d.quantize(1, rounding=decimal.ROUND_HALF_EVEN)
        return float(rounded)

    def addFeatures(self, features, layer_name='',
                    quantize_bounds=None, y_coord_down=False):

        self.layer = self.tile.layers.add()
        self.layer.name = layer_name
        self.layer.version = 1
        self.layer.extent = self.extents

        self.key_idx = 0
        self.val_idx = 0
        self.seen_keys_idx = {}
        self.seen_values_idx = {}

        for feature in features:

            # skip missing or empty geometries
            geometry_spec = feature.get('geometry')
            if geometry_spec is None:
                continue
            shape = self._load_geometry(geometry_spec)

            if shape is None:
                raise NotImplementedError(
                    'Can\'t do geometries that are not wkt, wkb, or shapely '
                    'geometries')

            if shape.is_empty:
                continue

            if quantize_bounds:
                shape = self.quantize(shape, quantize_bounds)

            shape = self.enforce_winding_order(shape, y_coord_down)

            if shape is not None and not shape.is_empty:
                self.addFeature(feature, shape, y_coord_down)

    def enforce_winding_order(self, shape, y_coord_down, n_try=1):
        if shape.type == 'MultiPolygon':
            # If we are a multipolygon, we need to ensure that the
            # winding orders of the consituent polygons are
            # correct. In particular, the winding order of the
            # interior rings need to be the opposite of the
            # exterior ones, and all interior rings need to follow
            # the exterior one. This is how the end of one polygon
            # and the beginning of another are signaled.
            shape = self.enforce_multipolygon_winding_order(
                shape, y_coord_down, n_try)

        elif shape.type == 'Polygon':
            # Ensure that polygons are also oriented with the
            # appropriate winding order. Their exterior rings must
            # have a clockwise order, which is translated into a
            # clockwise order in MVT's tile-local coordinates with
            # the Y axis in "screen" (i.e: +ve down) configuration.
            # Note that while the Y axis flips, we also invert the
            # Y coordinate to get the tile-local value, which means
            # the clockwise orientation is unchanged.
            shape = self.enforce_polygon_winding_order(
                shape, y_coord_down, n_try)

        # other shapes just get passed through
        return shape

    def quantize(self, shape, bounds):
        minx, miny, maxx, maxy = bounds

        def fn(x, y, z=None):
            xfac = self.extents / (maxx - minx)
            yfac = self.extents / (maxy - miny)
            x = xfac * (x - minx)
            y = yfac * (y - miny)
            return self._round(x), self._round(y)

        return transform(fn, shape)

    def handle_shape_validity(self, shape, y_coord_down, n_try):
        if shape.is_valid:
            return shape

        if n_try >= self.max_geometry_validate_tries:
            # ensure that we don't recurse indefinitely with an
            # invalid geometry handler that doesn't validate
            # geometries
            return None

        if self.on_invalid_geometry:
            shape = self.on_invalid_geometry(shape)
            if shape is not None and not shape.is_empty:
                # this means that we have a handler that might have
                # altered the geometry. We'll run through the process
                # again, but keep track of which attempt we are on to
                # terminate the recursion.
                shape = self.enforce_winding_order(
                    shape, y_coord_down, n_try + 1)

        return shape

    def enforce_multipolygon_winding_order(self, shape, y_coord_down, n_try):
        assert shape.type == 'MultiPolygon'

        parts = []
        for part in shape.geoms:
            part = self.enforce_polygon_winding_order(
                part, y_coord_down, n_try)
            if part is not None and not part.is_empty:
                if part.type == 'MultiPolygon':
                    parts.extend(part.geoms)
                else:
                    parts.append(part)

        if not parts:
            return None

        if len(parts) == 1:
            oriented_shape = parts[0]
        else:
            oriented_shape = MultiPolygon(parts)

        oriented_shape = self.handle_shape_validity(
            oriented_shape, y_coord_down, n_try)
        return oriented_shape

    def enforce_polygon_winding_order(self, shape, y_coord_down, n_try):
        assert shape.type == 'Polygon'

        def fn(point):
            x, y = point
            return self._round(x), self._round(y)

        exterior = apply_map(fn, shape.exterior.coords)
        rings = None

        if len(shape.interiors) > 0:
            rings = [apply_map(fn, ring.coords) for ring in shape.interiors]

        sign = 1.0 if y_coord_down else -1.0
        oriented_shape = orient(Polygon(exterior, rings), sign=sign)
        oriented_shape = self.handle_shape_validity(
            oriented_shape, y_coord_down, n_try)
        return oriented_shape

    def _load_geometry(self, geometry_spec):
        if isinstance(geometry_spec, BaseGeometry):
            return geometry_spec

        try:
            return load_wkb(geometry_spec)
        except:
            try:
                return load_wkt(geometry_spec)
            except:
                return None

    def addFeature(self, feature, shape, y_coord_down):
        f = self.layer.features.add()

        fid = feature.get('id')
        if fid is not None:
            if isinstance(fid, Number) and fid >= 0:
                f.id = fid

        # properties
        properties = feature.get('properties')
        if properties is not None:
            self._handle_attr(self.layer, f, properties)

        f.type = self._get_feature_type(shape)
        self._geo_encode(f, shape, y_coord_down)

    def _get_feature_type(self, shape):
        if shape.type == 'Point' or shape.type == 'MultiPoint':
            return self.tile.Point
        elif shape.type == 'LineString' or shape.type == 'MultiLineString':
            return self.tile.LineString
        elif shape.type == 'Polygon' or shape.type == 'MultiPolygon':
            return self.tile.Polygon
        elif shape.type == 'GeometryCollection':
            raise ValueError('Encoding geometry collections not supported')
        else:
            raise ValueError('Cannot encode unknown geometry type: %s' %
                             shape.type)

    def _chunker(self, seq, size):
        return [seq[pos:pos + size] for pos in xrange(0, len(seq), size)]

    def _can_handle_key(self, k):
        return isinstance(k, (str, unicode))

    def _can_handle_val(self, v):
        if isinstance(v, (str, unicode)):
            return True
        elif isinstance(v, bool):
            return True
        elif isinstance(v, (int, long)):
            return True
        elif isinstance(v, float):
            return True

        return False

    def _can_handle_attr(self, k, v):
        return self._can_handle_key(k) and \
            self._can_handle_val(v)

    def _handle_attr(self, layer, feature, props):
        for k, v in props.items():
            if self._can_handle_attr(k, v):
                if not PY3 and isinstance(k, str):
                    k = k.decode('utf-8')

                if k not in self.seen_keys_idx:
                    layer.keys.append(k)
                    self.seen_keys_idx[k] = self.key_idx
                    self.key_idx += 1

                feature.tags.append(self.seen_keys_idx[k])

                if v not in self.seen_values_idx:
                    self.seen_values_idx[v] = self.val_idx
                    self.val_idx += 1

                    val = layer.values.add()
                    if isinstance(v, bool):
                        val.bool_value = v
                    elif isinstance(v, str):
                        if PY3:
                            val.string_value = v
                        else:
                            val.string_value = unicode(v, 'utf-8')
                    elif isinstance(v, unicode):
                        val.string_value = v
                    elif isinstance(v, (int, long)):
                        val.int_value = v
                    elif isinstance(v, float):
                        val.double_value = v

                feature.tags.append(self.seen_values_idx[v])

    def _geo_encode(self, f, shape, y_coord_down):
        geom_encoder = GeometryEncoder(f.geometry, y_coord_down, self.extents,
                                       self._round)
        geom_encoder.encode(shape)
