Mapbox Vector Tile 
==================

Installation
------------

mapbox-vector-tile is compatible with Python 2.6, 2.7, 3.2, 3.3, and 3.4. It is listed on `PyPi as 'mapbox-vector-tile'`_. The recommended way to install is via pip_:

.. code::

  pip install mapbox-vector-tile

.. _PyPi as 'mapbox-vector-tile': https://pypi.python.org/pypi/mapbox-vector-tile/
.. _pip: http://www.pip-installer.org

Encoding
~~~~~~~~

.. code:: python

  >>> import mapbox_vector_tile

  >>> mapbox_vector_tile.encode([{"name": "water", "features": [{"geometry":"\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000", "properties":{"uid":123, "foo":"bar", "cat":"flew"}}]},{"name": "air", "features": [{"geometry":"\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000", "properties":{"uid":1234, "foo":"bar", "cat":"flew", "balls":"foo"}}]}]) 

  '\x1aJ\n\x05water\x12\x1a\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x03cat"\x05\n\x03bar"\x02 {"\x06\n\x04flew(\x80 x\x02\x1aY\n\x03air\x12\x1c\x08\x01\x12\x08\x00\x00\x01\x01\x02\x02\x03\x03\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x05balls\x1a\x03cat"\x05\n\x03bar"\x03 \xd2\t"\x05\n\x03foo"\x06\n\x04flew(\x80 x\x02'

Decoding
~~~~~~~~

.. code:: python

  >>> import mapbox_vector_tile

  >>> mapbox_vector_tile.decode('\x1aJ\n\x05water\x12\x1a\x08\x01\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x03cat"\x05\n\x03bar"\x02 {"\x06\n\x04flew(\x80 x\x02\x1aY\n\x03air\x12\x1c\x08\x01\x12\x08\x00\x00\x01\x01\x02\x02\x03\x03\x18\x03"\x0c\t\x00\x80@\x1a\x00\x01\x02\x00\x00\x02\x0f\x1a\x03foo\x1a\x03uid\x1a\x05balls\x1a\x03cat"\x05\n\x03bar"\x03 \xd2\t"\x05\n\x03foo"\x06\n\x04flew(\x80 x\x02') 

  {u'water': [{'geometry': [[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]], 'properties': {u'foo': u'bar', u'uid': 123L, u'cat': u'flew'}, 'id': 1L}], u'air': [{'geometry': [[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]], 'properties': {u'foo': u'bar', u'uid': 1234L, u'balls': u'foo', u'cat': u'flew'}, 'id': 1L}]}