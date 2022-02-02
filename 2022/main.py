from dataclasses import dataclass
import os
from typing import Iterable, Sequence, Tuple
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


@dataclass
class Worm:
    color: Tuple[float, float, float]
    length: float
    offset: float
    frequency: float
    amplitude: float
    phase: float



def generate_worms(n) -> Iterable[Worm]:
    rnd = random.normalvariate
    for _ in range(n):
        yield Worm(
            color=(1, 1, 1),
            length=rnd(0.1, 0.05),
            offset=rnd(0, 0.03),
            frequency=rnd(10, 5),
            amplitude=rnd(8, 5),
            phase=random.uniform(0, TAU)
        )
   

WORMS = list(generate_worms(8))


def draw(target: cairo.Surface, t: float) -> None:
    ctx = cairo.Context(target)
    ctx.scale(1, 1)
    ctx.translate(200, 200)
    ctx.set_line_width(2)

    n = 10
    for worm in WORMS:
        ctx.set_source_rgba(*worm.color)
        lines = []
        for i in range(n):
            s = (t + worm.offset - worm.length * i / n) % 1
            p = HEART.point(s)
            tangent = HEART.tangent(s)
            if abs(tangent) > 1e-10:
                normal = (tangent / abs(tangent)) * -1j
                offset = worm.amplitude * sin(worm.frequency * TAU * s + worm.phase)
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
