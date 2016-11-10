# -*- coding: utf-8 -*-
"""
Tests for vector_tile/polygon.py
"""
import unittest

from mapbox_vector_tile.polygon import make_it_valid, clean_multi
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

    def test_clean_multi(self):
        geom = wkt.loads("""MULTIPOLYGON (((1796 -189, 1794 -188, 1794 -190, 1798 -192,
        1805 -194, 1806 -195, 1806 -194, 1807 -203, 1803 -206, 1798 -205, 1781 -194, 1772 -187,
        1761 -185, 1748 -190, 1733 -181, 1725 -184, 1710 -198, 1704 -199, 1699 -195, 1695 -183,
        1690 -175, 1683 -173, 1676 -173, 1670 -176, 1656 -190, 1642 -196, 1637 -205, 1633 -209,
        1613 -215, 1603 -228, 1598 -233, 1564 -241, 1563 -239, 1580 -235, 1592 -234, 1598 -231,
        1603 -227, 1611 -215, 1621 -210, 1633 -208, 1641 -195, 1657 -187, 1669 -174, 1675 -171,
        1684 -171, 1691 -175, 1697 -184, 1700 -195, 1704 -197, 1710 -197, 1726 -181, 1732 -179,
        1739 -182, 1749 -189, 1761 -184, 1773 -185, 1778 -188, 1783 -195, 1792 -198, 1800 -204,
        1803 -204, 1804 -202, 1803 -196, 1789 -191, 1781 -183, 1779 -179, 1781 -174, 1786 -171,
        1801 -174, 1806 -173, 1824 -181, 1829 -181, 1837 -174, 1838 -170, 1838 -166, 1830 -158,
        1818 -155, 1816 -152, 1818 -149, 1822 -146, 1837 -142, 1853 -131, 1858 -132, 1869 -140,
        1873 -140, 1875 -134, 1870 -121, 1871 -118, 1875 -115, 1885 -117, 1900 -117, 1915 -110,
        1931 -113, 1946 -107, 1964 -118, 1982 -119, 1984 -122, 1987 -128, 1991 -130, 2001 -132,
        2018 -131, 2023 -135, 2030 -144, 2037 -166, 2045 -169, 2055 -166, 2060 -166, 2064 -168,
        2075 -182, 2095 -180, 2098 -183, 2101 -188, 2101 -193, 2100 -199, 2090 -209, 2085 -225,
        2064 -261, 2059 -274, 2056 -290, 2056 -306, 2060 -321, 2066 -334, 2075 -345, 2084 -348,
        2125 -349, 2149 -359, 2177 -389, 2193 -398, 2216 -404, 2226 -404, 2251 -407, 2269 -406,
        2274 -407, 2277 -412, 2277 -417, 2275 -423, 2270 -429, 2253 -441, 2232 -443, 2224 -446,
        2220 -451, 2219 -458, 2222 -463, 2234 -469, 2243 -471, 2250 -469, 2259 -463, 2266 -455,
        2278 -436, 2279.176470588235 -435, 2280 -435, 2289 -427, 2285.5 -429.625, 2298 -419,
        2302 -416, 2331 -404, 2335 -403, 2342 -403, 2350 -401, 2372 -384, 2381 -385,
        2390.375 -390.625, 2393 -395, 2394 -403, 2392 -417, 2394 -423, 2398 -426, 2405 -427,
        2414 -423, 2419 -415, 2425 -399, 2429 -392, 2435 -385, 2443 -383, 2450 -387, 2453 -393,
        2450 -400, 2443 -410, 2442 -415, 2445 -421, 2453 -430, 2461 -435, 2474 -437, 2483 -435,
        2486 -432, 2496 -411, 2497 -371, 2502 -360, 2510 -351, 2522 -340, 2531 -327, 2546 -310,
        2552 -305, 2559 -302, 2586 -299, 2593 -296, 2582 -298, 2595 -295, 2601 -285, 2600 -280,
        2597 -273, 2600 -271, 2603 -285, 2602 -290, 2597 -296, 2580 -309, 2579 -308, 2587 -302,
        2574 -302, 2551 -311, 2538 -327, 2537 -326, 2533 -330, 2523 -345, 2513 -354, 2504 -366,
        2500 -379, 2501 -400, 2499 -415, 2486 -435, 2480 -440, 2472 -442, 2459 -440, 2454 -437,
        2442 -423, 2439 -416, 2439 -410, 2450 -394, 2449 -390, 2446 -388, 2440 -387, 2436 -388,
        2430 -396, 2419 -422, 2412 -428, 2403 -430, 2395 -428, 2390 -423, 2389 -417, 2392 -402,
        2390 -396, 2382 -390, 2374 -389, 2365 -392, 2351 -404, 2332 -408, 2314 -417, 2306 -424,
        2297 -427, 2288 -432, 2278 -442, 2266 -460, 2252 -471, 2240 -473, 2220 -465, 2216 -459,
        2216 -452, 2219 -446, 2227 -441, 2235 -439, 2249 -438, 2264 -429, 2274 -419, 2274 -413,
        2272 -410, 2263 -409, 2232 -416, 2226 -416, 2184 -399, 2175 -393, 2162 -379, 2145 -365,
        2129 -355, 2111 -352, 2085 -356, 2076 -352, 2069 -346, 2059 -332, 2052 -315, 2051 -302,
        2053 -280, 2062 -254, 2059 -264, 2070 -246, 2071 -239, 2070 -238, 2071 -238, 2074 -234,
        2087 -209, 2097 -199, 2099 -193, 2098 -187, 2094 -183, 2078 -186, 2073 -185, 2068 -181,
        2061 -171, 2059 -169, 2042 -171, 2036 -170, 2031 -164, 2026 -144, 2020 -137, 2014 -134,
        2000 -136, 1990 -133, 1986 -131, 1981 -122, 1963 -121, 1946 -109, 1942 -109, 1936 -115,
        1932 -116, 1915 -113, 1911 -114, 1906 -118, 1900 -119, 1887 -119, 1880 -117, 1875 -117,
        1872 -121, 1878 -136, 1876 -140, 1874 -143, 1869 -143, 1860 -136, 1856 -135, 1837 -146,
        1821 -149, 1819 -151, 1819 -153, 1831 -156, 1839 -164, 1841 -170, 1839 -177, 1831 -182,
        1826 -184, 1787 -173, 1783 -174, 1782 -177, 1785 -184, 1792 -186, 1796 -189),
        (2226 -404, 2229 -406, 2231 -406, 2232 -406, 2226 -404),
        (2563 -303, 2557 -305, 2554 -307, 2558 -307, 2563 -303), 
        (2462 -438, 2470 -441, 2478 -439, 2463 -438, 2462 -438),
        (2336 -404, 2332 -404, 2327 -406, 2325 -407, 2336 -404),
        (2299 -425, 2306 -423, 2316 -415, 2304 -418, 2299 -424, 2298 -425, 2299 -425),
        (2206 -406, 2229 -414, 2248 -410, 2241 -409, 2206 -406),
        (2240 -407, 2239 -408, 2242 -408, 2241 -407, 2240 -407),
        (2204 -405, 2204 -406, 2205 -406, 2204 -405),
        (2156 -370, 2157 -371, 2150 -362, 2144 -360, 2156 -370),
        (2083 -353, 2089 -354, 2094 -352, 2079 -351, 2083 -353),
        (2079 -349, 2078 -350, 2080 -350, 2080 -349, 2079 -349)),
        ((1796 -189, 1804 -189, 1798 -190, 1796 -189)),
        ((1804 -189, 1806 -191, 1806 -190, 1807 -191, 1806 -193, 1804 -189)),
        ((1806 -193, 1806 -194, 1805 -194, 1806 -193)),
        ((2390 -390, 2385 -385, 2379 -382, 2385 -384, 2390 -390)),
        ((2062 -254, 2068 -239, 2069 -238, 2070 -238, 2062 -254)),
        ((1786 -185, 1791 -188, 1793 -190, 1786 -185),
        (1786 -185, 1787 -187, 1789 -189, 1793 -190, 1792 -187, 1786 -185)))""")
        self.assertFalse(geom.is_valid)
        fixed = clean_multi(geom)
        self.assertTrue(fixed.is_valid)
