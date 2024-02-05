import os
import sys
import random
import math
from typing import BinaryIO, Callable, Tuple

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
LineSegment = Tuple[Point, Point]
def distance_to(linesegment: LineSegment, p: Point) -> float:
    (ax, ay), (bx, by) = linesegment
    x, y = p
    return (bx - ax) * (y - ay) - (by - ay) * (x - a.x)


polygon = [random_point(RESOLUTION) for _ in range(4)]
line = ((360, 0), (360, 720))
def draw(target: cairo.ImageSurface, t: float) -> None:
    ctx = cairo.Context(target)

    ctx.set_source_rgb(0.7, 0.1, 0.7)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    
    ctx.new_path()
    for x, y in polygon:
        ctx.line_to(x, y)
    ctx.close_path()
    
    ctx.fill()
    #context.clip_preserve()


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
