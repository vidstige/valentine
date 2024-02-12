from itertools import cycle
import os
import sys
import math
from textwrap import wrap
from typing import BinaryIO, List, Tuple

import cairo
from PIL import Image
from shapely import Polygon, MultiPolygon, transform

from valentine.resolution import Resolution, parse_resolution
import valentine.zoom
import valentine.svg
from valentine import tony

TAU = 2 * math.pi


def parse_color(color: str) -> Tuple[float, float, float]:
    return tuple(int(channel, 16) / 255 for channel in wrap(color.removeprefix('#'), 2))


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


def draw(surface: cairo.ImageSurface, pieces: List[Polygon], t: float) -> None:
    pass


def load_svg(path: str, resolution: Resolution) -> MultiPolygon:
    """Loads path, converts to polygon(s) and translates/scales to resolution"""
    polygons = valentine.svg.load(path)
    zoom = valentine.zoom.zoom_to(polygons.bounds, resolution, padding=32)
    return transform(polygons, zoom.transform)


def animate(f: BinaryIO, resolution: Resolution, dt: float):        
    #polygons = load_svg('volumental.svg')
    polygons = load_svg('heart.svg', resolution)

    # cut polygons
    lines = list(tony.grid(resolution, (7, 7), value=0.4))
    pieces = tony.cut(polygons, lines)

    width, height = resolution
    surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)

    t = 0
    while t < 1:
        clear(surface)
        draw(surface, pieces, t)
        f.write(surface.get_data())
        t += dt


def main():
    resolution = parse_resolution(os.environ.get('RESOLUTION', '720x720'))
    animate(sys.stdout.buffer, resolution, dt=0.008)


if __name__ == "__main__":
    main()
