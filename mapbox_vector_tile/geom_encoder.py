import itertools as it

from mapbox_vector_tile.utils import CMD_BITS, CMD_FAKE, CMD_LINE_TO, CMD_MOVE_TO, CMD_SEG_END, zig_zag_encode


class GeometryEncoder:
    def __init__(self, y_coord_down, extents):
        self._geometry = []
        self._y_coord_down = y_coord_down
        self._extents = extents
        self._last_x, self._last_y = 0, 0

    @classmethod
    def encode_cmd_length(cls, cmd, length):
        return (length << CMD_BITS) | (cmd & ((1 << CMD_BITS) - 1))

    @staticmethod
    def omit_last(iterator):
        iterator, lookahead = it.tee(iterator)
        next(lookahead, None)
        for _ in lookahead:
            yield next(iterator)

    def coords_on_grid(self, x, y):
        """Snap coordinates on the grid with integer coordinates"""
        if isinstance(x, float):
            x = int(round(x))
        if isinstance(y, float):
            y = int(round(y))
        if not self._y_coord_down:
            y = self._extents - y
        return x, y

    def encode_multipoint(self, points):
        cmd_move_to = self.encode_cmd_length(CMD_MOVE_TO, len(points))
        self._geometry = [cmd_move_to]
        last_x = 0
        last_y = 0
        for point in points:
            x, y = self.coords_on_grid(point.x, point.y)
            dx, dy = x - last_x, y - last_y
            self._geometry.append(zig_zag_encode(dx))
            self._geometry.append(zig_zag_encode(dy))
            last_x = x
            last_y = y

    def encode_arc(self, coords):
        """Appends commands to _geometry to create an arc.
        - Returns False if nothing was added
        - Returns True and moves _last_x, _last_y if
            some points where added
        """
        last_x, last_y = self._last_x, self._last_y
        float_x, float_y = next(coords)
        x, y = self.coords_on_grid(float_x, float_y)
        dx, dy = x - last_x, y - last_y
        cmd_encoded = self.encode_cmd_length(CMD_MOVE_TO, 1)
        commands = [cmd_encoded, zig_zag_encode(dx), zig_zag_encode(dy), CMD_FAKE]
        pairs_added = 0
        last_x, last_y = x, y
        for float_x, float_y in coords:
            x, y = self.coords_on_grid(float_x, float_y)
            dx, dy = x - last_x, y - last_y
            if dx == 0 and dy == 0:
                continue
            commands.append(zig_zag_encode(dx))
            commands.append(zig_zag_encode(dy))
            last_x, last_y = x, y
            pairs_added += 1
        if pairs_added == 0:
            return False
        cmd_encoded = self.encode_cmd_length(CMD_LINE_TO, pairs_added)
        commands[3] = cmd_encoded
        self._geometry.extend(commands)
        self._last_x, self._last_y = last_x, last_y
        return True

    def encode_multilinestring(self, shape):
        for arc in shape.geoms:
            coords = iter(arc.coords)
            self.encode_arc(coords)

    def encode_ring(self, ring):
        coords = self.omit_last(iter(ring.coords))
        if not self.encode_arc(coords):
            return False
        cmd_seg_end = self.encode_cmd_length(CMD_SEG_END, 1)
        self._geometry.append(cmd_seg_end)
        return True

    def encode_polygon(self, shape):
        if not self.encode_ring(shape.exterior):
            return
        for arc in shape.interiors:
            self.encode_ring(arc)

    def encode_multipolygon(self, shape):
        for polygon in shape.geoms:
            self.encode_polygon(polygon)

    def encode(self, shape):
        if shape.geom_type == "GeometryCollection":
            # do nothing
            pass
        elif shape.geom_type == "Point":
            x, y = self.coords_on_grid(shape.x, shape.y)
            cmd_encoded = self.encode_cmd_length(CMD_MOVE_TO, 1)
            self._geometry = [cmd_encoded, zig_zag_encode(x), zig_zag_encode(y)]
        elif shape.geom_type == "MultiPoint":
            self.encode_multipoint(shape.geoms)
        elif shape.geom_type == "LineString":
            coords = iter(shape.coords)
            self.encode_arc(coords)
        elif shape.geom_type == "MultiLineString":
            self.encode_multilinestring(shape)
        elif shape.geom_type == "Polygon":
            self.encode_polygon(shape)
        elif shape.geom_type == "MultiPolygon":
            self.encode_multipolygon(shape)
        else:
            raise NotImplementedError(f"Can't do {shape.geom_type} geometries")
        return self._geometry
