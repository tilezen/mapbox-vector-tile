# -*- coding: utf-8 -*-
"""
Tests for vector_tile/polygon.py
"""
import unittest

from mapbox_vector_tile.polygon import make_it_valid
from shapely import wkt
import os


class TestPolygonMakeValid(unittest.TestCase):

    def test_dev_errors(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(test_dir, 'errors.wkt')) as fh:
            for line in fh:
                geom = wkt.loads(line)
                fixed = make_it_valid(geom)
                self.assertTrue(fixed.is_valid)
                self.assertTrue(fixed.area > 0.9 * abs(geom.area))

    def test_multipolygon_with_flipped_ring(self):
        geom = wkt.loads("""MULTIPOLYGON(
          ((0 0, 0 4, 4 4, 4 0, 0 0), (1 1, 1 3, 3 3, 3 1, 1 1)),
          ((5 0, 9 0, 9 4, 5 4, 5 0), (6 1, 6 3, 8 3, 8 1, 6 1))
        )""")
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(24, fixed.area)

    def test_polygon_self_touching(self):
        geom = wkt.loads("""POLYGON(
          (1 0, 5 0, 5 5, 0 5, 0 2, 2 2, 2 4, 3 4, 1 0)
        )""")
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(21, fixed.area)

    def test_polygon_self_touching_inner(self):
        geom = wkt.loads("""POLYGON(
          (-1 -1, -1 6, 6 6, 6 -1, -1 -1),
          (1 0, 5 0, 5 5, 0 5, 0 2, 2 2, 2 4, 3 4, 1 0)
        )""")
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(28, fixed.area)

    def test_polygon_inners_touching(self):
        geom = wkt.loads("""POLYGON(
          (0 0, 6 0, 6 6, 0 6, 0 0),
          (1 1, 1 3, 3 3, 3 1, 1 1),
          (3 3, 3 5, 5 5, 5 3, 3 3)
        )""")
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(28, fixed.area)

    def test_polygon_inner_touching_outer(self):
        geom = wkt.loads("""POLYGON(
          (0 0, 3 0, 3 3, 0 3, 0 0),
          (1 1, 2 3, 2 1, 1 1)
        )""")
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(8, fixed.area)

    def test_polygon_two_inners_touching_outer(self):
        geom = wkt.loads("""POLYGON(
          (0 0, 6 0, 6 3, 0 3, 0 0),
          (1 1, 2 3, 2 1, 1 1),
          (4 1, 5 3, 5 1, 4 1)
        )""")
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(16, fixed.area)

    def test_polygon_inners_touching_colinear(self):
        geom = wkt.loads("""POLYGON(
          (0 0, 6 0, 6 6, 0 6, 0 0),
          (1 1, 1 3, 3 4, 3 1, 1 1),
          (3 2, 3 5, 5 5, 5 3, 3 2)
        )""")
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(26, fixed.area)

    def test_polygon_inner_colinear_outer(self):
        geom = wkt.loads("""POLYGON(
          (0 0, 3 0, 3 3, 0 3, 0 0),
          (1 1, 1 3, 2 3, 2 1, 1 1)
        )""")
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(7, fixed.area)

    def test_polygon_many_inners_touching(self):
        geom = wkt.loads("""POLYGON(
          (0 0, 5 0, 5 5, 0 5, 0 0),
          (1 1, 1 2, 3 2, 1 1),
          (3 1, 3 3, 4 1, 3 1),
          (2 2, 1 4, 2 4, 2 2),
          (2 3, 4 4, 4 3, 2 3)
        )""")
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(21, fixed.area)

    def test_polygon_inner_spike(self):
        geom = wkt.loads("""POLYGON(
          (0 0, 3 0, 3 4, 0 4, 0 0),
          (1 1, 1 3, 2 3, 2 2, 1 2, 2 2, 2 1, 1 1)
        )""")
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(10, fixed.area)

    def test_polygon_disconnected_inner(self):
        geom = wkt.loads("""POLYGON(
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
        )""")
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(20.5, fixed.area)

    def test_polygon_disconnected_outer(self):
        geom = wkt.loads("""POLYGON(
          (0 0, 4 0, 4 3, 3 3, 3 2, 2 3, 1 2, 1 3, 0 3, 0 0),
          (1 1, 1 2, 3 2, 3 1, 1 1)
        )""")
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(9, fixed.area)

    def test_polygon_ring_of_inners(self):
        geom = wkt.loads("""POLYGON(
          (0 0, 4 0, 4 4, 0 4, 0 0),
          (1 1, 1 2, 2 1, 1 1),
          (1 2, 1 3, 2 3, 1 2),
          (2 3, 3 3, 3 2, 2 3),
          (2 1, 3 2, 3 1, 2 1)
        )""")
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(14, fixed.area)

    def test_polygon_ring_of_inners_2(self):
        geom = wkt.loads("""POLYGON(
          (0 0, 5 0, 5 5, 0 5, 0 0),
          (1 3, 1 4, 2 4, 1 3),
          (3 3, 4 3, 4 2, 3 3),
          (1 1, 1 2, 2 1, 1 1),
          (1 2, 1 3, 2 3, 1 2),
          (2 3, 3 3, 3 2, 2 3),
          (2 1, 3 2, 3 1, 2 1)
        )""")
        self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(fixed.is_valid)
        self.assertEquals(22, fixed.area)
