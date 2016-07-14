# -*- coding: utf-8 -*-
"""
Tests for vector_tile/encoder.py
"""
import unittest

import mapbox_vector_tile
from mapbox_vector_tile import encode, decode
from mapbox_vector_tile.compat import PY3
from past.builtins import long, unicode

from shapely import wkt


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.layer_name = "water"
        self.feature_properties = {
            "uid": 123,
            "foo": "bar",
            "baz": "foo"
        }
        self.feature_geometry = 'POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))'

    def assertRoundTrip(self, input_geometry, expected_geometry, name=None,
                        properties=None, id=None, expected_len=1,
                        expected_properties=None):
        if input_geometry is None:
            input_geometry = self.feature_geometry
        if name is None:
            name = self.layer_name
        if properties is None:
            properties = self.feature_properties
        if expected_properties is None:
            expected_properties = properties
        source = [{
            "name": name,
            "features": [{
                "geometry": input_geometry,
                "properties": properties
            }]
        }]
        if id:
            source[0]['features'][0]['id'] = id
        encoded = encode(source)
        decoded = decode(encoded)
        self.assertIn(name, decoded)
        layer = decoded[name]
        features = layer['features']
        self.assertEqual(expected_len, len(features))
        self.assertEqual(features[0]['properties'], expected_properties)
        self.assertEqual(features[0]['geometry'], expected_geometry)
        if id:
            self.assertEqual(features[0]['id'], id)


