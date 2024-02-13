from collections import deque
from itertools import count, cycle
import os
import sys
import math
import random
from textwrap import wrap
from typing import BinaryIO, Iterable, List, Tuple

import cairo
import numpy as np
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
    phases: List[float],
    logo: List[Polygon],
    heart: List[Polygon],
    t: float,
) -> None:
    assert len(logo) == len(heart)
    eye = cairo.Matrix()
    ctx = cairo.Context(target)
    ctx.set_source_rgb(0.8, 0.8, 0.8)
    
    for phase, logo_piece, heart_piece in zip(phases, logo, heart):
        # draw heart piece
        ctx.set_matrix(eye)
        y = timeline.tag('heart.y')((t + phase) % timeline.duration())
        ctx.translate(0, y)
        draw_polygon(ctx, heart_piece)
        ctx.fill()

        # draw logo piece
        ctx.set_matrix(eye)
        y = timeline.tag('logo.y')((t + phase) % timeline.duration())
        ctx.translate(0, y)
        draw_polygon(ctx, logo_piece)
        ctx.fill()


def load_svg(path: str, resolution: Resolution) -> MultiPolygon:
    """Loads path, converts to polygon(s) and translates/scales to resolution"""
    polygons = valentine.svg.load(path)
    zoom = valentine.zoom.zoom_to(polygons.bounds, resolution, padding=32)
    return transform(polygons, zoom.transform)


def as_array(surface: cairo.ImageSurface) -> np.ndarray:
    width, height = surface.get_width(), surface.get_height()
    return np.ndarray(
        shape=(height, width, 4),
        dtype=np.uint8,
        buffer=surface.get_data(),
    ).copy()


def motion_blur(frames: Iterable[np.ndarray]) -> np.ndarray:
    array = np.stack([frame.astype(np.uint32) for frame in frames], axis=-1)
    return np.mean(array, axis=-1).astype(np.uint8)


def animate(f: BinaryIO, resolution: Resolution, dt: float):        
    # cut polygons, first create templates
    random.seed(1337)
    grid = (7, 7)
    templates = tony.create_templates(resolution, grid, value=0.4)

    logo = tony.cut(load_svg('volumental.svg', resolution), templates)
    heart = tony.cut(load_svg('heart.svg', resolution), templates)

    # create timeline for pieces
    timeline = Timeline()
    _, height = resolution
    timeline.add('heart.y', TweenSequence([
        Constant(-height, duration=3.0),
        Linear(-height, 0, duration=0.50),
        Constant(0, duration=3.0),
        Linear(0, height, duration=0.8),
        Constant(height, duration=2.0),
    ]))
    heart_duration = timeline.tag('heart.y').duration()
    timeline.add('logo.y', TweenSequence([
        Constant(-height, duration=0.75 * heart_duration),
        Linear(-height, 0, duration=0.50),
        Constant(0, duration=3.0),
        Linear(0, height, duration=0.8),
        Constant(height, duration=0.5),
    ]))

    # phases
    phases = [random.random() * 3 for _ in range(tony.area(grid))]

    width, height = resolution
    surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)

    t = 0
    duration = timeline.duration()
    while t < duration:
        clear(surface)
        #frames = []
        #for i in range(8):
        #    draw(surface, timeline, phases, logo, heart, t - i * dt * 0.2)
        #    frames.append(as_array(surface))
        #buffer = motion_blur(frames).tobytes()
        
        draw(surface, timeline, phases, logo, heart, t)
        buffer = surface.get_data()
        f.write(buffer)
        t += dt


def main():
    resolution = parse_resolution(os.environ.get('RESOLUTION', '720x720'))
    animate(sys.stdout.buffer, resolution, dt=1/60)


if __name__ == "__main__":
    main()
