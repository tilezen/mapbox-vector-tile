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
        expected_result = '\x1aG\n\x05water\x12\x18\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03baz\x1a\x03uid"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02'
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
        expected_result = '\x1aE\n\x05water\x12\x16\x12\x06\x00\x00\x01\x01\x02\x02\x18\x02"\n\t\x8d\x01\xaa?\x12\x00\x00\x00\x00\x1a\x03foo\x1a\x03baz\x1a\x03uid"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02'
        self.assertEqual(mapbox_vector_tile.encode([{
                "name": self.layer_name,
                "features": [{
                    "geometry": geometry,
                    "properties": self.feature_properties
                }]
            }]), expected_result)

    def test_with_wkb(self):
        geometry = "\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000"
        expected_result = '\x1aG\n\x05water\x12\x18\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03baz\x1a\x03uid"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02'
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

    def test_encode_unicode_property(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"
        self.feature_properties["foo"] = unicode(self.feature_properties["foo"])
        self.feature_properties["baz"] = unicode(self.feature_properties["baz"])
        expected_result = '\x1aE\n\x05water\x12\x16\x12\x06\x00\x00\x01\x01\x02\x02\x18\x02"\n\t\x8d\x01\xaa?\x12\x00\x00\x00\x00\x1a\x03foo\x1a\x03baz\x1a\x03uid"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02'
        self.assertEqual(mapbox_vector_tile.encode([{
                "name": self.layer_name,
                "features": [{
                    "geometry": geometry,
                    "properties": self.feature_properties
                }]
            }]), expected_result)

    def test_encode_float_little_endian(self):
        geometry = "LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"
        expected_result = '\x1a\\\n\x05water\x12\x18\x12\x08\x00\x00\x01\x01\x02\x02\x03\x03\x18\x02"\n\t\x8d\x01\xaa?\x12\x00\x00\x00\x00\x1a\x08floatval\x1a\x03foo\x1a\x03baz\x1a\x03uid"\t\x19n\x86\x1b\xf0\xf9!\t@"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02'
        self.feature_properties['floatval'] = 3.14159
        self.assertEqual(mapbox_vector_tile.encode([{
                "name": self.layer_name,
                "features": [{
                    "geometry": geometry,
                    "properties": self.feature_properties
                }]
            }]), expected_result)

    def test_encode_feature_with_id(self):
        geometry = 'POINT(1 1)'
        expected_result = '\x1a\x18\n\x05water\x12\n\x08*\x18\x01"\x04\t\x02\xfe?(\x80 x\x02'
        result = mapbox_vector_tile.encode([
            dict(name='water',
                 features=[dict(geometry=geometry, properties={}, id=42)])])
        self.assertEqual(expected_result, result)
        decoded = mapbox_vector_tile.decode(result)
        features = decoded['water']
        self.assertEqual(1, len(features))
        feature = features[0]
        self.assertEqual(42, feature['id'])

    def test_encode_multipolygon(self):
        geometry = 'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))'
        expected_result = '\x1a9\n\x05water\x12\x0e\x18\x03"\n\tP\xb0?\x12\'\t2\x1e\x0f\x12\x1b\x18\x03"\x17\t(\xba?"\x13\n\x00((\n\x1e\x1d\x0f\t\x1d\x00\x12\x13\n\x00\x13\x0f(\x80 x\x02'
        result = mapbox_vector_tile.encode([
            dict(name='water',
                 features=[dict(geometry=geometry, properties={})])])
        self.assertEqual(expected_result, result)

        decoded = mapbox_vector_tile.decode(result)
        features = decoded['water']
        self.assertEqual(2, len(features))
