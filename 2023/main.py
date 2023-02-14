from collections import deque
from functools import partial
from math import e, tau
import sys
from typing import Callable, Dict, List, Tuple, TypeVar

import cairo
import numpy as np
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


def at_lerp(grid: np.ndarray, size: Tuple[float, float], p: complex) -> float:
    x0 = int(p.imag * grid.shape[0] / size[0])
    y0 = int(p.real * grid.shape[1] / size[1])
    x1, y1 = x0 + 1, y0 + 1
    g00 = grid[x0, y0]
    g10 = grid[x1, y0]
    g11 = grid[x1, y1]
    g01 = grid[x0, y1]
    return (g00 + g10 + g11 + g01) / 4


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
        self.trace = deque()  # type: deque[Tuple[complex, complex]]

    def update(self, acceleration: complex, dt: float) -> None:
        self.trace.appendleft((self.position, self.velocity))
        while len(self.trace) > 32:
            self.trace.pop()

        self.velocity += acceleration * dt
        self.position += self.velocity * dt

    def damp(self, damping: float) -> None:
        self.velocity *= (1.0 - damping)

    def retract(self):
        """undoes last update"""
        self.position, self.velocity = self.trace.popleft()
        #self.velocity = 0
        if self.trace:
            self.trace.pop()

    def respawn(self, position: complex, velocity: complex) -> None:
        self.trace.clear()
        self.position = position
        self.velocity = velocity


def is_inside(resolution: Tuple[int, int], p: complex):
    width, height = resolution
    return 0 < p.real < width and 0 < p.imag < height


def cuniform(rng: np.random.Generator, size: Tuple[float, float]) -> complex:
    width, height = size    
    return complex(width * rng.random(), height * rng.random())


