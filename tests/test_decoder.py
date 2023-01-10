"""
Tests for vector_tile/decoder.py
"""

import unittest

import mapbox_vector_tile
from mapbox_vector_tile.utils import DEFAULT_DECODE_OPTIONS, get_decode_options


class BaseTestCase(unittest.TestCase):
    def test_decoder(self):
        vector_tile = b'\x1aI\n\x05water\x12\x1a\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03baz\x1a\x03uid"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02'  # noqa
        self.assertEqual(
            mapbox_vector_tile.decode(vector_tile),
            {
                "water": {
                    "version": 2,
                    "extent": 4096,
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
                            "properties": {"foo": "bar", "baz": "foo", "uid": 123},
                            "id": 1,
                            "type": "Feature",
                        }
                    ],
                },
            },
        )

    def test_decoder_geojson(self):
        vector_tile = b'\x1aI\n\x05water\x12\x1a\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03baz\x1a\x03uid"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02'  # noqa
        self.assertEqual(
            mapbox_vector_tile.decode(vector_tile, default_options={"geojson": False}),
            {
                "water": {
                    "version": 2,
                    "extent": 4096,
                    "features": [
                        {
                            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
                            "properties": {"foo": "bar", "baz": "foo", "uid": 123},
                            "id": 1,
                            "type": 3,
                        }
                    ],
                },
            },
        )

    def test_decode_polygon_no_cmd_seg_end(self):
        # the binary here was generated without including the
        # CMD_SEG_END after the polygon parts
        # this tests that the decoder can detect that a new
        # CMD_MOVE_TO implicitly closes the previous polygon
        vector_tile = b'\x1a+\n\x05water\x12\x1d\x18\x03"\x19\t\x00\x80@"\x08\x00\x00\x07\x07\x00\x00\x08\t\x02\x01"\x00\x03\x04\x00\x00\x04\x03\x00(\x80 x\x02'  # noqa
        self.assertEqual(
            mapbox_vector_tile.decode(vector_tile),
            {
                "water": {
                    "version": 2,
                    "extent": 4096,
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]],
                                    [[1, 1], [1, 3], [3, 3], [3, 1], [1, 1]],
                                ],
                            },
                            "properties": {},
                            "id": 0,
                            "type": "Feature",
                        }
                    ],
                },
            },
        )

    def test_nondefault_extent(self):
        vector_tile = b'\x1aK\n\x05water\x12\x1c\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x02"\x0e\t\x80}\xd0\x12\x12\xbf>\xd86\xbf>\xd86\x1a\x03foo\x1a\x03baz\x1a\x03uid"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80@x\x02'  # noqa
        self.assertEqual(
            mapbox_vector_tile.decode(vector_tile),
            {
                "water": {
                    "version": 2,
                    "extent": 8192,
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "geometry": {"type": "LineString", "coordinates": [[8000, 7000], [4000, 3500], [0, 0]]},
                            "id": 1,
                            "properties": {"baz": "foo", "foo": "bar", "uid": 123},
                            "type": "Feature",
                        }
                    ],
                }
            },
        )

    def test_options(self):
        layer_options_1 = {"y_coord_down": True, "transformer": "my_function"}
        layer_options_2 = {"geojson": True}
        default_options = {"geojson": False}
        self.assertEqual(
            get_decode_options(layer_options=layer_options_1, default_options=default_options),
            {**layer_options_1, "geojson": False},
        )
        self.assertEqual(
            get_decode_options(layer_options=layer_options_2, default_options=default_options),
            {**layer_options_2, "y_coord_down": False, "transformer": None},
        )
        self.assertEqual(
            get_decode_options(layer_options=layer_options_2, default_options=None),
            {**layer_options_2, "y_coord_down": False, "transformer": None},
        )
        self.assertEqual(
            get_decode_options(layer_options=None, default_options=layer_options_1),
            {**layer_options_1, "geojson": True},
        )
        self.assertEqual(get_decode_options(layer_options=None, default_options=None), DEFAULT_DECODE_OPTIONS)

    def test_options_error(self):
        expected_result = "The following options are not allowed for decoding a tile: 'opt', 'unknown'."
        with self.assertRaises(ValueError) as ex:
            get_decode_options(layer_options={"geojson": False, "unknown": 23}, default_options={"opt": 42})
        self.assertEqual(str(ex.exception), expected_result)
