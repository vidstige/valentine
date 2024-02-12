from itertools import cycle
import os
import sys
import math
import random
from textwrap import wrap
from typing import BinaryIO, List, Tuple

import cairo
from PIL import Image
from shapely import Polygon, MultiPolygon, transform

from valentine.resolution import Resolution, parse_resolution
import valentine.zoom
import valentine.svg
from valentine.tween import Timeline, Linear, Constant, TweenSequence
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


def lerp(a: float, b: float, t: float) -> float:
    return (1 - t) * a + t * b


def clamp(t: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return min(max(t, lo), hi)


def draw(
    target: cairo.ImageSurface,
    timeline: Timeline,
    logo: List[Polygon],
    heart: List[Polygon],
    t: float,
) -> None:
    assert len(logo) == len(heart)
    eye = cairo.Matrix()
    ctx = cairo.Context(target)
    ctx.set_source_rgb(0.8, 0.8, 0.8)
    
    for polygon in heart:
        ctx.set_matrix(eye)
        y = timeline.tag('heart.y')(t)
        ctx.translate(0, y)
        draw_polygon(ctx, polygon)
        ctx.fill()


def load_svg(path: str, resolution: Resolution) -> MultiPolygon:
    """Loads path, converts to polygon(s) and translates/scales to resolution"""
    polygons = valentine.svg.load(path)
    zoom = valentine.zoom.zoom_to(polygons.bounds, resolution, padding=32)
    return transform(polygons, zoom.transform)


def animate(f: BinaryIO, resolution: Resolution, dt: float):        
    # cut polygons, first create templates
    random.seed(1337)
    templates = tony.create_templates(resolution, (7, 7), value=0.4)

    logo = tony.cut(load_svg('volumental.svg', resolution), templates)
    heart = tony.cut(load_svg('heart.svg', resolution), templates)

    # create timeline for pieces
    timeline = Timeline()
    timeline.add('heart.y', TweenSequence([
        Constant(-100, duration=0.5),
        Linear(-100, 0, duration=0.5),
        Constant(0, duration=1.0),
        Linear(0, 100, duration=1.0),
        Constant(100, duration=2.0),
    ]))

    width, height = resolution
    surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)

    t = 0
    duration = timeline.duration()
    while t < duration:
        clear(surface)
        draw(surface, timeline, logo, heart, t)
        f.write(surface.get_data())
        t += dt


def main():
    resolution = parse_resolution(os.environ.get('RESOLUTION', '720x720'))
    animate(sys.stdout.buffer, resolution, dt=1/40)


if __name__ == "__main__":
    main()