def random_dot(rng: np.random.Generator, size: Tuple[float, float], v: float) -> Dot:
    return Dot(
        cuniform(rng, size),
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


def draw(target: cairo.ImageSurface, dots: List[Dot], color: Color, line_width: float) -> None:
    ctx = cairo.Context(target)
    ctx.set_source_rgb(1, 1, 1)
    
    #r = 3
    ctx.set_line_width(line_width)
    ctx.set_source_rgb(*color)
    for dot in dots:
        for p, _ in dot.trace:
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


def gradient_at(field: np.ndarray, size: Tuple[float, float], p: complex, at: Callable[[np.ndarray, Tuple[float, float], complex], float]=at) -> complex:
    """computes the gradient of a fields as a complex (x + yi) coordinate"""
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
def along_line(rng: np.random.Generator, field: np.ndarray, p0: complex, p1: complex, v: complex) -> Tuple[complex, complex]:
    del field
    t = rng.random()
    return p0 * (1 - t) + p1 * t, v


def sample_2d(rng: np.random.Generator, pdf: np.ndarray):
    index = rng.choice(np.arange(pdf.size), p=pdf.ravel())
    return np.unravel_index(index, pdf.shape)


def as_pdf(field: np.ndarray):
    lo = np.min(field)
    hi = np.max(field)
    pdf = hi - field  # reverse and move to zero
    return pdf / np.sum(pdf)


def to_size(c: complex, size: Tuple[float, float], resolution: Tuple[int, int]) -> complex:
    return complex(
        c.real * size[0] / resolution[0],
        c.imag * size[1] / resolution[1],
    )

def field_resolution(field: np.ndarray) -> Tuple[int, int]:
    width, height = field.shape
    return width, height
    

def along_field(rng: np.random.Generator, field: np.ndarray, size: Tuple[float, float], v: float) -> Tuple[complex, complex]:
    #p = cuniform(rng, size)
    p = to_size(complex(*sample_2d(rng, pdf=as_pdf(field))), size, field_resolution(field))
    
    #return p, rng.choice((-1, 1)) * v * -1j * gradient_at(field, size, p)
    return p, v * -1j * gradient_at(field, size, p)


def everywhere(rng: np.random.Generator, field: np.ndarray, size: Tuple[float, float], v: complex) -> Tuple[complex, complex]:
    del field
    return cuniform(rng, size), v


Spawn = Callable[[np.random.Generator, np.ndarray], Tuple[complex, complex]]
T = TypeVar('T')
class Timeline:
    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.fields = []  # type: List[Tuple[float, np.ndarray]]
        self.spawns = []  # type: List[Tuple[float, Spawn]]
        self.dampings = []  # type: List[Tuple[float, float]]

    def _first(self, items: List[Tuple[float, T]], t: float) -> T:
        for start, item in items:
            if t >= start:
                return item
        raise Exception(f'not found for time {t}')

    def add(self, field: np.ndarray, t: float) -> None:
        self.fields.append((t, field))
        self.fields.sort(reverse=True)

    def add_spawn(self, spawn: Spawn, t: float) -> None:
        self.spawns.append((t, spawn))
        self.spawns.sort(reverse=True)

    def field(self, t: float) -> np.ndarray:
        """Returns the vector field at time t"""
        return self._first(self.fields, t)
    
    def spawn(self, t: float) -> Tuple[complex, complex]:
        spawn = self._first(self.spawns, t)
        field = self.field(t)
        return spawn(self.rng, field)
        
    def add_damping(self, damping: float, t: float) -> None:
        self.dampings.append((t, damping))
        self.dampings.sort(reverse=True)

    def damping(self, t: float) -> float:
        return self._first(self.dampings, t)


def fit_to(path: Path, size: Tuple[float, float], padding_fraction: float=0) -> Path:
    """Rescales cordinates to fit a specific resolution with paddning"""    
    xmin, xmax, ymin, ymax = path.bbox()
    w, h = xmax - xmin, ymax - ymin
    scale = (1 - padding_fraction) * max(size) / max(w, h)
    return transform(path, scale, complex(xmin, ymin) + complex(w, h) * padding_fraction)


def main():
    #scale = 1
    #path = transform(HEART, 1.0, 0.5*(720 - scale*400) + 0.5*(720j - scale*400j))

    N = 1024
    LINE_WIDTH = 0.1
    G = 500
    dt = 0.025
    size = (720, 720)
    resolution = (400, 400)

    path = fit_to(HEART, size, padding_fraction=0.5)

    rng = np.random.Generator(np.random.PCG64(1337))
    timeline = Timeline(rng)
    timeline.add(G * 5 * generate_perlin_noise_2d(resolution, (5, 5), rng), 0)
    timeline.add_spawn(partial(everywhere, size=size, v=200), 0)
    timeline.add_spawn(partial(along_line, p0=0, p1=1j*size[1], v=200), 0.1)
    timeline.add_damping(0, 0)

    timeline.add(G * create_sdf(path, size, resolution, n=100), 4)
    timeline.add_spawn(partial(along_field, size=size, v=0.051), 4)
    timeline.add_damping(0.005, 4)
    
    dots = [Dot(*timeline.spawn(0.0)) for _ in range(N)]

    #output_resolution = (400, 400)
    output_resolution = (720, 720)
    surface = cairo.ImageSurface(cairo.Format.ARGB32, *output_resolution)
    for t in np.arange(0, 30, dt):
        field = timeline.field(t)

        # step
        for dot in dots:
            dv = gradient_at(field, size, dot.position)
            dot.update(-dv, dt)
            dot.damp(timeline.damping(t))
            
            #if not is_inside(resolution, dot.position) or at(inside, size, dot.position):
            if not is_inside((size[0] - 1, size[1] - 1), dot.position):
                dot.retract()
                if not dot.trace:
                    #print('spawning new line', file=sys.stderr)
                    dot.respawn(*timeline.spawn(t))

        clear(surface, (1, 1, 1))
        draw(surface, dots, (0, 0, 0), line_width=LINE_WIDTH)
        
        sys.stdout.buffer.write(surface.get_data())
        #sys.stdout.buffer.write(encode_frame(from_gray(frame)))
        #sys.stdout.buffer.write(encode_frame(from_gray(autoscale(field))))


if __name__ == "__main__":
    main()
