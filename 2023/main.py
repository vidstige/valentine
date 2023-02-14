from collections import deque
from functools import partial
from math import e, tau
import sys
from typing import Dict, List, Tuple

import cairo
import numpy as np
from numpy.lib.function_base import meshgrid
from svgpathtools import parse_path, Path, path_encloses_pt

from transform import transform
from perlin import generate_perlin_noise_2d


HEART = parse_path("M348.151,54.514c-19.883-19.884-46.315-30.826-74.435-30.826c-28.124,0-54.559,10.942-74.449,30.826l-9.798,9.8l-9.798-9.8 c-19.884-19.884-46.325-30.826-74.443-30.826c-28.117,0-54.56,10.942-74.442,30.826c-41.049,41.053-41.049,107.848,0,148.885 l147.09,147.091c2.405,2.414,5.399,3.892,8.527,4.461c1.049,0.207,2.104,0.303,3.161,0.303c4.161,0,8.329-1.587,11.498-4.764 l147.09-147.091C389.203,162.362,389.203,95.567,348.151,54.514z")


Color = Tuple[float, float, float]


def create_sdf(path: Path, size: Tuple[float, float], resolution: Tuple[int, int], n: int):
    x, y = np.meshgrid(
        np.linspace(0, size[0], resolution[0]),
        np.linspace(0, size[1], resolution[1]))
    grid = x + 1j * y
    sdf = np.inf * np.ones(resolution)
    for t in np.linspace(0, 1, n):
        p = path.point(t)
        d = np.abs(grid - p)
        sdf = np.minimum(sdf, d)
    
    return sdf


def create_inside_lookup(path: Path, size: Tuple[float, float], resolution: Tuple[int, int]) -> np.ndarray:
    inside = np.full(resolution, False)
    for xi, x in enumerate(np.linspace(0, size[0], resolution[0])):
        for yi, y in enumerate(np.linspace(0, size[1], resolution[1])):
            inside[yi, xi] = is_inside_path(path, x + 1j * y)

    return inside


def at(grid: np.ndarray, size: Tuple[float, float], p: complex) -> float:
    x = int(p.imag * grid.shape[0] / size[0])
    y = int(p.real * grid.shape[1] / size[1])
    return grid[x, y]


def encode_frame(im: np.ndarray) -> bytes:
    return (im * 255).astype(np.uint8).tobytes()


def from_gray(im: np.ndarray) -> np.ndarray:
    return np.dstack([im, im, im, np.ones_like(im)])


def autoscale(x: np.ndarray) -> np.ndarray:
    lo = np.min(x)
    hi = np.max(x)
    return (x - lo) / (hi - lo)


class Dot:
    def __init__(self, position: complex, velocity: complex):
        self.position = position
        self.velocity = velocity
        self.trace = deque()  # type: deque[complex]

    def update(self, acceleration: complex, dt: float) -> None:
        self.trace.appendleft(self.position)
        while len(self.trace) > 32:
            self.trace.pop()

        self.velocity += acceleration * dt
        self.position += self.velocity * dt

    def retract(self):
        """undoes last update"""
        self.position = self.trace.popleft()
        if self.trace:
            self.trace.pop()

    def respawn(self, position: complex, velocity: complex) -> None:
        self.trace.clear()
        self.position = position
        self.velocity = velocity


def is_inside(resolution: Tuple[int, int], p: complex):
    width, height = resolution
    return 0 < p.real < width and 0 < p.imag < height


def cuniform(size: Tuple[float, float]) -> complex:
    width, height = size    
    return complex(width * np.random.random(), height * np.random.random())


def random_dot(size: Tuple[float, float], v: float) -> Dot:
    return Dot(
        cuniform(size),
        v * e ** (tau * 1j * np.random.random()),
    )


def is_inside_path(path: Path, p: complex) -> bool:
    outside = -100 + -100j
    return path_encloses_pt(p, outside, path)


def clear(target: cairo.ImageSurface, color: Color) -> None:
    ctx = cairo.Context(target)
    ctx.set_source_rgb(*color)
    ctx.set_operator(cairo.OPERATOR_SOURCE)
    ctx.paint()


def draw(target: cairo.ImageSurface, dots: List[Dot], color: Color) -> None:
    ctx = cairo.Context(target)
    ctx.set_source_rgb(1, 1, 1)
    
    #r = 3
    ctx.set_line_width(1)
    ctx.set_source_rgb(*color)
    for dot in dots:
        for p in dot.trace:
            ctx.line_to(p.real, p.imag)
        ctx.stroke()
        #ctx.arc(dot.position.real, dot.position.imag, r, 0, tau)
        #ctx.fill()


gradient_cache = {}  # type: Dict[int, Tuple[np.ndarray, np.ndarray]]
def gradient(field: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    if id(field) in gradient_cache:
        return gradient_cache[id(field)]
    dy, dx = np.gradient(field)
    gradient_cache[id(field)] = (dx, dy)
    return dx, dy


def gradient_at(field: np.ndarray, size: Tuple[float, float], p: complex) -> complex:
    """computes the gradient of a fields as a complex (x + yi) coordinate"""
    # TODO: cache dx, dy
    dx, dy = gradient(field)
    return at(dx, size, p) + 1j * at(dy, size, p)


# spawning functions
def on_path(path: Path, t: float) -> Tuple[complex, complex]:
    if np.random.random() < 0.5:
        v = path.derivative(t) * e ** (tau * 0.10j)
    else:
        v = -path.derivative(t) * e ** (tau * -0.10j)

    return path.point(t), 50 * v / abs(v)

# along line
def along_line(p0: complex, p1: complex, v: complex, t: float) -> Tuple[complex, complex]:
    return p0 * (1 - t) + p1 * t, v


def along_field(field: np.ndarray, size: Tuple[float, float], t: float) -> Tuple[complex, complex]:
    del t
    p = cuniform(size)
    return p, -1j * gradient_at(field, size, p)


def main():
    path = transform(HEART, 0.50, 100 + 100j)

    N = 100
    G = 20
    dt = 0.025
    size = (400, 400)
    resolution = (800, 800)

    sdf = create_sdf(path, size, resolution, n=100)
    field = G * sdf
    #inside = create_inside_lookup(path, size, (50, 50))
    
    #rng = np.random.Generator(np.random.PCG64(1337))
    #field = G * generate_perlin_noise_2d(resolution, (5, 5), rng)

    #spawn = partial(on_path, path)
    #spawn = partial(along_line, 0, 1j*size[1], 50)
    spawn = partial(along_field, field, size)
    dots = [Dot(*spawn(t)) for t in np.random.random(N)]

    output_resolution = (400, 400)
    surface = cairo.ImageSurface(cairo.Format.ARGB32, *output_resolution)
    for t in np.arange(0, 60, dt):
        # step
        for dot in dots:
            dv = gradient_at(field, size, dot.position)
            #dv = at(dx, size, dot.position) + 1j * at(dy, size, dot.position)
            dot.update(-dv, dt)
            
            #if not is_inside(resolution, dot.position) or at(inside, size, dot.position):
            if not is_inside(size, dot.position):
                dot.retract()
                if not dot.trace:
                    dot.respawn(*spawn(np.random.random()))
        
        clear(surface, (1, 1, 1))
        draw(surface, dots, (0, 0, 0))
        
        sys.stdout.buffer.write(surface.get_data())
        #sys.stdout.buffer.write(encode_frame(from_gray(frame)))
        #sys.stdout.buffer.write(encode_frame(from_gray(autoscale(field))))


if __name__ == "__main__":
    main()
