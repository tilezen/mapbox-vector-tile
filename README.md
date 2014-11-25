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

  >>> from mapbox-vector-tile import vector_tile

  >>> vector_tile.encode([{"name": "water", "features": [{"geometry":"\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000", "properties":{"uid":123, "foo":"bar", "cat":"flew"}}]},{"name": "air", "features": [{"geometry":"\001\003\000\000\000\001\000\000\000\005\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\360?\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000", "properties":{"uid":1234, "foo":"bar", "cat":"flew", "balls":"foo"}}]}]))

Decoding
~~~~~~~~

.. code:: python

  >>> from mapbox-vector-tile import vector_tile

  >>> vector_tile.decode(vectorTile)

