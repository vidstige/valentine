from typing import Optional, Tuple


Point = Tuple[int, int]
LineSegment = Tuple[Point, Point]


def lerp(a: Point, b: Point, t: float) -> Point:
    ax, ay = a
    bx, by = b
    return (1 - t) * ax + t * bx, (1 - t) * ay + t * by


def intersection(ls0: LineSegment, ls1: LineSegment) -> Optional[Point]:
    (x1, y1), (x2, y2) = ls0
    (x3, y3), (x4, y4) = ls1
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(d) < 1e-7:
        # lines (almost) parallel
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
    u = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3))  / d
    # TODO: Allow cutting line to extend indefinataly
    if t < 0 or t >= 1 or u < 0 or u >= 1:
        # intersection outside linesegments
        return None
    # intersection found - compute intersection point using t (u could also be used)
    return lerp(*ls0, t)
