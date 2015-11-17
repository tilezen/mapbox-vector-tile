from math import fabs
from numbers import Number
from shapely.geometry.base import BaseGeometry
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import orient
from shapely.wkb import loads as load_wkb
from shapely.wkt import loads as load_wkt
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    from .Mapbox import vector_tile_pb2_p3 as vector_tile
    xrange = range
else:
    from .Mapbox import vector_tile_pb2 as vector_tile

# tiles are padded by this number of pixels for the current zoom level
padding = 0

cmd_bits = 3
tolerance = 0

CMD_MOVE_TO = 1
CMD_LINE_TO = 2
CMD_SEG_END = 7


class VectorTile:
    """
    """
    def __init__(self, extents, layer_name=""):
        self.tile = vector_tile.tile()
        self.extents = extents

    def addFeatures(self, features, layer_name=""):
        self.layer = self.tile.layers.add()
        self.layer.name = layer_name
        self.layer.version = 2
        self.layer.extent = self.extents
        self.keys = []
        self.values = []

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

            if shape.type == 'MultiPolygon':
                # If we are a multipolygon, we need to ensure that the
                # winding orders of the consituent polygons are
                # correct. In particular, the winding order of the
                # interior rings need to be the opposite of the
                # exterior ones, and all interior rings need to follow
                # the exterior one. This is how the end of one polygon
                # and the beginning of another are signaled.
                shape = self.enforce_multipolygon_winding_order(shape)

            elif shape.type == 'Polygon':
                # Ensure that polygons are also oriented with the
                # appropriate winding order. Their exterior rings must
                # have a clockwise order, which is translated into a
                # clockwise order in MVT's tile-local coordinates with
                # the Y axis in "screen" (i.e: +ve down) configuration.
                # Note that while the Y axis flips, we also invert the
                # Y coordinate to get the tile-local value, which means
                # the clockwise orientation is unchanged.
                shape = orient(shape, sign=-1.0)

            self.addFeature(feature, shape)

    def enforce_multipolygon_winding_order(self, shape):
        assert shape.type == 'MultiPolygon'

        parts = []
        for part in shape.geoms:
            # see comment in shape.type == 'Polygon' above about why
            # the sign here has to be -1.
            part = orient(part, sign=-1.0)
            parts.append(part)
        oriented_shape = MultiPolygon(parts)
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

    def addFeature(self, feature, shape):
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
        self._geo_encode(f, shape)

    def _get_feature_type(self, shape):
        if shape.type == 'Point' or shape.type == 'MultiPoint':
            return self.tile.Point
        elif shape.type == 'LineString' or shape.type == 'MultiLineString':
            return self.tile.LineString
        elif shape.type == 'Polygon' or shape.type == 'MultiPolygon':
            return self.tile.Polygon

    def _encode_cmd_length(self, cmd, length):
        return (length << cmd_bits) | (cmd & ((1 << cmd_bits) - 1))

    def _chunker(self, seq, size):
        return [seq[pos:pos + size] for pos in xrange(0, len(seq), size)]

    def _can_handle_key(self, k):
        return isinstance(k, str) or \
            isinstance(k, str if PY3 else unicode)

    def _can_handle_val(self, v):
        if isinstance(v, str) or \
           isinstance(v, str if PY3 else unicode):
            return True
        elif isinstance(v, bool):
            return True
        elif (isinstance(v, int) or
              isinstance(v, int if PY3 else long)):
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
                if k not in self.keys:
                    layer.keys.append(k)
                    self.keys.append(k)
                feature.tags.append(self.keys.index(k))
                if v not in self.values:
                    self.values.append(v)
                    val = layer.values.add()
                    if isinstance(v, bool):
                        val.bool_value = v
                    elif (isinstance(v, str)):
                        if PY3:
                            val.string_value = str(v)
                        else:
                            val.string_value = unicode(v, 'utf8')
                    elif (isinstance(v, str if PY3 else unicode)):
                        val.string_value = v
                    elif (isinstance(v, int)) or (
                            isinstance(v, int if PY3 else long)):
                        val.int_value = v
                    elif (isinstance(v, float)):
                        val.double_value = v
                feature.tags.append(self.values.index(v))

    def _handle_skipped_last(self, f, skipped_index, cur_x, cur_y, x_, y_):
        last_x = f.geometry[skipped_index - 2]
        last_y = f.geometry[skipped_index - 1]
        last_dx = ((last_x >> 1) ^ (-(last_x & 1)))
        last_dy = ((last_y >> 1) ^ (-(last_y & 1)))
        dx = cur_x - x_ + last_dx
        dy = cur_y - y_ + last_dy
        x_ = cur_x
        y_ = cur_y
        f.geometry.__setitem__(skipped_index - 2, ((dx << 1) ^ (dx >> 31)))
        f.geometry.__setitem__(skipped_index - 1, ((dy << 1) ^ (dy >> 31)))

    def _parseGeometry(self, shape):
        coordinates = []
        line = "line"
        polygon = "polygon"

        def _get_point_obj(x, y, cmd=CMD_MOVE_TO):
            coordinate = {
                'x': x,
                'y': self.extents - y,
                'cmd': cmd
            }
            coordinates.append(coordinate)

        def _get_arc_obj(arc, type):
            length = len(arc.coords)
            iterator = 0
            cmd = CMD_MOVE_TO
            while (iterator < length):
                x = arc.coords[iterator][0]
                y = arc.coords[iterator][1]
                if iterator == 0:
                    cmd = CMD_MOVE_TO
                elif iterator == length-1 and type == polygon:
                    cmd = CMD_SEG_END
                else:
                    cmd = CMD_LINE_TO
                _get_point_obj(x, y, cmd)
                iterator = iterator + 1

        if shape.type == 'GeometryCollection':
            # do nothing
            coordinates = []

        elif shape.type == 'Point':
            _get_point_obj(shape.x, shape.y)

        elif shape.type == 'LineString':
            _get_arc_obj(shape, line)

        elif shape.type == 'Polygon':
            rings = [shape.exterior] + list(shape.interiors)
            for ring in rings:
                _get_arc_obj(ring, polygon)

        elif shape.type == 'MultiPoint':
            for point in shape.geoms:
                _get_point_obj(point.x, point.y)

        elif shape.type == 'MultiLineString':
            for arc in shape.geoms:
                _get_arc_obj(arc, line)

        elif shape.type == 'MultiPolygon':
            for polygon in shape.geoms:
                rings = [polygon.exterior] + list(polygon.interiors)
                for ring in rings:
                    _get_arc_obj(ring, polygon)

        else:
            raise NotImplementedError("Can't do %s geometries" % shape.type)

        return coordinates

    def _geo_encode(self, f, shape):
        x_, y_ = 0, 0

        cmd = -1
        cmd_idx = -1
        vtx_cmd = -1
        prev_cmd = -1

        skipped_index = -1
        skipped_last = False
        cur_x = 0
        cur_y = 0

        it = 0
        length = 0

        coordinates = self._parseGeometry(shape)

        while (True):
            if it >= len(coordinates):
                break

            c_it = coordinates[it]
            x, y, vtx_cmd = c_it['x'], c_it['y'], c_it['cmd']

            if vtx_cmd != cmd:
                if cmd_idx >= 0:
                    f.geometry[cmd_idx] = self._encode_cmd_length(cmd, length)

                cmd = vtx_cmd
                length = 0
                cmd_idx = len(f.geometry)
                f.geometry.append(0)  # placeholder added in first pass

            if (vtx_cmd == CMD_MOVE_TO or vtx_cmd == CMD_LINE_TO):
                if cmd == CMD_MOVE_TO and skipped_last and skipped_index > 1:
                    self._handle_skipped_last(
                        f, skipped_index, cur_x, cur_y, x_, y_)

                # Compute delta to the previous coordinate.
                cur_x = int(x)
                cur_y = int(y)

                dx = cur_x - x_
                dy = cur_y - y_

                sharp_turn_ahead = False

                if (it+2 <= len(coordinates)):
                    next_coord = coordinates[it+1]
                    if next_coord['cmd'] == CMD_LINE_TO:
                        next_x, next_y = next_coord['x'], next_coord['y']
                        next_dx = fabs(cur_x - int(next_x))
                        next_dy = fabs(cur_y - int(next_y))
                        if ((next_dx == 0 and next_dy >= tolerance) or
                                (next_dy == 0 and next_dx >= tolerance)):
                            sharp_turn_ahead = True

                # Keep all move_to commands, but omit other movements
                # that are not >= the tolerance threshold and should
                # be considered no-ops.
                # NOTE: length == 0 indicates the command has changed and will
                # preserve any non duplicate move_to or line_to
                if (length == 0 or sharp_turn_ahead or
                        fabs(dx) >= tolerance or fabs(dy) >= tolerance):
                    # Manual zigzag encoding.
                    f.geometry.append((dx << 1) ^ (dx >> 31))
                    f.geometry.append((dy << 1) ^ (dy >> 31))
                    x_ = cur_x
                    y_ = cur_y
                    skipped_last = False
                    length = length + 1
                else:
                    skipped_last = True
                    skipped_index = len(f.geometry)
            elif vtx_cmd == CMD_SEG_END:
                if prev_cmd != CMD_SEG_END:
                    length = length + 1
            else:
                raise Exception("Unknown command type: '%s'" % vtx_cmd)

            it = it + 1
            prev_cmd = cmd

        # at least one vertex + cmd/length
        if skipped_last and skipped_index > 1:
            # if we skipped previous vertex we just update it to the
            # last one here.
            self._handle_skipped_last(f, skipped_index, cur_x, cur_y, x_, y_)

        # Update the last length/command value.
        if cmd_idx >= 0:
            f.geometry[cmd_idx] = self._encode_cmd_length(cmd, length)
