
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


def encode_cmd_length(cmd, length):
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
        self._last_x, self._last_y = 0, 0

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

    def encode_multipoint(self, points):
        cmd_move_to = encode_cmd_length(CMD_MOVE_TO, len(points))
        self._geometry.append(cmd_move_to)
        last_x = 0
        last_y = 0
        for float_x, float_y in points:
            x, y = self.coords_on_grid(float_x, float_y)
            dx, dy = x - last_x, y - last_y
            self._geometry.append(zigzag(dx))
            self._geometry.append(zigzag(dy))
            last_x = x
            last_y = y

    def encode_arc(self, coords):
        """ Appends commands to _geometry to create an arc.
            - Returns False if nothing was added
            - Returns True and moves _last_x, _last_y if some points where added
        """
        last_x, last_y = self._last_x, self._last_y
        float_x, float_y = next(coords)
        x, y = self.coords_on_grid(float_x, float_y)
        dx, dy = x - last_x, y - last_y
        cmd_encoded = encode_cmd_length(CMD_MOVE_TO, 1)
        commands = [cmd_encoded,
                    zigzag(dx),
                    zigzag(dy),
                    CMD_FAKE
                    ]
        pairs_added = 0
        last_x, last_y = x, y
        for float_x, float_y in coords:
            x, y = self.coords_on_grid(float_x, float_y)
            dx, dy = x - last_x, y - last_y
            if dx == 0 and dy == 0:
                continue
            commands.append(zigzag(dx))
            commands.append(zigzag(dy))
            last_x, last_y = x, y
            pairs_added += 1
        if pairs_added == 0:
            return False
        cmd_encoded = encode_cmd_length(CMD_LINE_TO, pairs_added)
        commands[3] = cmd_encoded
        self._geometry.extend(commands)
        self._last_x, self._last_y = last_x, last_y
        return True

    def encode_multilinestring(self, shape):
        for arc in shape.geoms:
            coords = iter(arc.coords)
            self.encode_arc(coords)

    def encode_ring(self, ring):
        coords = omit_last(iter(ring.coords))
        if not self.encode_arc(coords):
            return False
        cmd_seg_end = encode_cmd_length(CMD_SEG_END, 1)
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
        if shape.type == 'GeometryCollection':
            # do nothing
            pass
        elif shape.type == 'Point':
            x, y = self.coords_on_grid(shape.x, shape.y)
            cmd_encoded = encode_cmd_length(CMD_MOVE_TO, 1)
            self._geometry.extend([cmd_encoded,
                              zigzag(x),
                              zigzag(y)
            ])
        elif shape.type == 'MultiPoint':
            self.encode_multipoint(shape.geoms)
        elif shape.type == 'LineString':
            coords = iter(shape.coords)
            self.encode_arc(coords)
        elif shape.type == 'MultiLineString':
            self.encode_multilinestring(shape)
        elif shape.type == 'Polygon':
            self.encode_polygon(shape)
        elif shape.type == 'MultiPolygon':
            self.encode_multipolygon(shape)
        else:
            raise NotImplementedError("Can't do %s geometries" % shape.type)