class TestDifferentGeomFormats(BaseTestCase):

    def test_encoder(self):
        self.assertRoundTrip(
            input_geometry='POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))',
            expected_geometry=[[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]])

    def test_encoder_quantize_before_orient(self):
        self.assertRoundTrip(
            input_geometry='POLYGON ((0 0, 4 0, 4 4, 0 4, 0 0), (1 1, 3 2, 2 2, 1 1))',  # noqa
            expected_geometry=[[[0, 0], [0, 4], [4, 4], [4, 0], [0, 0]],
                               [[1, 1], [3, 2], [2, 2], [1, 1]]])

    def test_encoder_winding_order_polygon(self):
        # example from the spec
        # https://github.com/mapbox/vector-tile-spec/tree/master/2.1#4355-example-polygon
        # the order given in the example is clockwise in a y-up coordinate
        # system, but the coordinate system given for the example is y-down!
        # therefore the y coordinate in this example is flipped negative.
        self.assertRoundTrip(
            input_geometry='POLYGON ((3 -6, 8 -12, 20 -34, 3 -6))',
            expected_geometry=[[[3, -6], [8, -12], [20, -34], [3, -6]]])

    def test_encoder_winding_order_polygon_reverse(self):
        # tests that encode _corrects_ the winding order
        # example is the same as above - note the flipped coordinate system.
        self.assertRoundTrip(
            input_geometry='POLYGON ((3 -6, 20 -34, 8 -12, 3 -6))',
            expected_geometry=[[[3, -6], [8, -12], [20, -34], [3, -6]]])

    def test_encoder_winding_order_multipolygon(self):
        # example from the spec
        # https://github.com/mapbox/vector-tile-spec/tree/master/2.1#4356-example-multi-polygon
        # the order given in the example is clockwise in a y-up coordinate
        # system, but the coordinate system given for the example is y-down!
        self.assertRoundTrip(
            input_geometry=('MULTIPOLYGON (' +
                            '((0 0, 10 0, 10 -10, 0 -10, 0 0)),' +
                            '((11 -11, 20 -11, 20 -20, 11 -20, 11 -11),' +
                            ' (13 -13, 13 -17, 17 -17, 17 -13, 13 -13)))'),
            expected_geometry=[
                [[[0, 0], [10, 0], [10, -10], [0, -10], [0, 0]]],
                [[[11, -11], [20, -11], [20, -20], [11, -20], [11, -11]],
                 [[13, -13], [13, -17], [17, -17], [17, -13], [13, -13]]]])

    def test_encoder_ensure_winding_after_quantization(self):
        self.assertRoundTrip(
            input_geometry='POLYGON ((0 0, 4 0, 4 4, 0 4, 0 0), (1 1, 3 2.4, 2 1.6, 1 1))',  # noqa
            # should be single polygon with hole
            expected_geometry=[[[0, 0], [0, 4], [4, 4], [4, 0], [0, 0]],
                               [[1, 1], [3, 2], [2, 2], [1, 1]]])
        # but becomes multi-polygon
        # expected_geometry=[[[[0, 0], [0, 4], [4, 4], [4, 0], [0, 0]]],
        #                   [[[1, 1], [2, 2], [3, 2], [1, 1]]]])

    def test_with_wkt(self):
        self.assertRoundTrip(
            input_geometry="LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)",  # noqa
            expected_geometry=[[-71, 42], [-71, 42], [-71, 42]])

    def test_with_wkb(self):
        self.assertRoundTrip(
            input_geometry=b"\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000",  # noqa
            expected_geometry=[[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]])

    def test_with_shapely(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa
        geometry = wkt.loads(geometry)
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[-71, 42], [-71, 42], [-71, 42]])

    def test_with_invalid_geometry(self):
        expected_result = ('Can\'t do geometries that are not wkt, wkb, or '
                           'shapely geometries')
        with self.assertRaises(NotImplementedError) as ex:
            mapbox_vector_tile.encode([{
                "name": self.layer_name,
                "features": [{
                    "geometry": "xyz",
                    "properties": self.feature_properties
                }]
            }])
        self.assertEqual(str(ex.exception), expected_result)

    def test_encode_unicode_property(self):
        if PY3:
            func = str
        else:
            func = unicode
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa
        properties = {
            "foo": func(self.feature_properties["foo"]),
            "baz": func(self.feature_properties["baz"]),
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[-71, 42], [-71, 42], [-71, 42]],
            properties=properties)

    def test_encode_unicode_property_key(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa
        properties = {
            u'☺': u'☺'
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[-71, 42], [-71, 42], [-71, 42]],
            properties=properties)

    def test_encode_float_little_endian(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa
        properties = {
            'floatval': 3.14159
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[-71, 42], [-71, 42], [-71, 42]],
            properties=properties)

    def test_encode_feature_with_id(self):
        geometry = 'POINT(1 1)'
        self.assertRoundTrip(input_geometry=geometry,
                             expected_geometry=[[1, 1]], id=42)

    def test_encode_polygon_reverse_winding_order(self):
        geometry = 'POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))'
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]])

    def test_encode_multilinestring(self):
        geometry = 'MULTILINESTRING ((10 10, 20 20, 10 40), (40 40, 30 30, 40 20, 30 10))'  # noqa
        self.assertRoundTrip(input_geometry=geometry,
                             expected_geometry=[
                                 [[10, 10], [20, 20], [10, 40]],
                                 [[40, 40], [30, 30], [40, 20], [30, 10]],
                             ])

    def test_encode_multipolygon_normal_winding_order(self):
        geometry = 'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))'  # noqa
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[
                [[[40, 40], [45, 30], [20, 45], [40, 40]]],
                [[[20, 35], [45, 20], [30, 5], [10, 10], [10, 30], [20, 35]],
                 [[30, 20], [20, 25], [20, 15], [30, 20]]],
            ],
            expected_len=1)

    def test_encode_multipolygon_normal_winding_order_zero_area(self):
        geometry = 'MULTIPOLYGON (((40 40, 40 20, 40 45, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))'  # noqa
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[
                [[20, 35], [45, 20], [30, 5], [10, 10], [10, 30], [20, 35]],
                [[30, 20], [20, 25], [20, 15], [30, 20]],
            ],
            expected_len=1)

    def test_encode_multipolygon_reverse_winding_order(self):
        geometry = 'MULTIPOLYGON (((10 10, 10 0, 0 0, 0 10, 10 10), (8 8, 2 8, 2 0, 8 0, 8 8)))'  # noqa
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[
                [[10, 10], [10, 0], [0, 0], [0, 10], [10, 10]],
                [[8, 8], [2, 8], [2, 0], [8, 0], [8, 8]],
            ],
            expected_len=1)

    def test_encode_property_bool(self):
        geometry = 'POINT(0 0)'
        properties = {
            'test_bool_true': True,
            'test_bool_false': False
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[0, 0]],
            properties=properties)

    def test_encode_property_long(self):
        geometry = 'POINT(0 0)'
        properties = {
            'test_int': int(1),
            'test_long': long(1)
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[0, 0]],
            properties=properties)

    def test_encode_property_null(self):
        geometry = 'POINT(0 0)'
        properties = {
            'test_none': None,
            'test_empty': ""
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[0, 0]],
            properties=properties,
            expected_properties={'test_empty': ''})

    def test_encode_property_list(self):
        geometry = 'POINT(0 0)'
        properties = {
            'test_list': [1, 2, 3],
            'test_empty': ""
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[0, 0]],
            properties=properties,
            expected_properties={'test_empty': ''})

    def test_encode_multiple_values_test(self):
        geometry = 'POINT(0 0)'
        properties1 = dict(foo='bar', baz='bar')
        properties2 = dict(quux='morx', baz='bar')
        name = 'foo'
        feature1 = dict(geometry=geometry, properties=properties1)
        feature2 = dict(geometry=geometry, properties=properties2)
        source = [{
            "name": name,
            "features": [feature1, feature2]
        }]
        encoded = encode(source)
        decoded = decode(encoded)
        self.assertIn(name, decoded)
        layer = decoded[name]
        features = layer['features']
        self.assertEqual(2, len(features))
        self.assertEqual(features[0]['properties'], properties1)
        self.assertEqual(features[1]['properties'], properties2)

    def test_encode_rounding_floats(self):
        geometry = 'LINESTRING(1.1 1.1, 41.5 41.8)'
        exp_geoemtry = [[1, 1], [42, 42]]
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=exp_geoemtry,
        )


