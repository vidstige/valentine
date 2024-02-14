from collections import deque
from itertools import count, cycle
import os
import sys
import math
import random
from typing import BinaryIO, Iterable, List, Optional

import cairo
import numpy as np
from PIL import Image
from shapely import Polygon, MultiPolygon, transform

from valentine import color
from valentine.resolution import Resolution, parse_resolution
import valentine.zoom
import valentine.svg
from valentine.tween import EaseInQuad, EaseOutQuad, Timeline, Linear, Constant, TweenSequence
from valentine import tony

TAU = 2 * math.pi


def from_cairo(surface: cairo.ImageSurface) -> Image:
    assert surface.get_format() == cairo.FORMAT_ARGB32, "Unsupported pixel format: %s" % surface.get_format()
    return Image.frombuffer('RGBA', (surface.get_width(), surface.get_height()), bytes(surface.get_data()), 'raw')


def clear(target: cairo.ImageSurface, background: Optional[cairo.Pattern]) -> None:
    ctx = cairo.Context(target)
    if background:
        ctx.set_source(background)
    else:
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

from valentine.tween.tweens import ease_in_quad

def phase(rng: float) -> float:
    """Computes phase for location"""
    return ease_in_quad(rng) * 3


def draw(
    target: cairo.ImageSurface,
    foreground: cairo.Pattern,
    timeline: Timeline,
    rngs: List[float],
    logo: List[Polygon],
    heart: List[Polygon],
    t: float,
) -> None:
    assert len(logo) == len(heart)
    camera = cairo.Matrix()
    ctx = cairo.Context(target)
    ctx.set_source(foreground)

    # compute camera shake amplitude
    heart_amplitude = sum(timeline.tag('heart.shake')(t + phase(rng)) for rng in rngs)
    logo_amplitude = sum(timeline.tag('logo.shake')(t + phase(rng)) for rng in rngs)
    amplitude = 1.5 * (heart_amplitude + logo_amplitude)
    # use time as shake phase
    theta = t * 1337
    
    camera.translate(target.get_width() / 2, target.get_height() / 2)
    camera.translate(math.cos(theta) * amplitude, math.sin(theta) * amplitude)
    camera.rotate(math.sin(amplitude*100) * 0.01)
    camera.translate(-target.get_width() / 2, -target.get_height() / 2)

    for rng, logo_piece, heart_piece in zip(rngs, logo, heart):
        # draw heart piece
        if not heart_piece.is_empty:
            y = timeline.tag('heart.y')((t + phase(rng)) % timeline.duration())
            ctx.set_matrix(camera)
            ctx.translate(0, y)
            # rotate around center
            center = heart_piece.centroid
            ctx.translate(center.x, center.y)
            ctx.rotate(y / 200)
            ctx.translate(-center.x, -center.y)
            draw_polygon(ctx, heart_piece)
            ctx.fill()

        # draw logo piece
        if not logo_piece.is_empty:
            ctx.set_matrix(camera)
            y = timeline.tag('logo.y')((t + phase(rng)) % timeline.duration())
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
        EaseInQuad(-height, 0, duration=0.50),
        Constant(0, duration=3.0),
        EaseOutQuad(0, height, duration=0.8),
        Constant(height, duration=2.0),
    ]))
    heart_duration = timeline.tag('heart.y').duration()
    timeline.add('logo.y', TweenSequence([
        Constant(-height, duration=0.75 * heart_duration),
        EaseInQuad(-height, 0, duration=0.50),
        Constant(0, duration=3.0),
        EaseOutQuad(0, height, duration=0.8),
        Constant(height, duration=0.2),
    ]))
    timeline.add('heart.shake', TweenSequence([
        Constant(0, duration=3 + 0.5), # don't shake until first two tweens are done
        EaseInQuad(1, 0, duration=dt * 3),  # shake for n frames
        Constant(0, duration=1),
    ]))
    timeline.add('logo.shake', TweenSequence([
        Constant(0, duration=0.75 * heart_duration + 0.5),  # wait until logo starts falling
        EaseInQuad(1, 0, duration=dt * 3),  # shake for n frames
        Constant(0, duration=1),
    ]))

    # each location has a random value called "rng" for it's properties
    rngs = [random.random() for _ in range(tony.area(grid))]

    width, height = resolution
    surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)

    # foreground
    # https://uigradients.com/#PurpleLove
    foreground = color.gradient(resolution, ['#cc2b5e', '#753a88'])

    # https://uigradients.com/#Clouds
    background = color.gradient(resolution, ['#ECE9E6', '#FFFFFF'])

    # thumb
    #clear(surface, background)
    #draw(surface, foreground, timeline, phases, logo, heart, t=2.8)
    #surface.write_to_png('debug.png')
    
    t = 0
    duration = timeline.duration()
    while t < duration:
        clear(surface, background)
        #frames = []
        #for i in range(8):
        #    draw(surface, timeline, phases, logo, heart, t - i * dt * 0.2)
        #    frames.append(as_array(surface))
        #buffer = motion_blur(frames).tobytes()
        
        draw(surface, foreground, timeline, rngs, logo, heart, t)
        buffer = surface.get_data()
        f.write(buffer)
        t += dt


def main():
    resolution = parse_resolution(os.environ.get('RESOLUTION', '720x720'))
    animate(sys.stdout.buffer, resolution, dt=1/60)


if __name__ == "__main__":
    main()
