from dataclasses import dataclass
import os
from typing import Iterable, Sequence, Tuple
from math import cos, sin, pi
import random
import sys

import cairo
from PIL import Image, ImageFilter
from svg.path import parse_path


def from_cairo(surface: cairo.ImageSurface) -> Image:
    assert surface.get_format() == cairo.FORMAT_ARGB32, "Unsupported pixel format: %s" % surface.get_format()
    return Image.frombuffer('RGBA', (surface.get_width(), surface.get_height()), bytes(surface.get_data()), 'raw')


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


def draw_fading_lines(ctx: cairo.Context, lines: Sequence[complex], color: Tuple[float, float, float], alpha_range: Tuple[float, float]):
    alpha_lo, alpha_hi = alpha_range
    ctx.move_to(lines[0].real, lines[0].imag)
    for i, p in enumerate(lines[1:]):
        alpha = alpha_lo + i * (alpha_hi - alpha_lo) / (len(lines) - 1)
        ctx.set_source_rgba(*color, alpha)
        ctx.line_to(p.real, p.imag)
        ctx.stroke()
        ctx.move_to(p.real, p.imag)


def parse_color(color: str) -> Tuple[float, float, float]:
    c = color.lstrip('#')
    r, g, b = [int(c[i:i + 2], 16) / 255 for i in range(0, len(c), 2)]
    return r, g, b


RAINBOW = list(map(parse_color, [
    '#FF000D',
    '#FF7034',
    '#FFFD01',
    '#66FF00',
    '#0165FC',
    '#6F00FE',
    '#AD0AFD',
]))

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
            color=random.choice(RAINBOW),
            length=rnd(0.1, 0.05),
            #offset=rnd(0, 0.03),
            offset=random.uniform(0, 1),
            frequency=rnd(8, 5),
            amplitude=rnd(8, 5),
            phase=random.uniform(0, TAU)
        )
   

WORMS = list(generate_worms(64))


def draw(target: cairo.ImageSurface, t: float) -> None:
    ctx = cairo.Context(target)
    #ctx.translate(200, 200)
    ctx.translate(target.get_width() / 2, target.get_height() / 2 + 200)
    ctx.rotate(-3/8*TAU)
    ctx.scale(1.5, 1.5)

    ctx.set_line_width(4)

    n = 32
    for worm in WORMS:
        lines = []
        for i in range(n):
            s = (t + worm.offset - worm.length * i / n) % 1
            p = HEART.point(s)
            tangent = HEART.tangent(s)
            if abs(tangent) > 1e-10:
                normal = (tangent / abs(tangent)) * -1j
                offset = worm.amplitude * sin(worm.frequency * TAU * s + worm.phase)
                lines.append(p + offset *  normal)

        draw_fading_lines(ctx, lines, worm.color, (1, 0))


def animate(f, draw, dt):
    width, height = RESOLUTION
    surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)
    t = 0
    while t < 1:
        clear(surface, color=(0, 0, 0))
        draw(surface, t)
        im = from_cairo(surface)
        f.write(im.tobytes())
        t += dt


def main():
    animate(sys.stdout.buffer, draw, dt=0.01)
    

if __name__ == "__main__":
    main()
