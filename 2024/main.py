import os
import sys
import random
import math
from typing import BinaryIO, Callable, Iterable

import cairo
from PIL import Image
import svg.path

from valentine.resolution import Resolution, parse_resolution
from valentine.linesegment import Point
from valentine.polygon import Polygon, split
import valentine.zoom
import valentine.svg


TAU = 2 * math.pi
RESOLUTION = parse_resolution(os.environ.get('RESOLUTION', '720x720'))


def from_cairo(surface: cairo.ImageSurface) -> Image:
    assert surface.get_format() == cairo.FORMAT_ARGB32, "Unsupported pixel format: %s" % surface.get_format()
    return Image.frombuffer('RGBA', (surface.get_width(), surface.get_height()), bytes(surface.get_data()), 'raw')


def clear(target: cairo.ImageSurface) -> None:
    ctx = cairo.Context(target)
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()


def random_point(resolution: Resolution) -> Point:
    width, height = resolution
    return random.random() * width, random.random() * height


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


def is_polygon(path: svg.path.Path) -> bool:
    return all(isinstance(segment, svg.path.Linear) for segment in path)


def to_point(c: complex) -> Point:
    return c.real, c.imag


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

def to_polygons(path: svg.path.Path) -> Iterable[Polygon]:
    for segment in path:
        if is_polygon(segment):
            polygon = []
            for line in segment:
                assert isinstance(line, svg.path.Linear)
                polygon.append(to_point(line.start))
            yield polygon
        else:
            # sample shape at 32 points
            n = 32
            for subpath in split_on_move(segment):
                ts = (i / n for i in range(n))
                polygon = [to_point(subpath.point(t)) for t in ts]
                yield polygon


def main():
    paths = valentine.svg.load('volumental.svg')
    polygons = list(to_polygons(paths))
    points = [p for polygon in polygons for p in polygon]
    zoom = valentine.zoom.zoom_to(points, RESOLUTION, padding=32)
    polygons = [[zoom.transform(p) for p in polygon] for polygon in polygons]

    width, height = RESOLUTION
    surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)    
    
    clear(surface)
    
    ctx = cairo.Context(surface)
    #ctx.scale(4, 4)
    #ctx.set_line_width(2 / 4)
    #ctx.translate(0.0, 20.0)
    ctx.set_source_rgb(0.8, 0.6, 0.8)
    for polygon in polygons:
        draw_polygon(ctx, polygon)
        ctx.stroke()

    sys.stdout.buffer.write(surface.get_data())

    #animate(sys.stdout.buffer, draw, dt=0.008)

if __name__ == "__main__":
    main()
