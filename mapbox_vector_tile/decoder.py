from mapbox_vector_tile.Mapbox import vector_tile_pb2 as vector_tile
from mapbox_vector_tile.utils import (
    CMD_BITS,
    CMD_LINE_TO,
    CMD_MOVE_TO,
    CMD_SEG_END,
    LINESTRING,
    POINT,
    POLYGON,
    get_decode_options,
    zig_zag_decode,
)


class TileData:
    def __init__(self, pbf_data, per_layer_options=None, default_options=None):
        self.tile = vector_tile.tile()
        self.tile.ParseFromString(pbf_data)
        self.default_options = default_options
        self.per_layer_options = per_layer_options if per_layer_options is not None else {}

    def get_message(self):
        tile = {}
        for layer in self.tile.layers:
            layer_name = layer.name
            layer_options = self.per_layer_options.get(layer_name, None)
            layer_options = get_decode_options(layer_options=layer_options, default_options=self.default_options)

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

                geometry = self.parse_geometry(
                    geom=feature.geometry,
                    ftype=feature.type,
                    extent=layer.extent,
                    y_coord_down=layer_options["y_coord_down"],
                    transformer=layer_options["transformer"],
                )
                if layer_options["geojson"]:
                    new_feature = {"geometry": geometry, "properties": props, "id": feature.id, "type": "Feature"}
                else:
                    new_feature = {"geometry": geometry, "properties": props, "id": feature.id, "type": feature.type}
                features.append(new_feature)

            tile_data = {"extent": layer.extent, "version": layer.version, "features": features}
            if layer_options["geojson"]:
                tile_data["type"] = "FeatureCollection"

            tile[layer_name] = tile_data
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
        a = sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1] for i in range(len(ring) - 1))
        return -1 if a < 0 else 1 if a > 0 else 0

    @staticmethod
    def _ensure_polygon_closed(coords):
        if coords and coords[0] != coords[-1]:
            coords.append(coords[0])

    def parse_geometry(self, geom, ftype, extent, y_coord_down, transformer):  # noqa:C901
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
                if coords and cmd == CMD_MOVE_TO and ftype in (LINESTRING, POLYGON):
                    # multi line string or polygon our encoder includes CMD_SEG_END to denote the end of a
                    # polygon ring, but this path would also handle the case where we receive a move without a
                    # previous close on polygons

                    # for polygons, we want to ensure that it is closed
                    if ftype == POLYGON:
                        self._ensure_polygon_closed(coords)
                    parts.append(coords)
                    coords = []

                for _ in range(cmd_len):
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

                    if not y_coord_down:
                        y = extent - y

                    if transformer is None:
                        coords.append([x, y])
                    else:
                        coords.append([*transformer(x, y)])

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
