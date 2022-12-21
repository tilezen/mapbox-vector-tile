"""
Tests for vector_tile/encoder.py
"""
import unittest

from shapely import wkt

import mapbox_vector_tile
from mapbox_vector_tile import decode, encode


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.layer_name = "water"
        self.feature_properties = {"uid": 123, "foo": "bar", "baz": "foo"}
        self.feature_geometry = "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))"

    def assertRoundTrip(
        self,
        input_geometry,
        expected_geometry,
        name=None,
        properties=None,
        id=None,
        expected_len=1,
        expected_properties=None,
    ):
        if input_geometry is None:
            input_geometry = self.feature_geometry
        if name is None:
            name = self.layer_name
        if properties is None:
            properties = self.feature_properties
        if expected_properties is None:
            expected_properties = properties
        source = [{"name": name, "features": [{"geometry": input_geometry, "properties": properties}]}]
        if id:
            source[0]["features"][0]["id"] = id
        encoded = encode(source)
        decoded = decode(encoded)
        self.assertIn(name, decoded)
        layer = decoded[name]
        features = layer["features"]
        self.assertEqual(expected_len, len(features))
        self.assertEqual(features[0]["properties"], expected_properties)
        self.assertEqual(features[0]["geometry"], expected_geometry)
        if id:
            self.assertEqual(features[0]["id"], id)


