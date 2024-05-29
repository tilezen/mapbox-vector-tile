## Version 2.1.0

- Drop the support for Python 3.8 and add the support for Python 3.12
- Update the minimum required version for `protobuf`
- Replace Isort, Flake8 and Black by Ruff in the `.pre-commit-config.yaml` file
- Use `prettier` pre-commit tool to prettify Markdown and Yaml files
- Use `poetry-check` pre-commit tool to avoid incompatibilities between `poetry.lock` and `pyproject.toml`

## Version 2.0.1

- Support previous pre 2.0 encode/decode method signatures with deprecation warning.
  [#129](https://github.com/tilezen/mapbox-vector-tile/pull/129)

## Version 2.0.0

- Drop Python 2 support
- Usage of `tox` for tests
- Add GitHub Actions
- Add pre-commit tool
- Regenerate the vector tile protobuf Python code to solve
  [#113](https://github.com/tilezen/mapbox-vector-tile/issues/113)
- Support for Python 3.11
- Delete the `round_fn` argument as Python 2 has been dropped
- Use `pyproject.toml` and Poetry to replace the `setup.py` file
- Use `geom_type` property instead of deprecated `type`
- Add the possibility to give a coordinates transformer
- Add a `geojson` option. See [#107](https://github.com/tilezen/mapbox-vector-tile/issues/107)
- Refactor the options using the `per_layer_options` and `default_options` dictionaries.
- Add the option `max_geometry_validate_tries`.

## Version 1.2.1

- Add the trove classifiers to the setup.py

## Version 1.2.0

- Performance focused release, including:
- Enable Shapely speedups, when available
- Skip inners which cause exceptions
- Union inners in blocks when making valid
- Make benchmark script python3 compatible
- Fix test to support different versions of GEOS

## Version 1.1.0

- Include LICENSE & CHANGELOG.md in sdist tarballs
- Refactor geometry encoding logic, including skipping tiny geometries
- Decoded geometry is now geojson-ish dict
- Winding order is now optional
- Add benchmarking around round function and document how to improve performance
- Document performance tip for protobuf encoding with C bindings for Debian

## Version 1.0.0

- Generate more valid polygons and multipolygons using [pyclipper](https://pypi.python.org/pypi/pyclipper) library for v2 MVT compliance (but we're still not fully v2 compliant for [other](https://github.com/tilezen/mapbox-vector-tile/issues/42) reasons).
- Handle edge cases where polygon buffer makes a multi-polygon, ensuring inner rings are dropped when subtracting them from the polygon would make it invalid, and not adding multipolygons as array elements for multipolygon constructor.
- Calculate area more properly by using PolyTree result from Clipper.
- Factor out polygon validity code into its own file.

## Version 0.5.0

- Improved results from `on_invalid_geometry_make_valid` when the geometry is self-crossing. It was possible for large parts of the geometry to be discarded, and it is now less likely. See [PR 66](https://github.com/tilezen/mapbox-vector-tile/pull/66) for more information.

## Version 0.4.0

- Custom rounding functions: a `round_fn` parameter was added to the `encode` function, which allows control over how floating point coordinates are transformed to integer ones. See [PR 55](https://github.com/tilezen/mapbox-vector-tile/pull/55).
- Custom validity functions: an `on_invalid_geometry` parameter was added to the `encode` function, which is called when invalid geometry is found, or created through coordinate rounding. See [PR 46](https://github.com/tilezen/mapbox-vector-tile/pull/46).
- Winding order bug fix: See [issue 57](https://github.com/tilezen/mapbox-vector-tile/issues/57) and [PR 59](https://github.com/tilezen/mapbox-vector-tile/pull/59).
- Performance improvements: including a 2x speedup from using `tuple`s instead of `dict`s for coordinates, see [PR 56](https://github.com/tilezen/mapbox-vector-tile/pull/56).
- Improvements to PY3 compatibility: See [PR 52](https://github.com/tilezen/mapbox-vector-tile/pull/52).

## Version 0.3.0

- python3 compatability improvements
- travis integration
- documentation updates
- insert CMD_SEG_END for MultiPolygons
- decode multipolygons correctly
- encode tiles using version 1

## Version 0.2.1

- include README.md in distribution to fix install

## Version 0.2.0

- python3 updates
- enforce winding order on multipolygons
- update key/val handling
- round floating point values instead of truncating
- add option to quantize bounds
- add option to flip y coord system
- add ability to pass custom extents

## Version 0.1.0

- Add compatibility with python 3
- Handle multipolygons as single features
- Use winding order from mapbox vector tile 2.0 spec
- Support custom extents when decoding

## Version 0.0.11

- Decode string keys to utf-8

## Version 0.0.10

- Allow encoder to accept shapely objects directly

## Version 0.0.9

- Handle tiles from java-vector-tile (zero pad binary integers)
- Update README

## Version 0.0.8

- Handle unicode properties

## Version 0.0.7

- Update id handling behavior

## Version 0.0.6

- Explode multipolygons into several features
- https://github.com/tilezen/mapbox-vector-tile/issues/4
- Resolve issue when id is passed in
- More tests

## Version 0.0.5

- Removing the option of encoding floats in big endian
- Updated tests

## Version 0.0.4

- Bug fix - does not try to load wkt geom if wkb succeeds

## Version 0.0.3

- Option to encode floats in little endian

## Version 0.0.2

- WKT Support
- Better Documentation
- More tests

## Version 0.0.1

- Initial release
