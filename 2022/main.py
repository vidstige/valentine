import os
from typing import List, Sequence, Tuple
from math import cos, sin, pi
import random

import cairo
from svg.path import parse_path


def parse_resolution(resolution: str) -> Tuple[int, ...]:
    return tuple(int(d) for d in resolution.split('x'))


TAU = 2 * pi
RESOLUTION = parse_resolution(os.environ.get('RESOLUTION', '720x720'))


def clear(target: cairo.ImageSurface, color=(1, 1, 1)) -> None:
    r, g, b = color
    ctx = cairo.Context(target)
    ctx.rectangle(0, 0, target.get_width(), target.get_height())
    ctx.set_source_rgb(r, g, b)
    ctx.fill()


HEART = parse_path("M0 200 v-200 h200 a100,100 90 0,1 0,200 a100,100 90 0,1 -200,0 z")


def draw_lines(ctx: cairo.Context, lines: Sequence[complex]):
    ctx.move_to(lines[0].real, lines[0].imag)
    for p in lines[1:]:
        ctx.line_to(p.real, p.imag)
    ctx.stroke()


def draw(target: cairo.Surface, t: float) -> None:
    ctx = cairo.Context(target)
    ctx.scale(1, 1)
    ctx.translate(200, 200)
    ctx.set_line_width(2)
    ctx.set_source_rgba(1, 1, 1)

    line_length = 0.05
    n = 10
    lines = []
    for i in range(n):
        s = (line_length * i / n + t) % 1
        p = HEART.point(s)
        tangent = HEART.tangent(s)
        if abs(tangent) > 1e-10:
            normal = (tangent / abs(tangent)) * -1j
            offset = 5 * sin(10 * TAU * s)
            lines.append(p + offset *  normal)

    draw_lines(ctx, lines)


def animate(f, draw, dt):
    width, height = RESOLUTION
    surface = cairo.ImageSurface(cairo.Format.RGB24, width, height)
    t = 0
    while t < 10:
        clear(surface, color=(0, 0, 0))
        draw(surface, t)
        f.write(surface.get_data())
        t += dt


def main():
    import sys
    
    animate(sys.stdout.buffer, draw, dt=0.01)
    

if __name__ == "__main__":
    main()
