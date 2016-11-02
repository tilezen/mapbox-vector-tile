
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


def _encode_cmd_length(cmd, length):
    return (length << cmd_bits) | (cmd & ((1 << cmd_bits) - 1))


def zigzag(delta):
    return (delta << 1) ^ (delta >> 31)


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

    def coords_on_grid(self, float_x, float_y):
        x = self.force_int(float_x)
        if not self._y_coord_down:
            y = self._extents - self.force_int(float_y)
        else:
            y = self.force_int(float_y)
        return x, y

    def append_coords(self, fx, fy, force=False):
        x = self.force_int(fx)
        if not self._y_coord_down:
            y = self._extents - self.force_int(fy)
        else:
            y = self.force_int(fy)
        dx = x - self.last_x
        dy = y - self.last_y
        if not force and dx == 0 and dy == 0:
            return 0
        self._geometry.append((dx << 1) ^ (dx >> 31))
        self._geometry.append((dy << 1) ^ (dy >> 31))
        self.last_x = x
        self.last_y = y
        self._geom_size += 2
        return 2

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

    def arc_commands(self, arc, last_x, last_y, ring=False):
        if ring:
            it = omit_last(iter(arc.coords))
        else:
            it = iter(arc.coords)
        float_x, float_y = next(it)
        x, y = self.coords_on_grid(float_x, float_y)
        dx, dy = x - last_x, y - last_y
        cmd_encoded = _encode_cmd_length(CMD_MOVE_TO, 1)
        commands = [cmd_encoded,
                    zigzag(dx),
                    zigzag(dy),
                    CMD_FAKE
                    ]
        pairs_added = 0
        last_x = x
        last_y = y
        for float_x, float_y in it:
            x, y = self.coords_on_grid(float_x, float_y)
            dx, dy = x - last_x, y - last_y
            if dx == 0 and dy == 0:
                continue
            commands.append(zigzag(dx))
            commands.append(zigzag(dy))
            last_x = x
            last_y = y
            pairs_added += 1
        if pairs_added == 0:
            return None, 0, 0
        cmd_encoded = _encode_cmd_length(CMD_LINE_TO, pairs_added)
        commands[3] = cmd_encoded
        cmd_encoded = _encode_cmd_length(CMD_SEG_END, 1)
        commands.append(cmd_encoded)
        return commands, last_x, last_y

    def append_arc(self, arc):
        it = iter(arc.coords)
        x, y = next(it)
        self.append_cmd(CMD_MOVE_TO, 1)
        self.append_coords(x, y, True)
        self.reserve_space_for_cmd()
        for x, y in it:
            self.append_coords(x, y)
        self.set_back_cmd(CMD_LINE_TO)

    def append_polygon_old(self, shape):
        self.append_ring(shape.exterior)
        for arc in shape.interiors:
            self.append_ring(arc)

    def append_polygon(self, shape):
        commands, final_x, final_y = self.arc_commands(shape.exterior, self.last_x, self.last_y, ring=True)
        self.append_commands(commands, final_x, final_y)
        for arc in shape.interiors:
            commands, final_x, final_y = self.arc_commands(arc, self.last_x, self.last_y, ring=True)
            self.append_commands(commands, final_x, final_y)

    def append_commands(self, commands, final_x, final_y):
        if commands:
            self._geometry.extend(commands)
            self._geom_size += len(commands)
            self.last_x, self.last_y = final_x, final_y

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
            commands, _, _ = self.arc_commands(shape, 0, 0, ring=False)
            if commands:
                self._geometry.extend(commands)
                self._geom_size += len(commands)
        elif shape.type == 'MultiLineString':
            for arc in shape.geoms:
                commands, final_x, final_y = self.arc_commands(arc, self.last_x, self.last_y, ring=False)
                self.append_commands(commands, final_x, final_y)
        elif shape.type == 'Polygon':
            self.append_polygon(shape)
        elif shape.type == 'MultiPolygon':
            for polygon in shape.geoms:
                self.append_polygon(polygon)
        else:
            raise NotImplementedError("Can't do %s geometries" % shape.type)
