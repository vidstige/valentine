from itertools import chain, tee
from typing import Iterable, List, Tuple, TypeVar

from valentine.linesegment import Point, LineSegment, intersection


Polygon = List[Point]


def cross(a: Point, b: Point) -> float:
    ax, ay = a
    bx, by = b
    return ax * by - ay * bx


T = TypeVar('T')
def sides(iterable: Iterable[T]) -> Iterable[Tuple[T, T]]:
    a, b = tee(iterable)
    first = next(b, None)
    return zip(a, chain(b, (first,)))


def split(polygon: Polygon, linesegment: LineSegment) -> Tuple[List[Polygon], List[Polygon]]:
    (ax, ay), (bx, by) = linesegment
    # linesegment vector (a -> b)
    lsv = bx - ax, by - ay

    # compute signed distance from line segment to all vertices in polygon
    signed_distances = [cross(lsv, (x - ax, y - ay)) for x, y in polygon]

    # all vertices are to the left of the line segment
    if all(d < 0 for d in signed_distances):
        return [polygon], []
    # all vertices are to the right of the line segment
    if all(d > 0 for d in signed_distances):
        return [], [polygon]

    # compute intersections (using signed distance)
    vertices = []
    for (da, pa), (db, pb) in sides(zip(signed_distances, polygon)):
        # always add "first" point of the segment
        vertices.append((pa, False, False))  # not entering nor exiting

        # check if segment enters or exits clip area (across line segment)
        entering = da < 0 and db > 0
        exiting = da > 0 and db < 0
        if entering or exiting:
            # find intersection point i
            i = intersection(linesegment, (pa, pb))
            # there should always be an intersection point between
            # an inside and outside point
            assert i is not None
            vertices.append((i, entering, exiting))
    
    # find index of first entering vertex
    ei = [entering for _, entering, _ in vertices].index(True)
    
    current = []
    inside, outside = [current], []
    # go through all vertices, starting with first entering one
    for i in range(len(vertices)):
        j = (ei + i) % len(vertices)
        p, entering, exiting = vertices[j]
        current.append(p)
        if exiting:
            current = [p]  # create new polygon
            outside.append(current)
        if entering:
            current = [p]  # create new polygon
            inside.append(current)
    # move the single-vertex polygon to the end of the last outside polygon
    tmp = inside.pop(0)
    outside[-1].extend(tmp)

    return inside, outside