class TestDifferentGeomFormats(BaseTestCase):
    def test_encoder(self):
        self.assertRoundTrip(
            input_geometry="POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))",
            expected_geometry={"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
        )

    def test_encoder_point(self):
        self.assertRoundTrip(input_geometry="POINT (1 2)", expected_geometry={"type": "Point", "coordinates": [1, 2]})

    def test_encoder_multipoint(self):
        self.assertRoundTrip(
            input_geometry="MULTIPOINT (1 2, 3 4)",
            expected_geometry={"type": "MultiPoint", "coordinates": [[1, 2], [3, 4]]},
        )

    def test_encoder_linestring(self):
        self.assertRoundTrip(
            input_geometry="LINESTRING (30 10, 10 30, 40 40)",
            expected_geometry={"type": "LineString", "coordinates": [[30, 10], [10, 30], [40, 40]]},
        )

    def test_encoder_multilinestring(self):
        self.assertRoundTrip(
            input_geometry="MULTILINESTRING ((10 10, 20 20, 10 40), (40 40, 30 30, 40 20, 30 10))",
            expected_geometry={
                "type": "MultiLineString",
                "coordinates": [[[10, 10], [20, 20], [10, 40]], [[40, 40], [30, 30], [40, 20], [30, 10]]],
            },
        )

    def test_encoder_polygon(self):
        self.assertRoundTrip(
            input_geometry="POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))",
            expected_geometry={"type": "Polygon", "coordinates": [[[30, 10], [10, 20], [20, 40], [40, 40], [30, 10]]]},
        )

    def test_encoder_polygon_w_hole(self):
        self.assertRoundTrip(
            input_geometry="POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10), (20 30, 35 35, 30 20, 20 30))",
            expected_geometry={
                "type": "Polygon",
                "coordinates": [
                    [[35, 10], [10, 20], [15, 40], [45, 45], [35, 10]],
                    [[20, 30], [30, 20], [35, 35], [20, 30]],
                ],
            },
        )

    def test_encoder_multipolygon(self):
        self.assertRoundTrip(
            input_geometry="MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)), ((15 5, 40 10, 10 20, 5 10, 15 5)))",
            expected_geometry={
                "type": "MultiPolygon",
                "coordinates": [
                    [[[30, 20], [10, 40], [45, 40], [30, 20]]],
                    [[[15, 5], [5, 10], [10, 20], [40, 10], [15, 5]]],
                ],
            },
        )

    def test_encoder_multipolygon_w_hole(self):
        self.assertRoundTrip(
            input_geometry="MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))",  # noqa
            expected_geometry={
                "type": "MultiPolygon",
                "coordinates": [
                    [[[40, 40], [45, 30], [20, 45], [40, 40]]],
                    [
                        [[20, 35], [45, 20], [30, 5], [10, 10], [10, 30], [20, 35]],
                        [[30, 20], [20, 25], [20, 15], [30, 20]],
                    ],
                ],
            },
        )

    def test_encoder_quantize_before_orient(self):
        self.assertRoundTrip(
            input_geometry="POLYGON ((0 0, 4 0, 4 4, 0 4, 0 0), (1 1, 3 2, 2 2, 1 1))",
            expected_geometry={
                "type": "Polygon",
                "coordinates": [[[0, 0], [0, 4], [4, 4], [4, 0], [0, 0]], [[1, 1], [3, 2], [2, 2], [1, 1]]],
            },
        )

    def test_encoder_winding_order_polygon(self):
        # example from the spec
        # https://github.com/mapbox/vector-tile-spec/tree/master/2.1#4355-example-polygon   ()
        # the order given in the example is clockwise in a y-up coordinate
        # system, but the coordinate system given for the example is y-down!
        # therefore the y coordinate in this example is flipped negative.
        self.assertRoundTrip(
            input_geometry="POLYGON ((3 -6, 8 -12, 20 -34, 3 -6))",
            expected_geometry={"type": "Polygon", "coordinates": [[[3, -6], [8, -12], [20, -34], [3, -6]]]},
        )

    def test_encoder_winding_order_polygon_reverse(self):
        # tests that encode _corrects_ the winding order
        # example is the same as above - note the flipped coordinate system.
        self.assertRoundTrip(
            input_geometry="POLYGON ((3 -6, 20 -34, 8 -12, 3 -6))",
            expected_geometry={"type": "Polygon", "coordinates": [[[3, -6], [8, -12], [20, -34], [3, -6]]]},
        )

    def test_encoder_winding_order_multipolygon(self):
        # example from the spec
        # https://github.com/mapbox/vector-tile-spec/tree/master/2.1#4356-example-multi-polygon   ()
        # the order given in the example is clockwise in a y-up coordinate
        # system, but the coordinate system given for the example is y-down!
        self.assertRoundTrip(
            input_geometry=(
                "MULTIPOLYGON ("
                + "((0 0, 10 0, 10 -10, 0 -10, 0 0)),"
                + "((11 -11, 20 -11, 20 -20, 11 -20, 11 -11),"
                + " (13 -13, 13 -17, 17 -17, 17 -13, 13 -13)))"
            ),
            expected_geometry={
                "type": "MultiPolygon",
                "coordinates": [
                    [[[0, 0], [10, 0], [10, -10], [0, -10], [0, 0]]],
                    [
                        [[11, -11], [20, -11], [20, -20], [11, -20], [11, -11]],
                        [[13, -13], [13, -17], [17, -17], [17, -13], [13, -13]],
                    ],
                ],
            },
        )

    def test_encoder_ensure_winding_after_quantization(self):
        self.assertRoundTrip(
            input_geometry="POLYGON ((0 0, 4 0, 4 4, 0 4, 0 0), (1 1, 3 2.4, 2 1.6, 1 1))",
            # should be single polygon with hole
            expected_geometry={
                "type": "Polygon",
                "coordinates": [[[0, 0], [0, 4], [4, 4], [4, 0], [0, 0]], [[1, 1], [3, 2], [2, 2], [1, 1]]],
            },
        )
        # but becomes multi-polygon
        # expected_geometry=[[[[0, 0], [0, 4], [4, 4], [4, 0], [0, 0]]],
        #                   [[[1, 1], [2, 2], [3, 2], [1, 1]]]])

    def test_with_wkt(self):
        self.assertRoundTrip(
            input_geometry="LINESTRING(-71.160281 42.258729,-71.160837 43.259113,-71.161144 42.25932)",
            expected_geometry={"type": "LineString", "coordinates": [[-71, 42], [-71, 43], [-71, 42]]},
        )

    def test_with_wkb(self):
        self.assertRoundTrip(
            input_geometry=b"\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000",  # noqa
            expected_geometry={"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
        )

    def test_with_shapely(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 43.259113,-71.161144 42.25932)"
        geometry = wkt.loads(geometry)
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={"type": "LineString", "coordinates": [[-71, 42], [-71, 43], [-71, 42]]},
        )

    def test_with_invalid_geometry(self):
        expected_result = "Can't do geometries that are not wkt, wkb, or shapely geometries"
        with self.assertRaises(NotImplementedError) as ex:
            mapbox_vector_tile.encode(
                [{"name": self.layer_name, "features": [{"geometry": "xyz", "properties": self.feature_properties}]}]
            )
        self.assertEqual(str(ex.exception), expected_result)

    def test_encode_unicode_property(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 43.259113,-71.161144 42.25932)"
        properties = {
            "foo": str(self.feature_properties["foo"]),
            "baz": str(self.feature_properties["baz"]),
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={"type": "LineString", "coordinates": [[-71, 42], [-71, 43], [-71, 42]]},
            properties=properties,
        )

    def test_encode_unicode_property_key(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 43.259113,-71.161144 42.25932)"
        properties = {"☺": "☺"}
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={"type": "LineString", "coordinates": [[-71, 42], [-71, 43], [-71, 42]]},
            properties=properties,
        )

    def test_encode_float_little_endian(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 43.259113,-71.161144 42.25932)"
        properties = {"floatval": 3.14159}
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={"type": "LineString", "coordinates": [[-71, 42], [-71, 43], [-71, 42]]},
            properties=properties,
        )

    def test_encode_feature_with_id(self):
        geometry = "POINT(1 1)"
        self.assertRoundTrip(input_geometry=geometry, expected_geometry={"type": "Point", "coordinates": [1, 1]}, id=42)

    def test_encode_point(self):
        geometry = "POINT(1 1)"
        self.assertRoundTrip(input_geometry=geometry, expected_geometry={"type": "Point", "coordinates": [1, 1]}, id=42)

    def test_encode_polygon_reverse_winding_order(self):
        geometry = "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))"
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
        )

    def test_encode_multipoint(self):
        geometry = "MULTIPOINT((10 10), (20 20), (10 40), (40 40), (30 30), (40 20), (30 10))"
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={
                "type": "MultiPoint",
                "coordinates": [[10, 10], [20, 20], [10, 40], [40, 40], [30, 30], [40, 20], [30, 10]],
            },
        )

    def test_encode_multilinestring(self):
        geometry = "MULTILINESTRING ((10 10, 20 20, 10 40), (40 40, 30 30, 40 20, 30 10))"
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={
                "type": "MultiLineString",
                "coordinates": [
                    [[10, 10], [20, 20], [10, 40]],
                    [[40, 40], [30, 30], [40, 20], [30, 10]],
                ],
            },
        )

    def test_encode_multipolygon_normal_winding_order(self):
        geometry = "MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))"  # noqa
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={
                "type": "MultiPolygon",
                "coordinates": [
                    [[[40, 40], [45, 30], [20, 45], [40, 40]]],
                    [
                        [[20, 35], [45, 20], [30, 5], [10, 10], [10, 30], [20, 35]],
                        [[30, 20], [20, 25], [20, 15], [30, 20]],
                    ],
                ],
            },
            expected_len=1,
        )

    def test_encode_multipolygon_normal_winding_order_zero_area(self):
        geometry = "MULTIPOLYGON (((40 40, 40 20, 40 45, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))"  # noqa
        # NB there is only one resultant polygon here
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={
                "type": "Polygon",
                "coordinates": [
                    [[20, 35], [45, 20], [30, 5], [10, 10], [10, 30], [20, 35]],
                    [[30, 20], [20, 25], [20, 15], [30, 20]],
                ],
            },
            expected_len=1,
        )

    def test_encode_multipolygon_reverse_winding_order(self):
        geometry = "MULTIPOLYGON (((10 10, 10 0, 0 0, 0 10, 10 10), (8 8, 2 8, 2 0, 8 0, 8 8)))"
        # NB there is only one resultant polygon here
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={
                "type": "Polygon",
                "coordinates": [
                    [[10, 10], [10, 0], [0, 0], [0, 10], [10, 10]],
                    [[8, 8], [2, 8], [2, 0], [8, 0], [8, 8]],
                ],
            },
            expected_len=1,
        )

    def test_encode_property_bool(self):
        geometry = "POINT(0 0)"
        properties = {"test_bool_true": True, "test_bool_false": False}
        self.assertRoundTrip(
            input_geometry=geometry, expected_geometry={"type": "Point", "coordinates": [0, 0]}, properties=properties
        )

    def test_encode_property_int(self):
        geometry = "POINT(0 0)"
        properties = {
            "test_int": int(1),
        }
        self.assertRoundTrip(
            input_geometry=geometry, expected_geometry={"type": "Point", "coordinates": [0, 0]}, properties=properties
        )

    def test_encode_property_null(self):
        geometry = "POINT(0 0)"
        properties = {"test_none": None, "test_empty": ""}
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={"type": "Point", "coordinates": [0, 0]},
            properties=properties,
            expected_properties={"test_empty": ""},
        )

    def test_encode_property_list(self):
        geometry = "POINT(0 0)"
        properties = {"test_list": [1, 2, 3], "test_empty": ""}
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry={"type": "Point", "coordinates": [0, 0]},
            properties=properties,
            expected_properties={"test_empty": ""},
        )

    def test_encode_multiple_values_test(self):
        geometry = "POINT(0 0)"
        properties1 = dict(foo="bar", baz="bar")
        properties2 = dict(quux="morx", baz="bar")
        name = "foo"
        feature1 = dict(geometry=geometry, properties=properties1)
        feature2 = dict(geometry=geometry, properties=properties2)
        source = [{"name": name, "features": [feature1, feature2]}]
        encoded = encode(source)
        decoded = decode(encoded)
        self.assertIn(name, decoded)
        layer = decoded[name]
        features = layer["features"]
        self.assertEqual(2, len(features))
        self.assertEqual(features[0]["properties"], properties1)
        self.assertEqual(features[1]["properties"], properties2)

    def test_encode_rounding_floats(self):
        geometry = "LINESTRING(1.1 1.1, 41.5 41.8)"
        exp_geoemtry = {"type": "LineString", "coordinates": [[1, 1], [42, 42]]}
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=exp_geoemtry,
        )

    def test_too_small_linestring(self):
        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid

        shape = shapely.wkt.loads("LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)")
        features = [dict(geometry=shape, properties={})]
        pbf = encode({"name": "foo", "features": features}, on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        features = result["foo"]["features"]
        self.assertEqual(0, len(features))

    def test_encode_1_True_values(self):
        geometry = "POINT(0 0)"
        properties = {
            "foo": True,
            "bar": 1,
        }
        source = [{"name": "layer", "features": [{"geometry": geometry, "properties": properties}]}]
        encoded = encode(source)
        decoded = decode(encoded)
        layer = decoded["layer"]
        features = layer["features"]
        act_props = features[0]["properties"]
        self.assertEqual(act_props["foo"], True)
        self.assertEqual(act_props["bar"], 1)
        self.assertTrue(isinstance(act_props["foo"], bool))
        self.assertFalse(isinstance(act_props["bar"], bool))


class TestDictGeometries(BaseTestCase):
    def _test_encoder_dict(self, geometry):
        self.assertRoundTrip(input_geometry=geometry, expected_geometry=geometry)

    def test_encoder_point(self):
        self._test_encoder_dict({"type": "Point", "coordinates": [1, 2]})

    def test_encoder_multipoint(self):
        self._test_encoder_dict({"type": "MultiPoint", "coordinates": [[1, 2], [3, 4]]})

    def test_encoder_linestring(self):
        self._test_encoder_dict({"type": "LineString", "coordinates": [[30, 10], [10, 30], [40, 40]]})

    def test_encoder_multilinestring(self):
        self._test_encoder_dict(
            {
                "type": "MultiLineString",
                "coordinates": [[[10, 10], [20, 20], [10, 40]], [[40, 40], [30, 30], [40, 20], [30, 10]]],
            }
        )

    def test_encoder_polygon(self):
        self._test_encoder_dict(
            {"type": "Polygon", "coordinates": [[[30, 10], [10, 20], [20, 40], [40, 40], [30, 10]]]}
        )

    def test_encoder_polygon_w_hole(self):
        self._test_encoder_dict(
            {
                "type": "Polygon",
                "coordinates": [
                    [[35, 10], [10, 20], [15, 40], [45, 45], [35, 10]],
                    [[20, 30], [30, 20], [35, 35], [20, 30]],
                ],
            }
        )

    def test_encoder_multipolygon(self):
        self._test_encoder_dict(
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [[[30, 20], [10, 40], [45, 40], [30, 20]]],
                    [[[15, 5], [5, 10], [10, 20], [40, 10], [15, 5]]],
                ],
            }
        )

    def test_encoder_multipolygon_w_hole(self):
        self._test_encoder_dict(
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [[[40, 40], [45, 30], [20, 45], [40, 40]]],
                    [
                        [[20, 35], [45, 20], [30, 5], [10, 10], [10, 30], [20, 35]],
                        [[30, 20], [20, 25], [20, 15], [30, 20]],
                    ],
                ],
            }
        )


