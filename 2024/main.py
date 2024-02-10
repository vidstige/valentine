from itertools import cycle
import os
import sys
import math
from typing import BinaryIO, Callable

import cairo
from PIL import Image
from shapely import Polygon, transform

from valentine.resolution import parse_resolution
import valentine.zoom
import valentine.svg
from valentine import tony

TAU = 2 * math.pi
RESOLUTION = parse_resolution(os.environ.get('RESOLUTION', '720x720'))


def from_cairo(surface: cairo.ImageSurface) -> Image:
    assert surface.get_format() == cairo.FORMAT_ARGB32, "Unsupported pixel format: %s" % surface.get_format()
    return Image.frombuffer('RGBA', (surface.get_width(), surface.get_height()), bytes(surface.get_data()), 'raw')


def clear(target: cairo.ImageSurface) -> None:
    ctx = cairo.Context(target)
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()


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

    lines = list(tony.grid(RESOLUTION, (5, 5)))

    width, height = RESOLUTION
    surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)    
    
    # cut polygons
    pieces = tony.cut(polygons, lines)

    clear(surface)    

    ctx = cairo.Context(surface)
    ctx.set_source_rgb(0.4, 0.4, 0.4)
    ctx.set_dash([10, 5])
    for line in lines:
        ctx.new_path()
        for x, y in line.coords:
            ctx.line_to(x, y)
        ctx.stroke()

    colors = [
        (0.6, 0.6, 0.8),
        (0.8, 0.6, 0.6),
        (0.6, 0.8, 0.6),
    ]
    for polygon, color in zip(pieces.geoms, cycle(colors)):
        ctx.set_source_rgb(*color)
        draw_polygon(ctx, polygon)
        ctx.fill()

    
    sys.stdout.buffer.write(surface.get_data())

    #animate(sys.stdout.buffer, draw, dt=0.008)

if __name__ == "__main__":
    main()
