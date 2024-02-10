from typing import Iterable, Tuple
from xml.dom import minidom

from shapely import MultiPolygon, Polygon, Point
import svg.path


def parse_point(point_string: str) -> Point:
    x, y = point_string.split(',')
    return Point(x, y)


def parse_polygon(polygon_string: str) -> Polygon:
    points = [parse_point(point) for point in polygon_string.split()]
    points.append(points[0])  # close shape
    return Polygon(points)


def split_on_move(path: svg.path.Path) -> Iterable[svg.path.Path]:
    indices = [-1]
    for index, segment in enumerate(path):
        if isinstance(segment, svg.path.Move):
            indices.append(index)
    indices.append(len(path))

    for a, b in zip(indices, indices[1:]):
        # skip empty paths
        if b - 1 > a + 1:
            yield svg.path.Path(*path[a + 1:b - 1])


def to_point(c: complex) -> Point:
    return c.real, c.imag


# todo, sample using tangent gradient rather than hard coded
def sample_curve(curve: svg.path.Path) -> Iterable[Tuple[float, float]]:
    n = 32
    ts = (i / n for i in range(n))
    yield from (to_point(curve.point(t)) for t in ts)

def sample_path(path: svg.path.Path) -> Polygon:
    curves = split_on_move(path)
    polygons = [sample_curve(curve) for curve in curves]
    # todo: select by winding
    exterior = polygons[-1]
    holes = polygons[:-1]
    return Polygon(exterior, holes)


def load(path: str) -> MultiPolygon:
    doc = minidom.parse(path)
    polygons = [parse_polygon(path.getAttribute('points')) for path in doc.getElementsByTagName('polygon')]
    paths = [svg.path.parse_path(path.getAttribute('d')) for path in doc.getElementsByTagName('path')]

    everything = MultiPolygon(
        polygons + [sample_path(path) for path in paths],
    )
    doc.unlink()
    return everything
