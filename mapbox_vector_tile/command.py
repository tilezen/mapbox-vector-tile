import argparse
import collections
import json
import logging
import os
import sys

import mercantile
import shapely.affinity
import shapely.geometry
import shapely.ops
import shapely.wkb

from . import encode, decode


_LOG = logging.getLogger(__name__)


def _configure_logger(logger, level, stream=None):
    formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(name)s:%(lineno)s - %(message)s')
    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)


def mvt_decode():
    buffer = sys.stdin.buffer.read()
    layers = decode(buffer)
    print(json.dumps(layers))


Tile = collections.namedtuple('Tile', ['x', 'y', 'z'])


def _parse_tiles(tile_texts):
    """
    :param tile_texts: an iterable of "z/x/y" or "minz-maxz" (inclusive)
    :return: a generator of tiles
    """
    tiles = set()
    for text in tile_texts:
        if '/' in text:
            z, x, y = text.split('/')
            tiles.add(Tile(x=int(x), y=int(y), z=int(z)))
        elif '-' in text:
            minz, maxz = text.split('-')
            minz, maxz = min(int(minz), int(maxz)), max(int(minz), int(maxz))
            for z in range(minz, maxz+1):
                tiles.add(Tile(x=None, y=None, z=z))
        else:
            tiles.add(Tile(x=None, y=None, z=int(text)))

    # if both x/y/z and None/None/z exist in tiles, we remove None/None/z
    removing = set(
        tile.z for tile in tiles
        if tile.x is not None
    )
    for z in removing:
        tile = Tile(x=None, y=None, z=z)
        if tile in tiles:
            tiles.remove(tile)

    return tiles


