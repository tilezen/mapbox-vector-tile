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

    def test_multipolygon_with_flipped_ring(self):
        geom = wkt.loads("""MULTIPOLYGON(
          ((0 0, 0 4, 4 4, 4 0, 0 0), (1 1, 1 3, 3 3, 3 1, 1 1)),
          ((5 0, 9 0, 9 4, 5 4, 5 0), (6 1, 6 3, 8 3, 8 1, 6 1))
        )""")
        #self.assertFalse(geom.is_valid)
        fixed = make_it_valid(geom)
        self.assertTrue(geom.is_valid)
        self.assertEquals(24, geom.area)