class QuantizeTest(unittest.TestCase):

    def test_quantize(self):
        from mapbox_vector_tile import decode
        from mapbox_vector_tile import encode
        props = dict(foo='bar')
        shape = 'POINT(15 15)'
        feature = dict(geometry=shape, properties=props)
        features = [feature]
        source = dict(name='layername', features=features)
        bounds = 10.0, 10.0, 20.0, 20.0
        pbf = encode(source, quantize_bounds=bounds)
        result = decode(pbf)
        act_feature = result['layername']['features'][0]
        act_geom = act_feature['geometry']
        exp_geom = [[2048, 2048]]
        self.assertEqual(exp_geom, act_geom)

    def test_y_coord_down(self):
        from mapbox_vector_tile import decode
        from mapbox_vector_tile import encode
        props = dict(foo='bar')
        shape = 'POINT(10 10)'
        feature = dict(geometry=shape, properties=props)
        features = [feature]
        source = dict(name='layername', features=features)
        pbf = encode(source, y_coord_down=True)
        result = decode(pbf, y_coord_down=True)
        act_feature = result['layername']['features'][0]
        act_geom = act_feature['geometry']
        exp_geom = [[10, 10]]
        self.assertEqual(exp_geom, act_geom)

    def test_quantize_and_y_coord_down(self):
        from mapbox_vector_tile import decode
        from mapbox_vector_tile import encode
        props = dict(foo='bar')
        shape = 'POINT(30 30)'
        feature = dict(geometry=shape, properties=props)
        features = [feature]
        source = dict(name='layername', features=features)
        bounds = 0.0, 0.0, 50.0, 50.0
        pbf = encode(source, quantize_bounds=bounds, y_coord_down=True)

        result_decode_no_flip = decode(pbf, y_coord_down=True)
        act_feature = result_decode_no_flip['layername']['features'][0]
        act_geom = act_feature['geometry']
        exp_geom = [[2458, 2458]]
        self.assertEqual(exp_geom, act_geom)

        result_decode_flip = decode(pbf)
        act_feature = result_decode_flip['layername']['features'][0]
        act_geom = act_feature['geometry']
        exp_geom = [[2458, 1638]]
        self.assertEqual(exp_geom, act_geom)


class ExtentTest(unittest.TestCase):

    def test_custom_extent(self):
        from mapbox_vector_tile import decode
        from mapbox_vector_tile import encode
        props = dict(foo='bar')
        shape = 'POINT(10 10)'
        feature = dict(geometry=shape, properties=props)
        features = [feature]
        source = dict(name='layername', features=features)
        bounds = 0.0, 0.0, 10.0, 10.0
        pbf = encode(source, quantize_bounds=bounds, extents=50)
        result = decode(pbf)
        act_feature = result['layername']['features'][0]
        act_geom = act_feature['geometry']
        exp_geom = [[50, 50]]
        self.assertEqual(exp_geom, act_geom)


class RoundTest(unittest.TestCase):

    def test_custom_rounding_function(self):
        from mapbox_vector_tile import decode
        from mapbox_vector_tile import encode
        props = dict(foo='bar')
        shape = 'POINT(10 10)'
        feature = dict(geometry=shape, properties=props)
        features = [feature]
        source = dict(name='layername', features=features)
        bounds = 0.0, 0.0, 10.0, 10.0
        # A really bad, custom "rounding" function
        pbf = encode(source, quantize_bounds=bounds, round_fn=lambda x: 5)
        result = decode(pbf)

        act_feature = result['layername']['features'][0]
        act_geom = act_feature['geometry']
        exp_geom = [[5, 5]]
        self.assertEqual(exp_geom, act_geom)