def _get_ancestral_tiles(tiles, sorted_levels):
    """
    generate ancestral tiles at the reversely sorted levels

    :param tiles: an iterable of tiles that mush be lower than sorted_levels[0]
    :param sorted_levels: reversely sorted levels
    :return: generate of ancestral tiles
    """
    children = tiles

    for level in sorted_levels:
        if level < 0:
            break

        tiles = set()
        for child in children:
            assert level <= child.z
            scale = 2 ** (child.z - level)
            tiles.add(Tile(x=child.x // scale, y=child.y // scale, z=level))

        for tile in tiles:
            yield tile

        children = tiles


def _generate_tile_children(tile: Tile):
    z = tile.z + 1
    yield Tile(x=tile.x * 2, y=tile.y * 2, z=z)
    yield Tile(x=tile.x * 2 + 1, y=tile.y * 2, z=z)
    yield Tile(x=tile.x * 2, y=tile.y * 2 + 1, z=z)
    yield Tile(x=tile.x * 2 + 1, y=tile.y * 2 + 1, z=z)


_WORLD_BOUNDS = mercantile.bounds(0, 0, 0)
_WORLD_MINX, _WORLD_MINY = mercantile.xy(_WORLD_BOUNDS.west, _WORLD_BOUNDS.south)
_WORLD_MAXX, _WORLD_MAXY = mercantile.xy(_WORLD_BOUNDS.east, _WORLD_BOUNDS.north)
_WORLD_WIDTH, _WORLD_HEIGHT = _WORLD_MAXX - _WORLD_MINX, _WORLD_MAXY - _WORLD_MINY


def _tile_bbox(tile):
    n = 2 ** tile.z
    tile_width, tile_height = _WORLD_WIDTH / n, _WORLD_HEIGHT / n
    minx, miny = tile.x * tile_width, tile.y * tile_height
    maxx, maxy = minx + tile_width, miny + tile_height
    # Flip y
    miny, maxy = _WORLD_HEIGHT - maxy, _WORLD_WIDTH - miny
    # Shift origin
    return minx + _WORLD_MINX, miny + _WORLD_MINY, maxx + _WORLD_MINX, maxy + _WORLD_MINY


def _is_intersected(shape_mercator, tile: Tile):
    """
    check if shape in mercator intersects with the tile.

    :param shape_mercator: shape in mercator
    :param tile: tile coodintates
    :return: whether they intersect
    """
    minx, miny, maxx, maxy = _tile_bbox(tile)
    coords = [
        (minx, miny),
        (maxx, miny),
        (maxx, maxy),
        (minx, maxy),
        (minx, miny),
    ]
    tile_bbox_shape = shapely.geometry.Polygon(coords)
    return tile_bbox_shape.intersects(shape_mercator)


def _intersected_tiles(shape_mercator, zoom_level, parent_tile=None):
    """
    generate intersected tiles at the zoom level.

    :param shape_mercator: the shape in mercator
    :param zoom_level: the zoom level
    :return: generator of tiles
    """

    if parent_tile is None:
        parent_tile = Tile(x=0, y=0, z=0)

    if zoom_level < parent_tile.z:
        return

    if zoom_level == parent_tile.z:
        yield parent_tile

    if _is_intersected(shape_mercator, parent_tile):
        for child in _generate_tile_children(parent_tile):
            yield from _intersected_tiles(shape_mercator, zoom_level, child)


def _extract_feature(geojson):
    type = geojson['type']
    if type == 'Feature':
        yield geojson
    elif type == 'FeatureCollection':
        for feature in geojson['features']:
            yield feature
    else:
        # assume it is a geometry
        yield {
            'type': 'Feature',
            'geometry': geojson,
            'properties': {},
        }


def _get_geometry_shape(geometry):
    type = geometry['type']
    coordinates = geometry['coordinates']
    if type == 'Point':
        return shapely.geometry.Point(coordinates)
    elif type == 'MultiPoint':
        return shapely.geometry.MultiPoint(coordinates)
    elif type == 'LineString':
        return shapely.geometry.LineString(coordinates)
    elif type == 'MultiLineString':
        return shapely.geometry.MultiLineString(coordinates)
    elif type == 'Polygon':
        return shapely.geometry.Polygon(coordinates)
    elif type == 'MultiPolygon':
        return shapely.geometry.MultiPolygon(coordinates)
    else:
        raise ValueError('Invalid geometry type {}'.format(type))


def _transform_to_mercator(shape_wgs84):
    return shapely.ops.transform(
        mercantile.xy,
        shape_wgs84,
    )


def _transform_affine_params(tile, extent):
    bounds = mercantile.bounds(*tile)

    minx, miny = mercantile.xy(bounds.west, bounds.south)
    maxx, maxy = mercantile.xy(bounds.east, bounds.north)

    dx = -minx
    dy = -miny
    fx = extent / (maxx - minx)
    fy = extent / (maxy - miny)

    return dx, dy, fx, fy


def _transform_tile_based_mercator(shape_mercator, tile, extent=4096):
    dx, dy, fx, fy = _transform_affine_params(tile, extent=extent)
    return shapely.affinity.affine_transform(
        shape_mercator,
        [
            fx, 0,
            0, fy,
            dx * fx, dy * fy
        ]
    )


def _index_features(geojson, sorted_levels):
    """
    put features in the geojson into the tiles that they intersect with respectively.

    :param geojson: any geojson element
    :param sorted_levels: a reversely sorted zoom levels
    :return: the indexed dict
    """
    indexed_features = {}

    for feature in _extract_feature(geojson):
        shape_wgs84 = _get_geometry_shape(feature['geometry'])
        shape_mercator = _transform_to_mercator(shape_wgs84)
        # highest tiles that intersect with the shape
        highest_tiles = _intersected_tiles(shape_mercator, sorted_levels[0])
        # all tiles in the sorted levels that contain the highest tiles
        ancestral_tiles = _get_ancestral_tiles(highest_tiles, sorted_levels)
        for tile in ancestral_tiles:
            indexed_features.setdefault(tile, []).append((feature, shape_mercator))

    return indexed_features


def write_tile(args, tile, indexed_features):
    """
    encode features indexed in the tile and write then into the disk.

    :param args: a namespace that must contain directory and layer name
    :param tile: the tile coordinates
    :param indexed_features: a dict that maps tile to a list of tuples (feature, shape in mercator)
    :return: None
    """
    if tile not in indexed_features:
        return


    def _transform_and_simplify(shape_mercator, tile):
        shape = _transform_tile_based_mercator(shape_mercator, tile)
        return shape.simplify(1, preserve_topology=True)


    def _normalize_properties(properties):
        return {
            key: (json.dumps(value) if isinstance(value, (list ,dict)) else value)
            for key, value in properties.items()
        }


    features = [
        {
            'geometry': _transform_and_simplify(shape_mercator, tile),
            'properties': _normalize_properties(feature['properties']),
        }
        for feature, shape_mercator in indexed_features[tile]
    ]
    encoded_tile = encode({
        'name': args.name,
        'features': features,
    })
    tile_path = os.path.join(args.directory, '{tile.z}/{tile.x}/{tile.y}.mvt'.format(tile=tile))
    tile_dir = os.path.dirname(tile_path)
    try:
        os.makedirs(tile_dir)
    except OSError:
        pass
    with open(tile_path, 'wb') as f:
        f.write(encoded_tile)

    _LOG.info('Wrote {nbr_features} feature(s) in {tile_path}'.format(
        nbr_features=len(features),
        tile_path=tile_path,
    ))


def mvt_encode():
    _configure_logger(_LOG, logging.INFO, stream=sys.stdout)

    parser = argparse.ArgumentParser(description='Encode GeoJSON read from stdin as mapbox vector tiles')
    parser.add_argument('-d', '--directory', help='Write tiles into the directory')
    parser.add_argument('name', help='Layer name')
    parser.add_argument('tiles', nargs='+', help='Tile coodinates (z/x/y), or zoom level ranges (minz-maxz)')
    args = parser.parse_args()

    sorted_tiles = sorted(
        _parse_tiles(args.tiles),
        key=lambda tile: tile.z,
        reverse=True,
    )
    sorted_levels = [tile.z for tile in sorted_tiles]

    # index features: tile -> (feature, shape)
    geojson = json.load(sys.stdin)
    indexed_features = _index_features(geojson, sorted_levels)

    # encode
    for tile in sorted_tiles:
        if tile.x is None:
            assert tile.y is None
            for indexed_tile in indexed_features:
                if indexed_tile.z == tile.z:
                    write_tile(args, indexed_tile, indexed_features)
        else:
            write_tile(args, tile, indexed_features)
