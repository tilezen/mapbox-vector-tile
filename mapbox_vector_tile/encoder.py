import types
from Mapbox import vector_tile_pb2
from shapely.wkb import loads as load_wkb
from shapely.wkt import loads as load_wkt

from math import floor, fabs
from array import array

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
    def __init__(self, extents, layer_name="", encode_floats_big_endian=True):
        self.tile          = vector_tile_pb2.tile()
        self.extents       = extents
        self.encode_floats_big_endian = encode_floats_big_endian

    def addFeatures(self, features, layer_name=""):
        self.layer         = self.tile.layers.add()
        self.layer.name    = layer_name
        self.layer.version = 2
        self.layer.extent  = self.extents
        self.feature_count = 0
        self.keys   = []
        self.values = []

        for feature in features:
            self.addFeature(feature)

    def addFeature(self, feature):
        f = self.layer.features.add()
        self.feature_count += 1
        f.id = self.feature_count
        
        # osm_id or the hash can be passed in as a feature['id']
        if feature.has_key("id"):
            feature[1].update(uid=feature["id"])

        # properties
        if feature.has_key("properties"):
            self._handle_attr(self.layer, f, feature["properties"])

        # geometry
        if (feature.has_key("geometry")):
            shape = {}
            for load in [load_wkb, load_wkt]:
                try:
                    shape = load(feature["geometry"])
                    break
                except:
                    pass

            if shape:
                f.type = self._get_feature_type(shape)
                self._geo_encode(f, shape)
            else: 
                raise NotImplementedError("Can't do geometries that are not wkt or wkb")
                
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

    def _handle_attr(self, layer, feature, props):
        for k,v in props.items():
            if v is not None:
                if k not in self.keys:
                    layer.keys.append(k)
                    self.keys.append(k)
                feature.tags.append(self.keys.index(k))
                if v not in self.values:
                    self.values.append(v)
                    if (isinstance(v,bool)):
                        val = layer.values.add()
                        val.bool_value = v
                    elif (isinstance(v,str)) or (isinstance(v,unicode)):
                        val = layer.values.add()
                        val.string_value = unicode(v,'utf8')
                    elif (isinstance(v,int)) or (isinstance(v,long)):
                        val = layer.values.add()
                        val.int_value = v
                    elif (isinstance(v,float)):
                        val = layer.values.add()
                        if self.encode_floats_big_endian:
                            d_arr = array('d', [v])
                            # google pbf expects big endian by default
                            d_arr.byteswap()
                            val.double_value = d_arr[0]
                        else:
                            val.double_value = v
                    # else:
                    #     # do nothing because we know kind is sometimes <type NoneType>
                    #     logging.info("Unknown value type: '%s' for key: '%s'", type(v), k)
                    #     raise Exception("Unknown value type: '%s'" % type(v))
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
        line    = "line"
        polygon = "polygon"

        def _get_point_obj(x, y, cmd=CMD_MOVE_TO):
            coordinate = {
                'x'  : x,
                'y'  : self.extents - y,
                'cmd': cmd 
            }
            coordinates.append(coordinate)

        def _get_arc_obj(arc, type):
            length = len(arc.coords)
            iterator=0
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
            _get_point_obj(shape.x,shape.y)
    
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

        cmd= -1
        cmd_idx = -1
        vtx_cmd = -1
        prev_cmd= -1
        
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
            
            x,y,vtx_cmd = coordinates[it]['x'],coordinates[it]['y'],coordinates[it]['cmd']
            
            if vtx_cmd != cmd:
                if (cmd_idx >= 0):
                    f.geometry.__setitem__(cmd_idx, self._encode_cmd_length(cmd, length))

                cmd = vtx_cmd
                length = 0
                cmd_idx = len(f.geometry)
                f.geometry.append(0) #placeholder added in first pass

            if (vtx_cmd == CMD_MOVE_TO or vtx_cmd == CMD_LINE_TO):
                if cmd == CMD_MOVE_TO and skipped_last and skipped_index >1:
                    self._handle_skipped_last(f, skipped_index, cur_x, cur_y, x_, y_)
                
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
                        if ((next_dx == 0 and next_dy >= tolerance) or (next_dy == 0 and next_dx >= tolerance)):
                            sharp_turn_ahead = True

                # Keep all move_to commands, but omit other movements that are
                # not >= the tolerance threshold and should be considered no-ops.
                # NOTE: length == 0 indicates the command has changed and will
                # preserve any non duplicate move_to or line_to
                if length == 0 or sharp_turn_ahead or fabs(dx) >= tolerance or fabs(dy) >= tolerance:
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
        if (skipped_last and skipped_index > 1): 
            # if we skipped previous vertex we just update it to the last one here.
            self._handle_skipped_last(f, skipped_index, cur_x, cur_y, x_, y_)
        
        # Update the last length/command value.
        if (cmd_idx >= 0):
            f.geometry.__setitem__(cmd_idx, self._encode_cmd_length(cmd, length))
