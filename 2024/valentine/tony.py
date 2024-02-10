"""Splits a set of polygons by cutting lines"""
import random
from typing import Iterable, Sequence

from shapely import Polygon, LineString

from valentine.resolution import Resolution


def cut_all(polygons: Iterable[Polygon], lines: Sequence[LineString]) -> Iterable[Polygon]:
    todo = polygons
    for line in lines:
        polygons = []
        for polygon in todo:
            #inside, outside = split(polygon, line)
            #polygons.extend(inside)
            #polygons.extend(outside)
            pass
        todo = polygons
    return polygons


def tony(
    resolution: Resolution,
    grid: Resolution,
    value: float = 0.5,
    rnd: random.Random = random,
) -> Sequence[LineString]:
    width, height = resolution
    vertical, horizontal = grid
    for gx in range(vertical):
        x = width * (gx + 1) / (vertical + 1)
        yield LineString([(x, 0), (x, height)])
    for gy in range(horizontal):
        y = height * (gy + 1) / (horizontal + 1)
        yield LineString([(0, y), (width, y)])
