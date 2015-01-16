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

  * ``geometry``: representation of the feature geometry in WKT or WKB
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
            "geometry":"LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)", 
            "properties":{
              "uid":1234, 
              "foo":"bar", 
              "cat":"flew"
            }
          }
        ]
      }
    ]) 

  '\x1aJ\n\x05water\x12\x1a\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x03cat"\x05\n\x03bar"\x02 {"\x06\n\x04flew(\x80 x\x02\x1aW\n\x03air\x12\x1a\x08\x01\x12\x08\x00\x00\x01\x01\x02\x02\x03\x03\x18\x02"\n\t\x8d\x01\xaa?\x12\x00\x00\x00\x00\x1a\x03foo\x1a\x03uid\x1a\x05balls\x1a\x03cat"\x05\n\x03bar"\x03 \xd2\t"\x05\n\x03foo"\x06\n\x04flew(\x80 x\x02'


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