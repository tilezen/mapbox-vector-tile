# -*- coding: utf-8 -*-
"""
Tests for vector_tile/encoder.py
"""

import unittest

import mapbox_vector_tile


class BaseTestCase(unittest.TestCase):
	def test_encoder(self):
		name = "water"
		geometry = "\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000"
		properties = {
			"uid":123, 
			"foo":"bar", 
			"baz":"foo"
		}
		self.assertEqual(mapbox_vector_tile.encode([{
				"name": name,
				"features": [{
					"geometry": geometry,
					"properties": properties
				}]
			}]), '\x1aI\n\x05water\x12\x1a\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03baz\x1a\x03uid"\x05\n\x03bar"\x05\n\x03foo"\x02 {(\x80 x\x02')

