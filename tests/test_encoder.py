# -*- coding: utf-8 -*-
"""
Tests for vector_tile/encoder.py
"""

import unittest

import mapbox_vector_tile


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.layer_name = "water"
        self.feature_properties = {
            "uid":123,
            "foo":"bar",
            "baz":"foo"
        }
        self.feature_geometry = 'POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))'

    def test_encoder(self):
        expected_result = '\x1aI\n\x05water\x12\x1a\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03baz\x1a\x03uid"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02'
        self.assertEqual(mapbox_vector_tile.encode([{
                "name": self.layer_name,
                "features": [{
                    "geometry": self.feature_geometry,
                    "properties": self.feature_properties
                }]
            }]), expected_result)

class TestDifferentGeomFormats(unittest.TestCase):
    def setUp(self):
        self.layer_name = "water"
        self.feature_properties = {
            "uid":123,
            "foo":"bar",
            "baz":"foo"
        }
        self.feature_geometry = 'POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))'

    def test_with_wkt(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"
        expected_result = '\x1aG\n\x05water\x12\x18\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x02"\n\t\x8d\x01\xaa?\x12\x00\x00\x00\x00\x1a\x03foo\x1a\x03baz\x1a\x03uid"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02'
        self.assertEqual(mapbox_vector_tile.encode([{
                "name": self.layer_name,
                "features": [{
                    "geometry": geometry,
                    "properties": self.feature_properties
                }]
            }]), expected_result)

    def test_with_wkb(self):
        geometry = "\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000"
        expected_result = '\x1aI\n\x05water\x12\x1a\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03baz\x1a\x03uid"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02'
        self.assertEqual(mapbox_vector_tile.encode([{
                "name": self.layer_name,
                "features": [{
                    "geometry": geometry,
                    "properties": self.feature_properties
                }]
            }]), expected_result)

    def test_with_invalid_geometry(self):
        geometry = "xyz"
        expected_result = 'Can\'t do geometries that are not wkt or wkb'
        with self.assertRaises(NotImplementedError) as ex:
            mapbox_vector_tile.encode([{
                "name": self.layer_name,
                "features": [{
                    "geometry": geometry,
                    "properties": self.feature_properties
                }]
            }])
        self.assertEqual(ex.exception[0], expected_result)

    def test_encode_float_little_endian(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"
        expected_result = '\x1a^\n\x05water\x12\x1a\x08\x01\x12\x08\x00\x00\x01\x01\x02\x02\x03\x03\x18\x02"\n\t\x8d\x01\xaa?\x12\x00\x00\x00\x00\x1a\x08floatval\x1a\x03foo\x1a\x03baz\x1a\x03uid"\t\x19n\x86\x1b\xf0\xf9!\t@"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02'
        self.feature_properties['floatval'] = 3.14159
        self.assertEqual(mapbox_vector_tile.encode([{
                "name": self.layer_name,
                "features": [{
                    "geometry": geometry,
                    "properties": self.feature_properties
                }]
            }]), expected_result)
