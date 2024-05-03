"""
Tests for vector_tile/polygon.py
"""

import unittest
from pathlib import Path

from shapely import wkt

from mapbox_vector_tile.polygon import make_it_valid


class TestPolygonMakeValid(unittest.TestCase):
    def test_dev_errors(self):
        test_dir = Path(__file__).resolve().parent
        with (test_dir / "errors.wkt").open() as fh:
            for line in fh:
                geom = wkt.loads(line)
                fixed = make_it_valid(geom)
                self.assertTrue(fixed.is_valid)
                self.assertTrue(fixed.area > 0.9 * abs(geom.area))

    def test_multipolygon_with_flipped_ring(self):
        geom = wkt.loads(
            """MULTIPOLYGON(
          ((0 0, 0 4, 4 4, 4 0, 0 0), (1 1, 1 3, 3 3, 3 1, 1 1)),
          ((5 0, 9 0, 9 4, 5 4, 5 0), (6 1, 6 3, 8 3, 8 1, 6 1))
        )"""
        )
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(24, fixed.area)

    def test_polygon_self_touching(self):
        geom = wkt.loads(
            """POLYGON(
          (1 0, 5 0, 5 5, 0 5, 0 2, 2 2, 2 4, 3 4, 1 0)
        )"""
        )
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(21, fixed.area)

    def test_polygon_self_touching_inner(self):
        geom = wkt.loads(
            """POLYGON(
          (-1 -1, -1 6, 6 6, 6 -1, -1 -1),
          (1 0, 5 0, 5 5, 0 5, 0 2, 2 2, 2 4, 3 4, 1 0)
        )"""
        )
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(28, fixed.area)

    def test_polygon_inners_touching(self):
        geom = wkt.loads(
            """POLYGON(
          (0 0, 6 0, 6 6, 0 6, 0 0),
          (1 1, 1 3, 3 3, 3 1, 1 1),
          (3 3, 3 5, 5 5, 5 3, 3 3)
        )"""
        )
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(28, fixed.area)

    def test_polygon_inner_touching_outer(self):
        geom = wkt.loads(
            """POLYGON(
          (0 0, 3 0, 3 3, 0 3, 0 0),
          (1 1, 2 3, 2 1, 1 1)
        )"""
        )
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(8, fixed.area)

    def test_polygon_two_inners_touching_outer(self):
        geom = wkt.loads(
            """POLYGON(
          (0 0, 6 0, 6 3, 0 3, 0 0),
          (1 1, 2 3, 2 1, 1 1),
          (4 1, 5 3, 5 1, 4 1)
        )"""
        )
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(16, fixed.area)

    def test_polygon_inners_touching_colinear(self):
        geom = wkt.loads(
            """POLYGON(
          (0 0, 6 0, 6 6, 0 6, 0 0),
          (1 1, 1 3, 3 4, 3 1, 1 1),
          (3 2, 3 5, 5 5, 5 3, 3 2)
        )"""
        )
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(26, fixed.area)

    def test_polygon_inner_colinear_outer(self):
        geom = wkt.loads(
            """POLYGON(
          (0 0, 3 0, 3 3, 0 3, 0 0),
          (1 1, 1 3, 2 3, 2 1, 1 1)
        )"""
        )
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(7, fixed.area)

    def test_polygon_many_inners_touching(self):
        geom = wkt.loads(
            """POLYGON(
          (0 0, 5 0, 5 5, 0 5, 0 0),
          (1 1, 1 2, 3 2, 1 1),
          (3 1, 3 3, 4 1, 3 1),
          (2 2, 1 4, 2 4, 2 2),
          (2 3, 4 4, 4 3, 2 3)
        )"""
        )
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(21, fixed.area)

    def test_polygon_inner_spike(self):
        geom = wkt.loads(
            """POLYGON(
          (0 0, 3 0, 3 4, 0 4, 0 0),
          (1 1, 1 3, 2 3, 2 2, 1 2, 2 2, 2 1, 1 1)
        )"""
        )
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(10, fixed.area)

    def test_polygon_disconnected_inner(self):
        geom = wkt.loads(
            """POLYGON(
          (0 0, 5 0, 5 5, 0 5, 0 0),
          (1 1, 1 2, 2 2, 1 1),
          (2 1, 2 2, 3 2, 2 1),
          (3 1, 3 2, 4 2, 3 1),
          (1 2, 1 3, 2 3, 1 2),
          (2 2, 2 3, 3 3, 2 2),
          (3 2, 3 3, 4 3, 3 2),
          (1 3, 1 4, 2 4, 1 3),
          (2 3, 2 4, 3 4, 2 3),
          (3 3, 3 4, 4 4, 3 3)
        )"""
        )
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(20.5, fixed.area)

    def test_polygon_disconnected_outer(self):
        geom = wkt.loads(
            """POLYGON(
          (0 0, 4 0, 4 3, 3 3, 3 2, 2 3, 1 2, 1 3, 0 3, 0 0),
          (1 1, 1 2, 3 2, 3 1, 1 1)
        )"""
        )
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(9, fixed.area)

    def test_polygon_ring_of_inners(self):
        geom = wkt.loads(
            """POLYGON(
          (0 0, 4 0, 4 4, 0 4, 0 0),
          (1 1, 1 2, 2 1, 1 1),
          (1 2, 1 3, 2 3, 1 2),
          (2 3, 3 3, 3 2, 2 3),
          (2 1, 3 2, 3 1, 2 1)
        )"""
        )
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(14, fixed.area)

    def test_polygon_ring_of_inners_2(self):
        geom = wkt.loads(
            """POLYGON(
          (0 0, 5 0, 5 5, 0 5, 0 0),
          (1 3, 1 4, 2 4, 1 3),
          (3 3, 4 3, 4 2, 3 3),
          (1 1, 1 2, 2 1, 1 1),
          (1 2, 1 3, 2 3, 1 2),
          (2 3, 3 3, 3 2, 2 3),
          (2 1, 3 2, 3 1, 2 1)
        )"""
        )
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEqual(22, fixed.area)

    def test_polygon_inners_crossing_outer(self):
        geom = wkt.loads(
            """POLYGON (
          (2325 1015, 2329 1021, 2419 1057, 2461 944, 2369 907, 2325 1015),
          (2329 1012, 2370 909, 2457 944, 2417 1050, 2329 1012),
          (2410 1053, 2410 1052, 2412 1053, 2411 1054, 2410 1053),
          (2378 1040, 2378 1039, 2379 1040, 2379 1041, 2378 1040),
          (2369 1037, 2370 1036, 2371 1036, 2371 1038, 2369 1037),
          (2361 1034, 2362 1033, 2363 1033, 2363 1034, 2361 1034),
          (2353 1031, 2354 1029, 2355 1030, 2354 1031, 2353 1031),
          (2337 1024, 2338 1023, 2339 1023, 2338 1025, 2337 1024)
        )"""
        )
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        # different versions of GEOS hit this bug in slightly different ways,
        # meaning that some inners get included and some don't, depending on
        # the version. therefore, we need quite a wide range of acceptable
        # answers.
        #
        # the main part of this polygon (outer - largest inner) has area 1551,
        # and the smaller inners sum up to area 11, so we'll take +/-6 from
        # 1545.
        self.assertAlmostEqual(1545, fixed.area, delta=6)