class InvalidGeometryTest(unittest.TestCase):

    def test_invalid_geometry_ignore(self):
        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_ignore
        import shapely.wkt
        geometry = 'POLYGON ((10 10, 20 10, 20 20, 15 15, 15 5, 10 10))'
        shape = shapely.wkt.loads(geometry)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name='layername', features=[feature])
        pbf = encode(source, on_invalid_geometry=on_invalid_geometry_ignore)
        result = decode(pbf)
        self.assertEqual(0, len(result['layername']['features']))

    def test_invalid_geometry_raise(self):
        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_raise
        import shapely.wkt
        geometry = 'POLYGON ((10 10, 20 10, 20 20, 15 15, 15 5, 10 10))'
        shape = shapely.wkt.loads(geometry)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name='layername', features=[feature])
        with self.assertRaises(Exception):
            encode(source, on_invalid_geometry=on_invalid_geometry_raise)

    def test_invalid_geometry_make_valid(self):
        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid
        import shapely.geometry
        import shapely.wkt
        geometry = 'POLYGON ((10 10, 20 10, 20 20, 15 15, 15 5, 10 10))'
        shape = shapely.wkt.loads(geometry)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name='layername', features=[feature])
        pbf = encode(source,
                     on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        self.assertEqual(1, len(result['layername']['features']))
        valid_geometry = result['layername']['features'][0]['geometry']
        shape = shapely.geometry.Polygon(valid_geometry[0])
        self.assertTrue(shape.is_valid)

    def test_bowtie(self):
        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid
        import shapely.geometry
        import shapely.wkt
        bowtie = ('POLYGON ((0 0, 0 2, 1 1, 2 2, 2 0, 1 1, 0 0))')
        shape = shapely.wkt.loads(bowtie)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name='layername', features=[feature])
        pbf = encode(source,
                     on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        self.assertEqual(1, len(result['layername']['features']))
        valid_geometries = result['layername']['features'][0]['geometry']
        self.assertEqual(2, len(valid_geometries))
        shape1, shape2 = [shapely.geometry.Polygon(x[0])
                          for x in valid_geometries]
        self.assertTrue(shape1.is_valid)
        self.assertTrue(shape2.is_valid)
        self.assertGreater(shape1.area, 0)
        self.assertGreater(shape2.area, 0)

    def test_validate_generates_rounding_error(self):
        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid
        import shapely.geometry
        import shapely.wkt
        bowtie = ('POLYGON((0 0, 1 1, 0 1, 1 0, 0 0))')
        shape = shapely.wkt.loads(bowtie)
        self.assertFalse(shape.is_valid)
        feature = dict(geometry=shape, properties={})
        source = dict(name='layername', features=[feature])
        pbf = encode(source,
                     on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        features = result['layername']['features']
        self.assertEqual(1, len(features))
        shape = shapely.geometry.Polygon(features[0]['geometry'][0])
        self.assertTrue(shape.is_valid)
        self.assertGreater(shape.area, 0)

    def test_geometry_collection_raises(self):
        from mapbox_vector_tile import encode
        import shapely.wkt
        collection = shapely.wkt.loads('GEOMETRYCOLLECTION (GEOMETRYCOLLECTION (POINT (4095 3664), LINESTRING (2889 0, 2889 0)), POINT (4095 3664), LINESTRING (2889 0, 2912 158, 3757 1700, 3732 1999, 4095 3277))')  # noqa
        with self.assertRaises(ValueError):
            encode({'name': 'streets', 'features': [{'geometry': collection}]})

    def test_quantize_makes_mutlipolygon_invalid(self):
        from mapbox_vector_tile import encode
        from mapbox_vector_tile.encoder import on_invalid_geometry_make_valid
        import shapely.wkt
        shape = shapely.wkt.loads('MULTIPOLYGON (((656510.8206577231 5674684.979891453, 656511.16 5674685.9, 656514.1758819892 5674684.979891453, 656510.8206577231 5674684.979891453)), ((657115.9120547654 5674684.979891453, 657118.85 5674690, 657118.0689111941 5674684.979891453, 657115.9120547654 5674684.979891453)))')  # noqa
        quantize_bounds = (645740.0149532147, 5674684.979891453, 665307.8941942193, 5694252.8591324575)  # noqa
        features = [dict(geometry=shape, properties={})]
        pbf = encode({'name': 'foo', 'features': features},
                     quantize_bounds=quantize_bounds,
                     on_invalid_geometry=on_invalid_geometry_make_valid)
        result = decode(pbf)
        features = result['foo']['features']
        self.assertEqual(1, len(features))


class LowLevelEncodingTestCase(unittest.TestCase):
    def test_example_multi_polygon(self):
        from mapbox_vector_tile.encoder import VectorTile
        # example from spec:
        # https://github.com/mapbox/vector-tile-spec/tree/master/2.1#4356-example-multi-polygon
        # note that examples are in **tile local coordinates** which are
        # y-down.
        input_geometry = 'MULTIPOLYGON (' + \
                         '((0 0, 10 0, 10 10, 0 10, 0 0)),' + \
                         '((11 11, 20 11, 20 20, 11 20, 11 11),' + \
                         ' (13 13, 13 17, 17 17, 17 13, 13 13)))'
        expected_commands = [
            9,       # 1 x move to
            0,   0,  # ........... +0,+0
            26,      # 3 x line to
            20,  0,  # ........... +10,+0
            0,  20,  # ........... +0,+10
            19,  0,  # ........... -10,+0
            15,      # 1 x close path
            9,       # 1 x move to
            22,  2,  # ........... +11,+1
            26,      # 3 x line to
            18,  0,  # ........... +9,+0
            0,  18,  # ........... +0,+9
            17,  0,  # ........... -9,+0
            15,      # 1 x close path
            9,       # 1 x move to
            4,  13,  # ........... +2,-7
            26,      # 3 x line to
            0,   8,  # ........... +0,+4
            8,   0,  # ........... +4,+0
            0,   7,  # ........... +0,-4
            15       # 1 x close path
        ]

        tile = VectorTile(4096)
        tile.addFeatures([dict(geometry=input_geometry)],
                         'example_layer', quantize_bounds=None,
                         y_coord_down=True)
        self.assertEqual(1, len(tile.layer.features))
        f = tile.layer.features[0]
        self.assertEqual(expected_commands, list(f.geometry))

    def test_example_multi_polygon_y_up(self):
        from mapbox_vector_tile.encoder import VectorTile
        # example from spec:
        # https://github.com/mapbox/vector-tile-spec/tree/master/2.1#4356-example-multi-polygon
        # in this example, we transform the coordinates to their equivalents
        # in a y-up coordinate system.
        input_geometry = 'MULTIPOLYGON (' + \
                         '((0 20, 10 20, 10 10, 0 10, 0 20)),' + \
                         '((11 9, 20 9, 20 0, 11 0, 11 9),' + \
                         ' (13 7, 13 3, 17 3, 17 7, 13 7)))'
        expected_commands = [
            9,       # 1 x move to
            0,   0,  # ........... +0,+0
            26,      # 3 x line to
            20,  0,  # ........... +10,+0
            0,  20,  # ........... +0,+10
            19,  0,  # ........... -10,+0
            15,      # 1 x close path
            9,       # 1 x move to
            22,  2,  # ........... +11,+1
            26,      # 3 x line to
            18,  0,  # ........... +9,+0
            0,  18,  # ........... +0,+9
            17,  0,  # ........... -9,+0
            15,      # 1 x close path
            9,       # 1 x move to
            4,  13,  # ........... +2,-7
            26,      # 3 x line to
            0,   8,  # ........... +0,+4
            8,   0,  # ........... +4,+0
            0,   7,  # ........... +0,-4
            15       # 1 x close path
        ]

        tile = VectorTile(20)
        tile.addFeatures([dict(geometry=input_geometry)],
                         'example_layer', quantize_bounds=None,
                         y_coord_down=False)
        self.assertEqual(1, len(tile.layer.features))
        f = tile.layer.features[0]
        self.assertEqual(expected_commands, list(f.geometry))

    def test_issue_57(self):
        from mapbox_vector_tile.encoder import VectorTile
        # example from issue:
        # https://github.com/tilezen/mapbox-vector-tile/issues/57
        input_geometry = 'POLYGON ((2 2, 5 4, 2 6, 2 2))'
        expected_commands = [
            9,       # 1 x move to
            4,   4,  # ........... +2,+2
            18,      # 2 x line to
            6,   4,  # ........... +3,+2
            5,   4,  # ........... -3,+2
            15       # 1 x close path
        ]

        tile = VectorTile(4096)
        tile.addFeatures([dict(geometry=input_geometry)],
                         'example_layer', quantize_bounds=None,
                         y_coord_down=True)
        self.assertEqual(1, len(tile.layer.features))
        f = tile.layer.features[0]
        self.assertEqual(expected_commands, list(f.geometry))
