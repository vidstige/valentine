import os
from typing import Tuple

import cairo
from svg.path import parse_path


def parse_resolution(resolution: str) -> Tuple[int, ...]:
    return tuple(int(d) for d in resolution.split('x'))


RESOLUTION = parse_resolution(os.environ.get('RESOLUTION', '720x720'))


def clear(target: cairo.ImageSurface, color=(1, 1, 1)) -> None:
    r, g, b = color
    ctx = cairo.Context(target)
    ctx.rectangle(0, 0, target.get_width(), target.get_height())
    ctx.set_source_rgb(r, g, b)
    ctx.fill()


HEART = parse_path("M0 200 v-200 h200 a100,100 90 0,1 0,200 a100,100 90 0,1 -200,0 z")

def p(c: complex) -> Tuple[float, float]:
    return c.real, c.imag

def draw(target: cairo.Surface, t: float) -> None:
    ctx = cairo.Context(target)
    ctx.scale(1, 1)
    ctx.translate(200, 200)
    ctx.set_line_width(1)
    ctx.set_source_rgba(1, 1, 1)

    ctx.move_to(*p(HEART.point(0)))
    n = 100
    for s in range(1, n + 1):
        ctx.line_to(*p(HEART.point(s / n)))

    ctx.stroke()


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
    
    animate(sys.stdout.buffer, draw, dt=0.1)
    

if __name__ == "__main__":
    main()