class QuantizeTest(unittest.TestCase):
    def test_quantize(self):
        from mapbox_vector_tile import decode, encode

        props = dict(foo="bar")
        shape = "POINT(15 15)"
        feature = dict(geometry=shape, properties=props)
        features = [feature]
        source = dict(name="layername", features=features)
        bounds = 10.0, 10.0, 20.0, 20.0
        pbf = encode(source, quantize_bounds=bounds)
        result = decode(pbf)
        act_feature = result["layername"]["features"][0]
        act_geom = act_feature["geometry"]
        exp_geom = {"type": "Point", "coordinates": [2048, 2048]}
        self.assertEqual(exp_geom, act_geom)

    def test_y_coord_down(self):
        from mapbox_vector_tile import decode, encode

        props = dict(foo="bar")
        shape = "POINT(10 10)"
        feature = dict(geometry=shape, properties=props)
        features = [feature]
        source = dict(name="layername", features=features)
        pbf = encode(source, y_coord_down=True)
        result = decode(pbf, y_coord_down=True)
        act_feature = result["layername"]["features"][0]
        act_geom = act_feature["geometry"]
        exp_geom = {"type": "Point", "coordinates": [10, 10]}
        self.assertEqual(exp_geom, act_geom)

    def test_quantize_and_y_coord_down(self):
        from mapbox_vector_tile import decode, encode

        props = dict(foo="bar")
        shape = "POINT(30 30)"
        feature = dict(geometry=shape, properties=props)
        features = [feature]
        source = dict(name="layername", features=features)
        bounds = 0.0, 0.0, 50.0, 50.0
        pbf = encode(source, quantize_bounds=bounds, y_coord_down=True)

        result_decode_no_flip = decode(pbf, y_coord_down=True)
        act_feature = result_decode_no_flip["layername"]["features"][0]
        act_geom = act_feature["geometry"]
        exp_geom = {"type": "Point", "coordinates": [2458, 2458]}
        self.assertEqual(exp_geom, act_geom)

        result_decode_flip = decode(pbf)
        act_feature = result_decode_flip["layername"]["features"][0]
        act_geom = act_feature["geometry"]
        exp_geom = {"type": "Point", "coordinates": [2458, 1638]}
        self.assertEqual(exp_geom, act_geom)


