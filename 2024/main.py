from itertools import cycle
import os
import sys
import random
import math
from typing import BinaryIO, Callable

import cairo
from PIL import Image
from shapely import Polygon, transform

from valentine.resolution import Resolution, parse_resolution
from valentine.linesegment import Point
import valentine.zoom
import valentine.svg
from valentine.tony import cut_all, tony

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
    for x, y in polygon.exterior.coords:
        ctx.line_to(x, y)
    for hole in polygon.interiors:
        for x, y in hole.coords:
            ctx.line_to(x, y)
    ctx.close_path()


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
    polygons = valentine.svg.load('volumental.svg')
    zoom = valentine.zoom.zoom_to(polygons.bounds, RESOLUTION, padding=32)
    polygons = transform(polygons, zoom.transform)

    lines = list(tony(RESOLUTION, (5, 5)))

    width, height = RESOLUTION
    surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)    
    
    clear(surface)
    
    ctx = cairo.Context(surface)

    ctx.set_source_rgb(0.4, 0.4, 0.4)
    ctx.set_dash([10, 5])
    for a, b in lines:
        ctx.move_to(*a)
        ctx.line_to(*b)
        ctx.stroke()

    colors = [
        (0.6, 0.6, 0.8),
        (0.8, 0.6, 0.6),
        (0.6, 0.8, 0.6),
    ]
    for polygon in polygons.geoms:
        draw_polygon(ctx, polygon)
        ctx.fill()

    
    sys.stdout.buffer.write(surface.get_data())

    #animate(sys.stdout.buffer, draw, dt=0.008)

if __name__ == "__main__":
    main()
