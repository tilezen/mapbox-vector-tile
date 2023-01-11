import unittest

import mapbox_vector_tile
from mapbox_vector_tile.Mapbox import vector_tile_pb2 as vector_tile
from mapbox_vector_tile.optimise import optimise_tile


class BaseTestCase(unittest.TestCase):
    def test_string_table_optimizer(self):
        tile_data = mapbox_vector_tile.encode(
            {
                "name": "water",
                "features": [
                    {"geometry": "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))", "properties": {"uid": 123, "foo": "bar"}},
                    {"geometry": "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))", "properties": {"uid": 124, "foo": "bar"}},
                    {
                        "geometry": "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))",
                        "properties": {"uid": 125, "cat": "flew", "foo": "bar"},
                    },
                ],
            }
        )
        # Check the tags in the encoded tile
        tile = vector_tile.tile()
        tile.ParseFromString(tile_data)
        tile_layer = tile.layers[0]
        expected_tile_tags = ([0, 0, 1, 1], [0, 2, 1, 1], [0, 3, 2, 4, 1, 1])
        for i, f in enumerate(tile_layer.features):
            self.assertEqual(f.tags, expected_tile_tags[i])

        # Optimise it
        result = optimise_tile(tile_data)

        # Check that the tags have been modified
        result_tile = vector_tile.tile()
        result_tile.ParseFromString(result)
        result_layer = result_tile.layers[0]
        expected_results = ([1, 4, 0, 0], [1, 3, 0, 0], [1, 2, 2, 1, 0, 0])
        for i, f in enumerate(result_layer.features):
            self.assertEqual(f.tags, expected_results[i])

    def test_optimise_linestring(self):
        # No particular optimization as only a linestring
        tile_data = mapbox_vector_tile.encode(
            {"name": "water", "features": [{"geometry": "LINESTRING (0 0, 0 1, 1 1, 1 0, 0 0)", "properties": {}}]}
        )
        result = optimise_tile(tile_data)
        self.assertEqual(tile_data, result)

        # Multilinestring to optimize
        tile_data = mapbox_vector_tile.encode(
            {
                "name": "water",
                "features": [
                    {"geometry": "MULTILINESTRING ((0 0, 0 1, 1 1), (2 2, 3 2), (1 1, 2 2))", "properties": {}}
                ],
            }
        )
        result = optimise_tile(tile_data)
        decoded_result = mapbox_vector_tile.decode(result)
        decoded_geometry = decoded_result["water"]["features"][0]["geometry"]
        self.assertEqual(decoded_geometry["type"], "MultiLineString")
        self.assertEqual(
            decoded_geometry["coordinates"], [[[0, 0], [0, 1], [1, 1]], [[1, 1], [2, 2]], [[2, 2], [3, 2]]]
        )
