import os
import sys
import random
import math
from typing import BinaryIO, Callable, Iterable, List, Optional, Tuple, TypeVar

import cairo
from PIL import Image, ImageFilter


Resolution = Tuple[int, int]


def parse_resolution(resolution: str) -> Resolution:
    width, height = (int(d) for d in resolution.split('x'))
    return width, height


TAU = 2 * math.pi
RESOLUTION = parse_resolution(os.environ.get('RESOLUTION', '720x720'))


def from_cairo(surface: cairo.ImageSurface) -> Image:
    assert surface.get_format() == cairo.FORMAT_ARGB32, "Unsupported pixel format: %s" % surface.get_format()
    return Image.frombuffer('RGBA', (surface.get_width(), surface.get_height()), bytes(surface.get_data()), 'raw')


def clear(target: cairo.ImageSurface) -> None:
    ctx = cairo.Context(target)
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()


def random_point(resolution: Resolution) -> Tuple[float, float]:
    width, height = resolution
    return random.random() * width, random.random() * height


Point = Tuple[int, int]
def lerp(a: Point, b: Point, t: float) -> Point:
    ax, ay = a
    bx, by = b
    return (1 - t) * ax + t * bx, (1 - t) * ay + t * by


LineSegment = Tuple[Point, Point]

def cross(a: Point, b: Point) -> float:
    ax, ay = a
    bx, by = b
    return ax * by - ay * bx


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


Polygon = List[Point]

from itertools import chain, tee

T = TypeVar('T')
def sides(iterable: Iterable[T]) -> Iterable[Tuple[T, T]]:
    a, b = tee(iterable)
    first = next(b, None)
    return zip(a, chain(b, (first,)))


import math
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


def draw_polygon(ctx: cairo.Context, polygon: Polygon) -> None:
    ctx.new_path()
    for x, y in polygon:
        ctx.line_to(x, y)
    ctx.close_path()


random.seed(1337)
polygon = [random_point(RESOLUTION) for _ in range(4)]
line = ((360, 0), (360, 720))
def draw(target: cairo.ImageSurface, t: float) -> None:
    ctx = cairo.Context(target)
    # draw line
    ctx.set_source_rgb(0.5, 0.5, 0.5)
    ctx.move_to(*line[0])
    ctx.line_to(*line[1])
    ctx.stroke()

    left_polygons, right_polygons = split(polygon, line)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_source_rgb(0.7, 0.1, 0.1)
    for p in left_polygons:
        draw_polygon(ctx, p)
    ctx.fill()
    ctx.set_source_rgb(0.1, 0.1, 0.7)
    for p in right_polygons:
        draw_polygon(ctx, p)
    ctx.fill()
    
    # draw original polyon
    ctx.set_source_rgb(0.6, 0.6, 0.6)
    ctx.set_dash([10, 5])
    draw_polygon(ctx, polygon)
    ctx.stroke()


def animate(f: BinaryIO, draw: Callable[[cairo.ImageSurface, float], None], dt: float):
    width, height = RESOLUTION
    surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)
    
    t = 0
    while t < 1:
        clear(surface)
        draw(surface, t)
        f.write(surface.get_data())
        t += dt


def main():
    animate(sys.stdout.buffer, draw, dt=0.008)
    

if __name__ == "__main__":
    main()