class ExtentTest(unittest.TestCase):
    def test_custom_extent(self):
        from mapbox_vector_tile import decode, encode

        props = dict(foo="bar")
        shape = "POINT(10 10)"
        feature = dict(geometry=shape, properties=props)
        features = [feature]
        source = dict(name="layername", features=features)
        bounds = 0.0, 0.0, 10.0, 10.0
        pbf = encode(source, quantize_bounds=bounds, extents=50)
        result = decode(pbf)
        act_feature = result["layername"]["features"][0]
        act_geom = act_feature["geometry"]
        exp_geom = {"type": "Point", "coordinates": [50, 50]}
        self.assertEqual(exp_geom, act_geom)


class InvalidGeometryTest(unittest.TestCase):
    def test_invalid_geometry_ignore(self):
        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_ignore

        geometry = "POLYGON ((10 10, 20 10, 20 20, 15 15, 15 5, 10 10))"
        shape = shapely.wkt.loads(geometry)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name="layername", features=[feature])
        pbf = encode(source, on_invalid_geometry=on_invalid_geometry_ignore)
        result = decode(pbf)
        self.assertEqual(0, len(result["layername"]["features"]))

    def test_invalid_geometry_raise(self):
        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_raise

        geometry = "POLYGON ((10 10, 20 10, 20 20, 15 15, 15 5, 10 10))"
        shape = shapely.wkt.loads(geometry)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name="layername", features=[feature])
        with self.assertRaises(Exception):
            encode(source, on_invalid_geometry=on_invalid_geometry_raise)

    def test_invalid_geometry_make_valid(self):
        import shapely.geometry
        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid

        geometry = "POLYGON ((10 10, 20 10, 20 20, 15 15, 15 5, 10 10))"
        shape = shapely.wkt.loads(geometry)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name="layername", features=[feature])
        pbf = encode(source, on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        self.assertEqual(1, len(result["layername"]["features"]))
        valid_geometry = result["layername"]["features"][0]["geometry"]
        self.assertTrue(valid_geometry["type"], "MultiPolygon")
        multipolygon = shapely.geometry.shape(valid_geometry)
        self.assertTrue(multipolygon.geom_type, "MultiPolygon")
        self.assertTrue(multipolygon.is_valid)

        for poly in multipolygon.geoms:
            self.assertTrue(poly.is_valid)

    def test_bowtie_self_touching(self):
        import shapely.geometry
        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid

        bowtie = "POLYGON ((0 0, 0 2, 1 1, 2 2, 2 0, 1 1, 0 0))"
        shape = shapely.wkt.loads(bowtie)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name="layername", features=[feature])
        pbf = encode(source, on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        self.assertEqual(1, len(result["layername"]["features"]))
        valid_geometries = result["layername"]["features"][0]["geometry"]
        multipolygon = shapely.geometry.shape(valid_geometries)
        self.assertEqual(2, len(multipolygon.geoms))
        shape1, shape2 = multipolygon.geoms
        self.assertTrue(shape1.is_valid)
        self.assertTrue(shape2.is_valid)
        self.assertGreater(shape1.area, 0)
        self.assertGreater(shape2.area, 0)

    def test_bowtie_self_crossing(self):
        import shapely.geometry
        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid

        bowtie = "POLYGON ((0 0, 2 2, 2 0, 0 2, 0 0))"
        shape = shapely.wkt.loads(bowtie)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name="layername", features=[feature])
        pbf = encode(source, on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        self.assertEqual(1, len(result["layername"]["features"]))
        valid_geometries = result["layername"]["features"][0]["geometry"]
        multipolygon = shapely.geometry.shape(valid_geometries)
        self.assertEqual(multipolygon.geom_type, "MultiPolygon")
        self.assertTrue(multipolygon.is_valid)

        total_area = 0
        for p in multipolygon.geoms:
            self.assertEqual(p.geom_type, "Polygon")
            self.assertTrue(p.is_valid)
            self.assertGreater(p.area, 0)
            total_area += p.area
        self.assertEqual(2, total_area)

    def test_make_valid_self_crossing(self):
        import shapely.geometry
        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid

        geometry = "POLYGON ((10 10, 20 10, 20 20, 15 15, 15 5, 10 10))"
        shape = shapely.wkt.loads(geometry)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name="layername", features=[feature])
        pbf = encode(source, on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        self.assertEqual(1, len(result["layername"]["features"]))
        valid_geometries = result["layername"]["features"][0]["geometry"]
        geom_type = result["layername"]["features"][0]["type"]
        self.assertEqual(3, geom_type)  # 3 means POLYGON
        self.assertEqual(valid_geometries["type"], "MultiPolygon")
        multipolygon = shapely.geometry.shape(valid_geometries)
        self.assertTrue(multipolygon.is_valid)

        total_area = 0
        for p in multipolygon.geoms:
            self.assertTrue(p.is_valid)
            self.assertGreater(p.area, 0)
            total_area += p.area

        self.assertEqual(50, total_area)
        self.assertEqual(50, multipolygon.area)

    def test_validate_generates_rounding_error(self):
        import shapely.geometry
        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid

        bowtie = "POLYGON((0 0, 1 1, 0 1, 1 0, 0 0))"
        shape = shapely.wkt.loads(bowtie)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name="layername", features=[feature])
        pbf = encode(source, on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        features = result["layername"]["features"]
        self.assertEqual(1, len(features))
        self.assertEqual(features[0]["geometry"]["type"], "Polygon")
        shape = shapely.geometry.shape(features[0]["geometry"])
        self.assertEqual(shape.geom_type, "Polygon")
        self.assertTrue(shape.is_valid)
        self.assertGreater(shape.area, 0)

    def test_geometry_collection_raises(self):
        import shapely.wkt

        from mapbox_vector_tile import encode

        collection = shapely.wkt.loads(
            """GEOMETRYCOLLECTION (GEOMETRYCOLLECTION (POINT (4095 3664), LINESTRING (2889 0, 2889 0)),
POINT (4095 3664), LINESTRING (2889 0, 2912 158, 3757 1700, 3732 1999, 4095 3277))"""
        )
        with self.assertRaises(ValueError):
            encode({"name": "streets", "features": [{"geometry": collection}]})

    def test_quantize_makes_mutlipolygon_invalid(self):
        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid

        shape = shapely.wkt.loads(
            """MULTIPOLYGON (((656510.8206577231 5674684.979891453, 656511.16 5674685.9, """
            """656514.1758819892 5674684.979891453, 656510.8206577231 5674684.979891453)), """
            """((657115.9120547654 5674684.979891453, 657118.85 5674690, 657118.0689111941 5674684.979891453, """
            """657115.9120547654 5674684.979891453)))"""
        )
        quantize_bounds = (645740.0149532147, 5674684.979891453, 665307.8941942193, 5694252.8591324575)
        features = [dict(geometry=shape, properties={})]
        pbf = encode(
            {"name": "foo", "features": features},
            quantize_bounds=quantize_bounds,
            on_invalid_geometry=on_invalid_geometry_make_valid,
        )
        result = decode(pbf)
        features = result["foo"]["features"]
        self.assertEqual(1, len(features))

    def test_flipped_geometry_produces_multipolygon(self):
        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid

        shape = shapely.wkt.loads(
            """POLYGON ((3449 1939, 3476 1967, 3473 1996, 3483 2027, 3542 2119, 3538 2160, 3563 2233, 3602 2255, """
            """3639 2326, 3629 2388, 3573 2455, 3594 2493, 3558 2533, 3573 2549, 3518 2572, 3502 2592, 3505 2607, """
            """3513 2614, 3535 2616, 3537 2610, 3535 2602, 3537 2599, 3548 2607, 3551 2636, 3528 2634, 3537 2668, """
            """3549 2670, 3528 2711, 3550 2667, 3532 2635, 3550 2641, 3553 2613, 3549 2602, 3540 2596, 3512 2610, """
            """3506 2589, 3576 2552, 3576 2543, 3563 2535, 3596 2506, 3597 2494, 3587 2469, 3589 2451, 3636 2385, """
            """3644 2326, 3605 2251, 3566 2230, 3547 2122, 3482 2014, 3479 1966, 3455 1944, 3458 1910, 3449 1902, """
            """3449 1939))"""
        )
        features = [dict(geometry=shape, properties={})]
        pbf = encode({"name": "foo", "features": features}, on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        features = result["foo"]["features"]
        self.assertEqual(1, len(features))
        geom = shapely.geometry.shape(features[0]["geometry"])
        self.assertEqual(features[0]["geometry"]["type"], "MultiPolygon")
        self.assertEqual(geom.geom_type, "MultiPolygon")
        self.assertTrue(geom.is_valid)
        for poly in geom.geoms:
            self.assertTrue(poly.is_valid)

    def test_make_valid_can_return_multipolygon(self):
        import os.path

        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid

        test_dir = os.path.dirname(os.path.realpath(__file__))
        file_name = "error_nested_multipolygon.wkt"

        with open(os.path.join(test_dir, file_name)) as fh:
            shape = wkt.loads(fh.read())

        features = [dict(geometry=shape, properties={})]
        pbf = encode(
            {"name": "foo", "features": features},
            quantize_bounds=(-10018754.1713946, 11271098.44281893, -8766409.899970269, 12523442.714243261),
            on_invalid_geometry=on_invalid_geometry_make_valid,
        )
        result = decode(pbf)
        features = result["foo"]["features"]
        self.assertEqual(1, len(features))
        geom = features[0]["geometry"]
        self.assertEqual(geom["type"], "MultiPolygon")
        multipolygon = shapely.geometry.shape(geom)
        self.assertTrue(multipolygon.is_valid)

        area = 0
        for p in multipolygon.geoms:
            self.assertTrue(p.is_valid)
            area += p.area
        self.assertEqual(4339852.5, area)

    def test_too_small_geometry(self):
        import shapely.wkt

        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid

        shape = shapely.wkt.loads(
            "LINESTRING (3065.656210384849 3629.831662879646, 3066.458953567231 3629.725941289478)"
        )
        features = [dict(geometry=shape, properties={})]
        pbf = encode({"name": "foo", "features": features}, on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        features = result["foo"]["features"]
        self.assertEqual(0, len(features))


class LowLevelEncodingTestCase(unittest.TestCase):
    def test_example_multi_polygon(self):
        from mapbox_vector_tile.encoder import VectorTile

        # example from spec:
        # https://github.com/mapbox/vector-tile-spec/tree/master/2.1#4356-example-multi-polygon  ()
        # note that examples are in **tile local coordinates** which are
        # y-down.
        input_geometry = (
            "MULTIPOLYGON ("
            + "((0 0, 10 0, 10 10, 0 10, 0 0)),"
            + "((11 11, 20 11, 20 20, 11 20, 11 11),"
            + " (13 13, 13 17, 17 17, 17 13, 13 13)))"
        )
        expected_commands = [
            9,  # 1 x move to
            0,
            0,  # ........... +0,+0
            26,  # 3 x line to
            20,
            0,  # ........... +10,+0
            0,
            20,  # ........... +0,+10
            19,
            0,  # ........... -10,+0
            15,  # 1 x close path
            9,  # 1 x move to
            22,
            2,  # ........... +11,+1
            26,  # 3 x line to
            18,
            0,  # ........... +9,+0
            0,
            18,  # ........... +0,+9
            17,
            0,  # ........... -9,+0
            15,  # 1 x close path
            9,  # 1 x move to
            4,
            13,  # ........... +2,-7
            26,  # 3 x line to
            0,
            8,  # ........... +0,+4
            8,
            0,  # ........... +4,+0
            0,
            7,  # ........... +0,-4
            15,  # 1 x close path
        ]

        tile = VectorTile(4096)
        tile.addFeatures([dict(geometry=input_geometry)], "example_layer", quantize_bounds=None, y_coord_down=True)
        self.assertEqual(1, len(tile.layer.features))
        f = tile.layer.features[0]
        self.assertEqual(expected_commands, list(f.geometry))

    def test_example_multi_polygon_y_up(self):
        from mapbox_vector_tile.encoder import VectorTile

        # example from spec:
        # https://github.com/mapbox/vector-tile-spec/tree/master/2.1#4356-example-multi-polygon
        # in this example, we transform the coordinates to their equivalents
        # in a y-up coordinate system.
        input_geometry = (
            "MULTIPOLYGON ("
            + "((0 20, 10 20, 10 10, 0 10, 0 20)),"
            + "((11 9, 20 9, 20 0, 11 0, 11 9),"
            + " (13 7, 13 3, 17 3, 17 7, 13 7)))"
        )
        expected_commands = [
            9,  # 1 x move to
            0,
            0,  # ........... +0,+0
            26,  # 3 x line to
            20,
            0,  # ........... +10,+0
            0,
            20,  # ........... +0,+10
            19,
            0,  # ........... -10,+0
            15,  # 1 x close path
            9,  # 1 x move to
            22,
            2,  # ........... +11,+1
            26,  # 3 x line to
            18,
            0,  # ........... +9,+0
            0,
            18,  # ........... +0,+9
            17,
            0,  # ........... -9,+0
            15,  # 1 x close path
            9,  # 1 x move to
            4,
            13,  # ........... +2,-7
            26,  # 3 x line to
            0,
            8,  # ........... +0,+4
            8,
            0,  # ........... +4,+0
            0,
            7,  # ........... +0,-4
            15,  # 1 x close path
        ]

        tile = VectorTile(20)
        tile.addFeatures([dict(geometry=input_geometry)], "example_layer", quantize_bounds=None, y_coord_down=False)
        self.assertEqual(1, len(tile.layer.features))
        f = tile.layer.features[0]
        self.assertEqual(expected_commands, list(f.geometry))

    def test_issue_57(self):
        from mapbox_vector_tile.encoder import VectorTile

        # example from issue:
        # https://github.com/tilezen/mapbox-vector-tile/issues/57
        input_geometry = "POLYGON ((2 2, 5 4, 2 6, 2 2))"
        expected_commands = [
            9,  # 1 x move to
            4,
            4,  # ........... +2,+2
            18,  # 2 x line to
            6,
            4,  # ........... +3,+2
            5,
            4,  # ........... -3,+2
            15,  # 1 x close path
        ]

        tile = VectorTile(4096)
        tile.addFeatures([dict(geometry=input_geometry)], "example_layer", quantize_bounds=None, y_coord_down=True)
        self.assertEqual(1, len(tile.layer.features))
        f = tile.layer.features[0]
        self.assertEqual(expected_commands, list(f.geometry))
