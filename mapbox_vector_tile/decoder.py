from mapbox_vector_tile.Mapbox import vector_tile_pb2 as vector_tile
from mapbox_vector_tile.utils import (
    CMD_BITS,
    CMD_LINE_TO,
    CMD_MOVE_TO,
    CMD_SEG_END,
    LINESTRING,
    POINT,
    POLYGON,
    zig_zag_decode,
)


class TileData:
    def __init__(self, pbf_data, y_coord_down=False, transformer=None):
        self.tile = vector_tile.tile()
        self.tile.ParseFromString(pbf_data)
        self.y_coord_down = y_coord_down
        self.transformer = transformer

    def get_message(self):
        tile = {}
        for layer in self.tile.layers:
            keys = layer.keys
            vals = layer.values

            features = []
            for feature in layer.features:
                tags = feature.tags
                props = {}
                assert len(tags) % 2 == 0, "Unexpected number of tags"
                for key_idx, val_idx in zip(tags[::2], tags[1::2]):
                    key = keys[key_idx]
                    val = vals[val_idx]
                    value = self.parse_value(val)
                    props[key] = value

                geometry = self.parse_geometry(geom=feature.geometry, ftype=feature.type, extent=layer.extent)
                new_feature = {"geometry": geometry, "properties": props, "id": feature.id, "type": "Feature"}
                features.append(new_feature)

            tile[layer.name] = {
                "extent": layer.extent,
                "version": layer.version,
                "features": features,
                "type": "FeatureCollection",
            }
        return tile

    @staticmethod
    def zero_pad(val):
        return "0" + val if val[0] == "b" else val

    @staticmethod
    def parse_value(val):
        for candidate in (
            "bool_value",
            "double_value",
            "float_value",
            "int_value",
            "sint_value",
            "string_value",
            "uint_value",
        ):
            if val.HasField(candidate):
                return getattr(val, candidate)
        raise ValueError(f"{val} is an unknown value")

    @staticmethod
    def _area_sign(ring):
        a = sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1] for i in range(0, len(ring) - 1))
        return -1 if a < 0 else 1 if a > 0 else 0

    @staticmethod
    def _ensure_polygon_closed(coords):
        if coords and coords[0] != coords[-1]:
            coords.append(coords[0])

    def parse_geometry(self, geom, ftype, extent):  # noqa:C901
        # [9 0 8192 26 0 10 2 0 0 2 15]
        i = 0
        coords = []
        dx = 0
        dy = 0
        parts = []  # for multi linestrings and polygons

        while i != len(geom):
            item = bin(geom[i])
            ilen = len(item)
            cmd = int(self.zero_pad(item[(ilen - CMD_BITS) : ilen]), 2)
            cmd_len = int(self.zero_pad(item[: ilen - CMD_BITS]), 2)

            i = i + 1

            if cmd == CMD_SEG_END:
                if ftype == POLYGON:
                    self._ensure_polygon_closed(coords)
                parts.append(coords)
                coords = []

            elif cmd in (CMD_MOVE_TO, CMD_LINE_TO):
                if coords and cmd == CMD_MOVE_TO:
                    if ftype in (LINESTRING, POLYGON):
                        # multi line string or polygon our encoder includes CMD_SEG_END to denote the end of a
                        # polygon ring, but this path would also handle the case where we receive a move without a
                        # previous close on polygons

                        # for polygons, we want to ensure that it is closed
                        if ftype == POLYGON:
                            self._ensure_polygon_closed(coords)
                        parts.append(coords)
                        coords = []

                for point in range(0, cmd_len):
                    x = geom[i]
                    i = i + 1

                    y = geom[i]
                    i = i + 1

                    # zigzag decode
                    x = zig_zag_decode(x)
                    y = zig_zag_decode(y)

                    x = x + dx
                    y = y + dy

                    dx = x
                    dy = y

                    if not self.y_coord_down:
                        y = extent - y

                    if self.transformer is None:
                        coords.append([x, y])
                    else:
                        coords.append([*self.transformer(x, y)])

        if ftype == POINT:
            if len(coords) == 1:
                return {"type": "Point", "coordinates": coords[0]}
            else:
                return {"type": "MultiPoint", "coordinates": coords}
        elif ftype == LINESTRING:
            if parts:
                if coords:
                    parts.append(coords)
                if len(parts) == 1:
                    return {"type": "LineString", "coordinates": parts[0]}
                else:
                    return {"type": "MultiLineString", "coordinates": parts}
            else:
                return {"type": "LineString", "coordinates": coords}
        elif ftype == POLYGON:
            if coords:
                parts.append(coords)

            polygon = []
            polygons = []
            winding = 0

            for ring in parts:
                a = self._area_sign(ring)
                if a == 0:
                    continue
                if winding == 0:
                    winding = a

                if winding == a:
                    if polygon:
                        polygons.append(polygon)
                    polygon = [ring]
                else:
                    polygon.append(ring)

            if polygon:
                polygons.append(polygon)

            if len(polygons) == 1:
                return {"type": "Polygon", "coordinates": polygons[0]}
            else:
                return {"type": "MultiPolygon", "coordinates": polygons}

        else:
            raise ValueError(f"Unknown geometry type: {ftype}")
