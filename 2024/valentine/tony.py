"""Splits a set of polygons by cutting lines"""
import random
from typing import Dict, Sequence, Tuple

from shapely import box, MultiPolygon, Polygon, LineString
from shapely.ops import split

from valentine.resolution import Resolution


def rectangle_for(resolution: Resolution) -> Polygon:
    width, height = resolution
    return box(0, 0, width, height)


def cut_by_lines(polygons: MultiPolygon, lines: Sequence[LineString]) -> MultiPolygon:
    todo = [polygons]
    for line in lines:
        tmp = []
        for polygon in todo:
            tmp.extend(split(polygon, line).geoms)
        todo = tmp
    return MultiPolygon(todo)


def lines(
    resolution: Resolution,
    grid: Resolution,
    value: float = 0.5,
    rnd: random.Random = random,
) -> Sequence[LineString]:
    width, height = resolution
    vertical, horizontal = grid
    for gx in range(vertical):
        x0 = width * (gx + 1 + value * (rnd.random() - 0.5)) / (vertical + 1)
        x1 = width * (gx + 1 + value * (rnd.random() - 0.5)) / (vertical + 1)
        yield LineString([(x0, 0), (x1, height)])
    for gy in range(horizontal):
        y0 = height * (gy + 1 + value * (rnd.random() - 0.5)) / (horizontal + 1)
        y1 = height * (gy + 1 + value * (rnd.random() - 0.5)) / (horizontal + 1)
        yield LineString([(0, y0), (width, y1)])


def create_templates(
    resolution: Resolution,
    grid: Resolution,
    value: float = 0.5,
    rnd: random.Random = random,
) -> MultiPolygon:
    linesegments = lines(resolution, grid, value, rnd)
    return cut_by_lines(rectangle_for(resolution), linesegments)


def cut(polygons: MultiPolygon, templates: MultiPolygon) -> MultiPolygon:
    """Cuts a MultiPolygon by lines"""
    return MultiPolygon([polygons.intersection(template) for template in templates.geoms])
