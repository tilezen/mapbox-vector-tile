Version 0.2.1
-------------

* include README.md in distribution to fix install

Version 0.2.0
-------------

* python3 updates
* enforce winding order on multipolygons
* update key/val handling
* round floating point values instead of truncating
* add option to quantize bounds
* add option to flip y coord system
* add ability to pass custom extents

Version 0.1.0
-------------

* Add compatibility with python 3
* Handle multipolygons as single features
* Use winding order from mapbox vector tile 2.0 spec
* Support custom extents when decoding

Version 0.0.11
--------------

* Decode string keys to utf-8

Version 0.0.10
--------------

* Allow encoder to accept shapely objects directly

Version 0.0.9
-------------

* Handle tiles from java-vector-tile (zero pad binary integers)
* Update README

Version 0.0.8
-------------

* Handle unicode properties

Version 0.0.7
-------------

* Update id handling behavior

Version 0.0.6
-------------

* Explode multipolygons into several features
* https://github.com/mapzen/mapbox-vector-tile/issues/4
* Resolve issue when id is passed in
* More tests

Version 0.0.5
-------------

* Removing the option of encoding floats in big endian
* Updated tests

Version 0.0.4
-------------

* Bug fix - does not try to load wkt geom if wkb succeeds 

Version 0.0.3
-------------

* Option to encode floats in little endian

Version 0.0.2
-------------

* WKT Support
* Better Documentation
* More tests

Version 0.0.1
-------------

* Initial release
