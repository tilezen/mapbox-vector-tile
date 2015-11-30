# -*- coding: utf-8 -*-
"""
Tests for vector_tile/encoder.py
"""
import sys
import unittest

import mapbox_vector_tile
from mapbox_vector_tile import encode, decode

from shapely import wkt

PY3 = sys.version_info[0] == 3


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
            expected_geometry=[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]])

    def test_with_wkt(self):
        self.assertRoundTrip(
            input_geometry="LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)",  # noqa
            expected_geometry=[[-71, 43], [-71, 43], [-71, 43]])

    def test_with_wkb(self):
        self.assertRoundTrip(
            input_geometry=b"\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000",  # noqa
            expected_geometry=[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]])

    def test_with_shapely(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa
        geometry = wkt.loads(geometry)
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[-71, 43], [-71, 43], [-71, 43]])

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
            expected_geometry=[[-71, 43], [-71, 43], [-71, 43]],
            properties=properties)

    def test_encode_unicode_property_key(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa
        properties = {
            u'☺': u'☺'
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[-71, 43], [-71, 43], [-71, 43]],
            properties=properties)

    def test_encode_float_little_endian(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa
        properties = {
            'floatval': 3.14159
        }
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[-71, 43], [-71, 43], [-71, 43]],
            properties=properties)

    def test_encode_feature_with_id(self):
        geometry = 'POINT(1 1)'
        self.assertRoundTrip(input_geometry=geometry,
                             expected_geometry=[[1, 1]], id=42)

    def test_encode_polygon_reverse_winding_order(self):
        geometry = 'POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))'
        self.assertRoundTrip(
            input_geometry=geometry,
            expected_geometry=[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]])

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
                [[40, 40], [45, 30], [20, 45], [40, 40]],
                [[20, 35], [45, 20], [30,  5], [10, 10], [10, 30], [20, 35]],
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
