from dataclasses import dataclass
import os
from typing import Iterable, Sequence, Tuple
from math import cos, sin, pi
import random
import sys

import cairo
from PIL import Image, ImageFilter
from svg.path import parse_path


random.seed(17)


Color = Tuple[float, float, float]


def parse_color(color: str) -> Color:
    c = color.lstrip('#')
    r, g, b = [int(c[i:i + 2], 16) / 255 for i in range(0, len(c), 2)]
    return r, g, b


def mix(x: Color, y: Color, t: float) -> Color:
    r, g, b = ((1-t) * xc + t * yc for xc, yc in zip(x, y))
    return r, g, b


@dataclass
class Gradient:
    stops: Sequence[Color]
    def sample(self, t: float) -> Color:
        n = (len(self.stops) - 1)
        i = int(t * n)
        return mix(self.stops[i], self.stops[i + 1], t - i / n)


def make_gradient(colors: Iterable[str]) -> Gradient:
    return Gradient(list(map(parse_color, colors)))


RAINBOW = list(map(parse_color, [
    '#FF000D',
    '#FF7034',
    '#FFFD01',
    '#66FF00',
    '#0165FC',
    '#6F00FE',
    '#AD0AFD',
]))
ARGON = make_gradient([
    '#03001e',
    '#7303c0',
    '#ec38bc',
    '#fdeff9',
])

def from_cairo(surface: cairo.ImageSurface) -> Image:
    assert surface.get_format() == cairo.FORMAT_ARGB32, "Unsupported pixel format: %s" % surface.get_format()
    return Image.frombuffer('RGBA', (surface.get_width(), surface.get_height()), bytes(surface.get_data()), 'raw')


def parse_resolution(resolution: str) -> Tuple[int, ...]:
    return tuple(int(d) for d in resolution.split('x'))


TAU = 2 * pi
RESOLUTION = parse_resolution(os.environ.get('RESOLUTION', '720x720'))


def clear(target: cairo.ImageSurface) -> None:
    ctx = cairo.Context(target)
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()


HEART = parse_path("M0 200 v-200 h200 a100,100 90 0,1 0,200 a100,100 90 0,1 -200,0 z")


def draw_fading_lines(ctx: cairo.Context, lines: Sequence[complex], color: Color, alpha_range: Tuple[float, float]):
    alpha_lo, alpha_hi = alpha_range
    ctx.move_to(lines[0].real, lines[0].imag)
    for i, p in enumerate(lines[1:]):
        alpha = alpha_lo + i * (alpha_hi - alpha_lo) / (len(lines) - 1)
        ctx.set_source_rgba(*color, alpha)
        ctx.line_to(p.real, p.imag)
        ctx.stroke()
        ctx.move_to(p.real, p.imag)


@dataclass
class Worm:
    color: Color
    length: float
    offset: float
    frequency: float
    amplitude: float
    phase: float



def generate_worms(n) -> Iterable[Worm]:
    rnd = random.normalvariate
    for _ in range(n):
        yield Worm(
            #color=random.choice(RAINBOW),
            color=ARGON.sample(random.uniform(0, 1)),
            length=rnd(0.1, 0.05),
            #offset=rnd(0, 0.03),
            offset=random.uniform(0, 1),
            frequency=rnd(8, 5),
            amplitude=rnd(8, 5),
            phase=random.uniform(0, TAU)
        )
   

WORMS = list(generate_worms(64))


def draw(target: cairo.ImageSurface, t: float, line_width: float) -> None:
    ctx = cairo.Context(target)
    #ctx.translate(200, 200)
    ctx.translate(target.get_width() / 2, target.get_height() / 2 + 200)
    ctx.rotate(-3/8*TAU)
    ctx.scale(1.5, 1.5)

    ctx.set_line_width(line_width)

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
        clear(surface)
        draw(surface, t, line_width=8)
        im = from_cairo(surface)
        blurred = im.filter(ImageFilter.GaussianBlur(radius=8))
        clear(surface)
        draw(surface, t, line_width=2)
        sharp = from_cairo(surface)
        final = Image.alpha_composite(blurred, sharp)
        f.write(final.tobytes())
        t += dt


def main():
    animate(sys.stdout.buffer, draw, dt=0.01)
    

if __name__ == "__main__":
    main()
