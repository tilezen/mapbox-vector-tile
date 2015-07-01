==================
Mapbox Vector Tile 
==================

Installation
------------

mapbox-vector-tile is compatible with Python 2.6, 2.7, 3.2, 3.3, and 3.4. It is listed on `PyPi as 'mapbox-vector-tile'`_. The recommended way to install is via pip_:

.. code-block:: bash

  $ pip install mapbox-vector-tile

.. _PyPi as 'mapbox-vector-tile': https://pypi.python.org/pypi/mapbox-vector-tile/
.. _pip: http://www.pip-installer.org

Encoding
--------

Encode method expects an array of layers or atleast a single valid layer. A valid layer is a dictionary with the following keys

* ``name``: layer name
* ``features``: an array of features. A feature is a dictionary with the following keys:

  * ``geometry``: representation of the feature geometry in WKT or WKB. Coordinates are relative to the tile, scaled in the range `[0, 4096]`. See below for example code to perform the necessary transformation.
  * ``properties``: a dictionary with a few keys and their corresponding values.

.. code-block:: python

  >>> import mapbox_vector_tile
  
  # Using WKT
  >>> mapbox_vector_tile.encode([
      {
        "name": "water", 
        "features": [
          {
            "geometry":"POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))", 
            "properties":{
              "uid":123, 
              "foo":"bar", 
              "cat":"flew"
            }
          }
        ]
      },
      {
        "name": "air", 
        "features": [
          {
            "geometry":"LINESTRING(159 3877, -1570 3877)",
            "properties":{
              "uid":1234, 
              "foo":"bar", 
              "cat":"flew"
            }
          }
        ]
      }
    ]) 

  '\x1aH\n\x05water\x12\x18\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x03cat"\x05\n\x03bar"\x02 {"\x06\n\x04flew(\x80 x\x02\x1aD\n\x03air\x12\x15\x12\x06\x00\x00\x01\x01\x02\x02\x18\x02"\t\t\xbe\x02\xb6\x03\n\x81\x1b\x00\x1a\x03foo\x1a\x03uid\x1a\x03cat"\x05\n\x03bar"\x03 \xd2\t"\x06\n\x04flew(\x80 x\x02'


  # Using WKB
  >>> mapbox_vector_tile.encode([
      {
        "name": "water", 
        "features": [
          {
            "geometry":"\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000", 
            "properties":{
              "uid":123, 
              "foo":"bar", 
              "cat":"flew"
            }
          }
        ]
      },
      {
        "name": "air", 
        "features": [
          {
            "geometry":"\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000", 
            "properties":{
              "uid":1234, 
              "foo":"bar", 
              "cat":"flew"
            }
          }
        ]
      }
      ]) 

  '\x1aJ\n\x05water\x12\x1a\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x03cat"\x05\n\x03bar"\x02 {"\x06\n\x04flew(\x80 x\x02\x1aY\n\x03air\x12\x1c\x08\x01\x12\x08\x00\x00\x01\x01\x02\x02\x03\x03\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x05balls\x1a\x03cat"\x05\n\x03bar"\x03 \xd2\t"\x05\n\x03foo"\x06\n\x04flew(\x80 x\x02'


Coordinate transformations for encoding
~~~~~~~~

The encoder expects geometries in tile-relative coordinates, where the lower left corner is origin and values grow up and to the right, and the tile is 4096 pixels square. For example, `POINT(0 0)` is the lower left corner of the tile and `POINT(4095, 4095)` is the upper right corner of the tile. Per the specification, geometries are expected to be in spherical mercator projection before this transformations

If you have geometries in longitude and latitude (EPSG:4326), you can convert to tile-based coordinates by first projecting to Spherical Mercator (EPSG:3857) and then computing the pixel location within the tile. This example code uses Django's included GEOS library to do the transformation for `LineString` objects:


.. code-block:: python

  SRID_SPHERICAL_MERCATOR = 3857

  def linestring_in_tile(tile_bounds, line):
      # `mapbox-vector-tile` has hardcoded tile extent of 4096 units.
      MVT_EXTENT = 4096
      from django.contrib.gis.geos import LineString

      # We need tile bounds in spherical mercator
      assert tile_bounds.srid == SRID_SPHERICAL_MERCATOR

      # And we need the line to be in a known projection so we can re-project
      assert line.srid is not None
      line.transform(SRID_SPHERICAL_MERCATOR)

      (x0, y0, x_max, y_max) = tile_bounds.extent
      x_span = x_max - x0
      y_span = y_max - y0
      def xy_pairs():
          for x_merc, y_merc in line:
              yield (
                  int((x_merc - x0) * MVT_EXTENT / x_span),
                  int((y_merc - y0) * MVT_EXTENT / y_span),

The tile bounds can be found with `mercantile`, so a complete usage example might look like this:

.. code-block:: python

  from django.contrib.gis.geos import LineString, Polygon
  import mercantile
  import mapbox_vector_tile

  SRID_LNGLAT = 4326
  SRID_SPHERICAL_MERCATOR = 3857

  tile_xyz = (2452, 3422, 18)
  tile_bounds = Polygon.from_bbox(mercantile.bounds(*tile_xyz))
  tile_bounds.srid = SRID_LNGLAT
  tile_bounds.transform(SRID_SPHERICAL_MERCATOR)

  lnglat_line = LineString(((-122.1, 45.1), (-122.2, 45.2)), srid=SRID_LNGLAT)
  tile_line = linestring_in_tile(tile_bounds, lnglat_line)
  tile_pbf = mapbox_vector_tile.encode({
    "name": "my-layer",
    "features": [ {
      "geometry": tile_line.wkt,
      "properties": { "stuff": "things" },
    } ]
  })

Note that this example may not have anything visible within the tile when rendered. It's up to you to make sure you put the right data in the tile!

Decoding
--------

Decode method takes in a valid google.protobuf.message Tile and returns decoded string in the following format:

::

  {
    layername: [
      {
        'geometry': 'list of points',
        'properties': 'dictionary of key/value pairs',
        'id': 'unique id for the given feature within the layer '
      },
      {
        # ...
      }
    ],
    layername2: [
      # ...
    ]
  }

.. code-block:: python

  >>> import mapbox_vector_tile

  >>> mapbox_vector_tile.decode('\x1aJ\n\x05water\x12\x1a\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x03cat"\x05\n\x03bar"\x02 {"\x06\n\x04flew(\x80 x\x02\x1aY\n\x03air\x12\x1c\x08\x01\x12\x08\x00\x00\x01\x01\x02\x02\x03\x03\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x05balls\x1a\x03cat"\x05\n\x03bar"\x03 \xd2\t"\x05\n\x03foo"\x06\n\x04flew(\x80 x\x02') 

  {
    'water': [
      {
        'geometry': [[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]], 
        'properties': {
          'foo': 'bar', 
          'uid': 123, 
          'cat': 'flew'
        }, 
        'id': 1
      }
    ], 
    'air': [
      {
        'geometry': [[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]], 
        'properties': {
          'foo': 'bar', 
          'uid': 1234, 
          'balls': 'foo', 
          'cat': 'flew'
        }, 
        'id': 1
      }
    ]
  }

Changelog
---------

Click here_ to see what changed over time in various versions.

.. _here: https://github.com/mapzen/mapbox-vector-tile/blob/master/CHANGELOG.rst