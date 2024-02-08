from xml.dom import minidom

import svg.path


def parse_point(point_string: str) -> complex:
    x, y = point_string.split(',')
    return complex(float(x), float(y))


def parse_polygon(polygon_string: str) -> svg.path.Path:
    points = [parse_point(point) for point in polygon_string.split()]
    return svg.path.Path(*(svg.path.Line(start, end) for start, end in zip(points, points[1:])))


def _load_svg(doc: minidom.Document) -> svg.path.Path:
    polygons = [parse_polygon(path.getAttribute('points')) for path in doc.getElementsByTagName('polygon')]
    paths = [svg.path.parse_path(path.getAttribute('d')) for path in doc.getElementsByTagName('path')]
    return svg.path.Path(*(polygons + paths))


def load(path: str) -> svg.path.Path:
    doc = minidom.parse(path)
    everything = _load_svg(doc)
    doc.unlink()
    return everything
