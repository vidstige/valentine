"""Splits a set of polygons by cutting lines"""
import random
from typing import Iterable, Sequence

from valentine.polygon import Polygon, LineSegment, split
from valentine.resolution import Resolution


def cut_all(polygons: Iterable[Polygon], linesegments: Sequence[LineSegment]) -> Iterable[Polygon]:
    todo = polygons
    for linesegment in linesegments:
        polygons = []
        for polygon in todo:
            inside, outside = split(polygon, linesegment)
            todo.extend(inside)
            todo.extend(outside)
        todo = polygons
    return polygons


def tony(
    resolution: Resolution,
    grid: Resolution,
    value: float = 0.5,
    rnd: random.Random = random,
) -> Sequence[LineSegment]:
    width, height = resolution
    vertical, horizontal = grid
    for gx in range(vertical):
        x = width * (gx + 1) / (vertical + 1)
        offset = 0
        yield (x, 0), (x, height)
    for gy in range(horizontal):
        y = height * (gy + 1) / (horizontal + 1)
        yield (0, y), (width, y)
