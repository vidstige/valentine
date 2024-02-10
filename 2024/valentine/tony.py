"""Splits a set of polygons by cutting lines"""
import random
from typing import Iterable, Sequence

from shapely import GeometryCollection, MultiPolygon, Polygon, LineString
from shapely.ops import split

from valentine.resolution import Resolution

import sys
def cut(polygons: MultiPolygon, lines: Sequence[LineString]) -> MultiPolygon:
    """Cuts a MultiPolygon by lines"""
    todo = [polygons]
    for line in lines:
        tmp = []
        for polygon in todo:
            tmp.extend(split(polygon, line).geoms)
        
        #print('todo:', type(tmp[0]), file=sys.stderr)
        todo = tmp

    #for t in todo:
    #    print(type(t), file=sys.stderr)
    return MultiPolygon(todo)


def grid(
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
