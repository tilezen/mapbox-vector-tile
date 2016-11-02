
cmd_bits = 3

CMD_MOVE_TO = 1
CMD_LINE_TO = 2
CMD_SEG_END = 7
CMD_FAKE = 0


def omit_last(iterator):
    try:
        next_elmt = next(iterator)
        while True:
            elmt = next_elmt
            next_elmt = next(iterator)
            yield elmt
    except StopIteration:
        pass


class GeometryEncoder:
    """
    """
    def __init__(self, geometry, y_coord_down, extents, round_fn):
        self._geometry = geometry
        self._y_coord_down = y_coord_down
        self._extents = extents
        self._round = round_fn
        self._cmd_idx = -1
        self._geom_size = 0
        self.last_x, self.last_y = 0, 0

    def _encode_cmd_length(self, cmd, length):
        return (length << cmd_bits) | (cmd & ((1 << cmd_bits) - 1))

    def reserve_space_for_cmd(self):
        self._geometry.append(CMD_FAKE)
        self._cmd_idx = self._geom_size
        self._geom_size += 1

    def append_cmd(self, cmd, length):
        cmd_encoded = self._encode_cmd_length(cmd, length)
        self._geometry.append(cmd_encoded)
        self._geom_size += 1

    def set_back_cmd(self, cmd):
        length = (self._geom_size - self._cmd_idx) >> 1
        cmd_encoded = self._encode_cmd_length(cmd, length)
        self._geometry[self._cmd_idx] = cmd_encoded

    def force_int(self, n):
        if isinstance(n, float):
            return int(self._round(n))
        return n

    def append_coords(self, fx, fy, force=False):
        x = self.force_int(fx)
        if not self._y_coord_down:
            y = self._extents - self.force_int(fy)
        else:
            y = self.force_int(fy)
        dx = x - self.last_x
        dy = y - self.last_y
        if not force and dx == 0 and dy == 0:
            return
        self._geometry.append((dx << 1) ^ (dx >> 31))
        self._geometry.append((dy << 1) ^ (dy >> 31))
        self.last_x = x
        self.last_y = y
        self._geom_size += 2

    def append_ring(self, arc):
        it = iter(arc.coords)
        x, y = next(it)
        self.append_cmd(CMD_MOVE_TO, 1)
        self.append_coords(x, y, True)
        self.reserve_space_for_cmd()
        for x, y in omit_last(it):
            self.append_coords(x, y)
        self.set_back_cmd(CMD_LINE_TO)
        self.append_cmd(CMD_SEG_END, 1)

    def append_arc(self, arc):
        it = iter(arc.coords)
        x, y = next(it)
        self.append_cmd(CMD_MOVE_TO, 1)
        self.append_coords(x, y, True)
        self.reserve_space_for_cmd()
        for x, y in it:
            self.append_coords(x, y)
        self.set_back_cmd(CMD_LINE_TO)

    def append_polygon(self, shape):
        self.append_ring(shape.exterior)
        for arc in shape.interiors:
            self.append_ring(arc)

    def encode(self, shape):
        if shape.type == 'GeometryCollection':
            # do nothing
            pass
        elif shape.type == 'Point':
            self.append_cmd(CMD_MOVE_TO, 1)
            self.append_coords(shape.x, shape.y, True)
        elif shape.type == 'MultiPoint':
            self.append_cmd(CMD_MOVE_TO, len(shape.geoms))
            for point in shape.geoms:
                self.append_coords(point.x, point.y, True)
        elif shape.type == 'LineString':
            self.append_arc(shape)
        elif shape.type == 'MultiLineString':
            for arc in shape.geoms:
                self.append_arc(arc)
        elif shape.type == 'Polygon':
            self.append_polygon(shape)
        elif shape.type == 'MultiPolygon':
            for polygon in shape.geoms:
                self.append_polygon(polygon)
        else:
            raise NotImplementedError("Can't do %s geometries" % shape.type)
