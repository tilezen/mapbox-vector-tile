from numbers import Number

from shapely.geometry import shape as shapely_shape
from shapely.geometry.base import BaseGeometry
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon, orient
from shapely.ops import transform
from shapely.wkb import loads as load_wkb
from shapely.wkt import loads as load_wkt

from mapbox_vector_tile.geom_encoder import GeometryEncoder
from mapbox_vector_tile.Mapbox import vector_tile_pb2 as vector_tile
from mapbox_vector_tile.polygon import make_it_valid
from mapbox_vector_tile.utils import get_encode_options


def on_invalid_geometry_raise(shape):
    raise ValueError(f"Invalid geometry: {shape.wkt}")


def on_invalid_geometry_ignore(shape):
    return None


def on_invalid_geometry_make_valid(shape):
    return make_it_valid(shape)


class VectorTile:
    def __init__(self, default_options=None):
        self.tile = vector_tile.tile()
        self.default_options = default_options

        self.layer = None
        self.layer_options = None
        self.key_idx = 0
        self.val_idx = 0
        self.seen_keys_idx = {}
        self.seen_values_idx = {}
        self.seen_values_bool_idx = {}
        self.seen_layer_names = set()

    def add_layer(self, name, features, options=None):
        if not name:
            raise ValueError(f"A layer name can not be empty. {name!r} was provided.")
        if name in self.seen_layer_names:
            raise ValueError(f"The layer name {name!r} already exists in the vector tile.")
        self.seen_layer_names.add(name)
        self.layer = self.tile.layers.add()
        self.layer_options = get_encode_options(layer_options=options, default_options=self.default_options)
        self.layer.name = name
        self.layer.version = 2
        self.layer.extent = self.layer_options["extents"]

        self.key_idx = 0
        self.val_idx = 0
        self.seen_keys_idx = {}
        self.seen_values_idx = {}
        self.seen_values_bool_idx = {}

        for feature in features:
            # skip missing or empty geometries
            geometry_spec = feature.get("geometry")
            if geometry_spec is None:
                continue
            shape = self._load_geometry(geometry_spec)

            if shape is None:
                raise NotImplementedError("Can't do geometries that are not wkt, wkb, or shapely geometries")

            if shape.is_empty:
                continue

            if self.layer_options["quantize_bounds"]:
                shape = self.quantize(shape)
            if self.layer_options["check_winding_order"]:
                shape = self.enforce_winding_order(shape)

            if shape is not None and not shape.is_empty:
                self.add_feature(feature, shape)

    def enforce_winding_order(self, shape, n_try=1):
        if shape.geom_type == "MultiPolygon":
            # If we are a multipolygon, we need to ensure that the winding orders of the constituent polygons are
            # correct. In particular, the winding order of the interior rings need to be the opposite of the exterior
            # ones, and all interior rings need to follow the exterior one. This is how the end of one polygon and
            # the beginning of another are signaled.
            shape = self.enforce_multipolygon_winding_order(shape=shape, n_try=n_try)

        elif shape.geom_type == "Polygon":
            # Ensure that polygons are also oriented with the appropriate winding order. Their exterior rings must
            # have a clockwise order, which is translated into a clockwise order in MVT's tile-local coordinates with
            # the Y axis in "screen" (i.e: +ve down) configuration. Note that while the Y axis flips, we also invert
            # the Y coordinate to get the tile-local value, which means the clockwise orientation is unchanged.
            shape = self.enforce_polygon_winding_order(shape=shape, n_try=n_try)

        # other shapes just get passed through
        return shape

    def quantize(self, shape):
        minx, miny, maxx, maxy = self.layer_options["quantize_bounds"]
        extents = self.layer_options["extents"]

        def fn(x, y, z=None):
            xfac = extents / (maxx - minx)
            yfac = extents / (maxy - miny)
            x = xfac * (x - minx)
            y = yfac * (y - miny)
            return round(x), round(y)

        return transform(fn, shape)

    def handle_shape_validity(self, shape, n_try):
        if shape.is_valid:
            return shape

        if n_try >= self.layer_options["max_geometry_validate_tries"]:
            # ensure that we don't recurse indefinitely with an invalid geometry handler that doesn't validate
            # geometries
            return None

        if self.layer_options["on_invalid_geometry"]:
            shape = self.layer_options["on_invalid_geometry"](shape)
            if shape is not None and not shape.is_empty:
                # This means that we have a handler that might have altered the geometry. We'll run through the process
                # again, but keep track of which attempt we are on to terminate the recursion.
                shape = self.enforce_winding_order(shape=shape, n_try=n_try + 1)

        return shape

    def enforce_multipolygon_winding_order(self, shape, n_try):
        assert shape.geom_type == "MultiPolygon"

        parts = []
        for part in shape.geoms:
            part = self.enforce_polygon_winding_order(shape=part, n_try=n_try)
            if part is not None and not part.is_empty:
                if part.geom_type == "MultiPolygon":
                    parts.extend(part.geoms)
                else:
                    parts.append(part)

        if not parts:
            return None

        oriented_shape = parts[0] if len(parts) == 1 else MultiPolygon(parts)
        oriented_shape = self.handle_shape_validity(oriented_shape, n_try)
        return oriented_shape

    def enforce_polygon_winding_order(self, shape, n_try):
        assert shape.geom_type == "Polygon"

        def fn(point):
            x, y = point
            return round(x), round(y)

        exterior = self.apply_map(fn, shape.exterior.coords)
        rings = None

        if len(shape.interiors) > 0:
            rings = [self.apply_map(fn, ring.coords) for ring in shape.interiors]

        sign = 1.0 if self.layer_options["y_coord_down"] else -1.0
        oriented_shape = orient(Polygon(exterior, rings), sign=sign)
        oriented_shape = self.handle_shape_validity(oriented_shape, n_try)
        return oriented_shape

    @staticmethod
    def apply_map(fn, x):
        return list(map(fn, x))

    def _load_geometry(self, geometry_spec):
        if isinstance(geometry_spec, BaseGeometry):
            geom = geometry_spec
        elif isinstance(geometry_spec, dict):
            geom = shapely_shape(geometry_spec)
        else:
            try:
                geom = load_wkb(geometry_spec)
            except Exception:
                try:
                    geom = load_wkt(geometry_spec)
                except Exception:
                    return None

        if self.layer_options["transformer"] is None:
            return geom
        else:
            return transform(self.layer_options["transformer"], geom)

    def add_feature(self, feature, shape):
        geom_encoder = GeometryEncoder(self.layer_options["y_coord_down"], self.layer_options["extents"])
        geometry = geom_encoder.encode(shape)

        feature_type = self._get_feature_type(shape)
        if len(geometry) == 0:
            # Don't add geometry if it's too small
            return
        f = self.layer.features.add()

        fid = feature.get("id")
        if fid is not None and isinstance(fid, Number) and fid >= 0:
            f.id = fid

        # properties
        properties = feature.get("properties")
        if properties is not None:
            self._handle_attr(self.layer, f, properties)

        f.type = feature_type
        f.geometry.extend(geometry)

    def _get_feature_type(self, shape):
        if shape.geom_type == "Point" or shape.geom_type == "MultiPoint":
            return self.tile.Point
        elif shape.geom_type == "LineString" or shape.geom_type == "MultiLineString":
            return self.tile.LineString
        elif shape.geom_type == "Polygon" or shape.geom_type == "MultiPolygon":
            return self.tile.Polygon
        elif shape.geom_type == "GeometryCollection":
            raise ValueError("Encoding geometry collections not supported")
        else:
            raise ValueError(f"Cannot encode unknown geometry type: {shape.geom_type}")

    @staticmethod
    def _chunker(seq, size):
        return [seq[pos : pos + size] for pos in range(0, len(seq), size)]

    @staticmethod
    def _can_handle_key(k):
        return isinstance(k, str)

    @staticmethod
    def _can_handle_val(v):
        return isinstance(v, (str, bool, int, float))

    @classmethod
    def _can_handle_attr(cls, k, v):
        return cls._can_handle_key(k) and cls._can_handle_val(v)

    def _handle_attr(self, layer, feature, props):
        for k, v in props.items():
            if self._can_handle_attr(k, v):
                if k not in self.seen_keys_idx:
                    layer.keys.append(k)
                    self.seen_keys_idx[k] = self.key_idx
                    self.key_idx += 1

                feature.tags.append(self.seen_keys_idx[k])

                values_idx = self.seen_values_bool_idx if isinstance(v, bool) else self.seen_values_idx
                if v not in values_idx:
                    values_idx[v] = self.val_idx
                    self.val_idx += 1

                    val = layer.values.add()
                    if isinstance(v, bool):
                        val.bool_value = v
                    elif isinstance(v, str):
                        val.string_value = v
                    elif isinstance(v, int):
                        val.int_value = v
                    elif isinstance(v, float):
                        val.double_value = v

                feature.tags.append(values_idx[v])
