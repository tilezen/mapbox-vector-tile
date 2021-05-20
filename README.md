Mapbox Vector Tile
==================

[![Build Status](https://travis-ci.org/tilezen/mapbox-vector-tile.svg?branch=master)](https://travis-ci.org/tilezen/mapbox-vector-tile)
[![Coverage Status](https://coveralls.io/repos/github/tilezen/mapbox-vector-tile/badge.svg?branch=master)](https://coveralls.io/github/tilezen/mapbox-vector-tile?branch=master)

Installation
------------

mapbox-vector-tile is compatible with Python 2.7 and 3.5. It is listed on PyPi as `mapbox-vector-tile`. The recommended way to install is via `pip`:

```shell
pip install mapbox-vector-tile
```

Note that `mapbox-vector-tile` depends on [Shapely](https://pypi.python.org/pypi/Shapely), a Python library for computational geometry which requires a library called [GEOS](https://trac.osgeo.org/geos/). Please see [Shapely's instructions](https://pypi.python.org/pypi/Shapely#installing-shapely) for information on how to install its prerequisites.

Encoding
--------

Encode method expects an array of layers or atleast a single valid layer. A valid layer is a dictionary with the following keys

* `name`: layer name
* `features`: an array of features. A feature is a dictionary with the following keys:

  * `geometry`: representation of the feature geometry in WKT, WKB, or a shapely geometry. Coordinates are relative to the tile, scaled in the range `[0, 4096)`. See below for example code to perform the necessary transformation. *Note* that `GeometryCollection` types are not supported, and will trigger a `ValueError`.
  * `properties`: a dictionary with a few keys and their corresponding values.

```python

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
```

### Coordinate transformations for encoding

The encoder expects geometries either:

1. In tile-relative coordinates, where the lower left corner is origin and values grow up and to the right, and the tile is 4096 pixels square. For example, `POINT(0 0)` is the lower left corner of the tile and `POINT(4096, 4096)` is the upper right corner of the tile. In this case, the library does no projection, and coordinates are encoded as-is.
2. In another coordinate system, with the tile bounds given by the `quantize_bounds` parameter. In this case, the library will scale coordinates so that the `quantize_bounds` fit within the range (0, 4096) in both `x` and `y` directions. Aside than the affine transformation, the library does no other projection.

It is possible to control whether the tile is in a "y down" coordinate system by setting the parameter `y_coord_down=True` on the call to `encode()`. The default is "y up".

It is possible to control the tile extents (by default, 4096 as used in the examples above), by setting the `extents` parameter on the call to `encode()`. The default is 4096.

If you have geometries in longitude and latitude (EPSG:4326), you can convert to tile-based coordinates by first projecting to Spherical Mercator (EPSG:3857) and then computing the pixel location within the tile. This example code uses Django's included GEOS library to do the transformation for `LineString` objects:

```python
  SRID_SPHERICAL_MERCATOR = 3857

  def linestring_in_tile(tile_bounds, line):
      # `mapbox-vector-tile` has a hardcoded tile extent of 4096 units.
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

      tile_based_coords = []
      for x_merc, y_merc in line:
          tile_based_coord = (int((x_merc - x0) * MVT_EXTENT / x_span),
                              int((y_merc - y0) * MVT_EXTENT / y_span))
          tile_based_coords.append(tile_based_coord)
      return LineString(*tile_based_coords)
```

The tile bounds can be found with `mercantile`, so a complete usage example might look like this:

```python
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
```

Note that this example may not have anything visible within the tile when rendered. It's up to you to make sure you put the right data in the tile!

Also note that the spec allows the extents to be modified, even though they are often set to 4096 by convention. `mapbox-vector-tile` assumes an extent of 4096.

### Quantization

The encoder also has options to quantize the data for you via the `quantize_bounds` option. When encoding, pass in the bounds in the form (minx, miny, maxx, maxy) and the coordinates will be scaled appropriately during encoding.

```python
mapbox_vector_tile.encode([
      {
        "name": "water",
        "features": [
          {
            "geometry":"POINT(15 15)",
            "properties":{
              "foo":"bar",
            }
          }
        ]
      }
    ], quantize_bounds=(10.0, 10.0, 20.0, 20.0))
```

In this example, the coordinate that would get encoded would be (2048, 2048)

Additionally, if the data is already in a cooridnate system with y values going down, the encoder supports an option, `y_coord_down`, that can be set to True. This will suppress flipping the y coordinate values during encoding.

### Custom extents

The encoder also supports passing in custom extents. These will be passed through to the layer in the pbf, and honored during any quantization or y coordinate flipping.

```python
mapbox_vector_tile.encode([
      {
        "name": "water",
        "features": [
          {
            "geometry":"POINT(15 15)",
            "properties":{
              "foo":"bar",
            }
          }
        ]
      }
    ], quantize_bounds=(0.0, 0.0, 10.0, 10.0), extents=50)
```

### Custom rounding functions

In order to maintain consistency between Python 2 and 3, the `decimal` module is used to explictly define `ROUND_HALF_EVEN` as the rounding method. This can be slower than the built-in `round()` function. Encode takes an optional `round_fn` where you can specify the round function to be used.

 ```python
mapbox_vector_tile.encode([
      {
        "name": "water",
        "features": [
          {
            "geometry":"POINT(15 15)",
            "properties":{
              "foo":"bar",
            }
          }
        ]
      }
    ], quantize_bounds=(0.0, 0.0, 10.0, 10.0), round_fn=round)
```

Decoding
--------

Decode method takes in a valid google.protobuf.message Tile and returns decoded string in the following format:

```python
  {
    layername: {
        'extent': 'integer layer extent'
        'version': 'integer'
        'features': [{
          'geometry': 'list of points',
          'properties': 'dictionary of key/value pairs',
          'id': 'unique id for the given feature within the layer '
          }, ...
        ]
    },
    layername2: {
      # ...
    }
  }
```

```python
  >>> import mapbox_vector_tile

  >>> mapbox_vector_tile.decode('\x1aJ\n\x05water\x12\x1a\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x03cat"\x05\n\x03bar"\x02 {"\x06\n\x04flew(\x80 x\x02\x1aY\n\x03air\x12\x1c\x08\x01\x12\x08\x00\x00\x01\x01\x02\x02\x03\x03\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x05balls\x1a\x03cat"\x05\n\x03bar"\x03 \xd2\t"\x05\n\x03foo"\x06\n\x04flew(\x80 x\x02')

  {
    'water': {
      'extent': 4096,
      'version': 2,
      'features': [{
          'geometry': {'type': 'Polygon', 'coordinates': [[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]},
          'properties': {
            'foo': 'bar',
            'uid': 123,
            'cat': 'flew'
          },
          'type': 3,
          'id': 1
        }
      ]
    },
    'air': {
      'extent': 4096,
      'version': 2,
      'features': [{
          'geometry': {'type': 'Polygon', 'coordinates': [[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]},
          'properties': {
            'foo': 'bar',
            'uid': 1234,
            'balls': 'foo',
            'cat': 'flew'
          },
          'type': 3,
          'id': 1
        }
      ]
    }
  }
```

Here's how you might decode a tile from a file.

```python
  >>> import mapbox_vector_tile
  >>> with open('tile.mvt', 'rb') as f:
  >>>     data = f.read()
  >>> decoded_data = mapbox_vector_tile.decode(data)
  >>> with open('out.txt', 'w') as f:
  >>>     f.write(repr(decoded_data))
```

Use native protobuf library for performance
------------------------------------------

The c++ implementation of the underlying protobuf library is more performant than the pure python one. Depending on your operating system, you might need to [compile the C++ library](https://github.com/google/protobuf/tree/master/python#c-implementation) or install it.

### on debian Jessie

The version of protobuf (libprotobuf9) available on debian Jessie is [2.6.1](https://github.com/google/protobuf/tree/v2.6.1/python). You can install it with the proper python bindings from your package manager :

    $  sudo apt-get install libprotoc9 libprotobuf9 protobuf-compiler python-protobuf
    
Then, you'll have to enable two environnement variable BEFORE runing your python program :

    $ export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=cpp
    $ export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION_VERSION=2


Changelog
---------

Click [here](https://github.com/tilezen/mapbox-vector-tile/blob/master/CHANGELOG.md) to see what changed over time in various versions.
