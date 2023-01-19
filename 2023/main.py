from math import e, tau
import sys
from typing import Tuple

import numpy as np
from svg.path import parse_path, Path

from transform import transform


HEART = parse_path("M348.151,54.514c-19.883-19.884-46.315-30.826-74.435-30.826c-28.124,0-54.559,10.942-74.449,30.826l-9.798,9.8l-9.798-9.8 c-19.884-19.884-46.325-30.826-74.443-30.826c-28.117,0-54.56,10.942-74.442,30.826c-41.049,41.053-41.049,107.848,0,148.885 l147.09,147.091c2.405,2.414,5.399,3.892,8.527,4.461c1.049,0.207,2.104,0.303,3.161,0.303c4.161,0,8.329-1.587,11.498-4.764 l147.09-147.091C389.203,162.362,389.203,95.567,348.151,54.514z")


def create_sdf(path: Path, size: Tuple[float, float], resolution: Tuple[int, int], n: int):
    x, y = np.meshgrid(
        np.linspace(0, size[0], resolution[0]),
        np.linspace(0, size[1], resolution[1]))
    center = complex(resolution[0], resolution[1]) * 0.5
    grid = x + 1j * y
    sdf = np.inf * np.ones(resolution)
    for t in np.linspace(0, 1, n):
        p = path.point(t) * 0.5 + center * 0.5
        d = np.abs(grid - p)
        sdf = np.minimum(sdf, d)
    return sdf


def at(grid: np.ndarray, p: complex) -> float:
    return grid[int(p.imag), int(p.real)]


def encode_frame(im: np.ndarray) -> bytes:
    return (im * 255).astype(np.uint8).tobytes()


def from_gray(im: np.ndarray) -> np.ndarray:
    return np.dstack([im, im, im])


def autoscale(x: np.ndarray) -> np.ndarray:
    lo = np.min(x)
    hi = np.max(x)
    return (x - lo) / (hi - lo)


class Dot:
    def __init__(self, position: complex, velocity: complex):
        self.position = position
        self.velocity = velocity

    @staticmethod
    def sample(path: Path, t: float):
        v = path.tangent(t) * 1j
        return Dot(path.point(t), 50 * v / abs(v))


def inside(resolution: Tuple[int, int], p: complex):
    width, height = resolution
    return 0 < p.real < width and 0 < p.imag < height


def cuniform(resolution: Tuple[int, int]) -> complex:
    width, height = resolution    
    return complex(width * np.random.random(), height * np.random.random())


def random_dot(resolution: Tuple[int, int], v: float) -> Dot:
    return Dot(
        cuniform(resolution),
        v * e ** (tau * 1j * np.random.random()),
    )


def main():
    path = transform(HEART, 0.5, 100 + 100j)

    N = 1000
    resolution = (400, 400)

    #dots = [Dot.sample(path, t) for t in np.random.random(N)]
    dots = [random_dot(resolution, 5) for _ in range(N)]
    
    sdf = create_sdf(path, (400, 400), resolution, n=100)
    dy, dx = np.gradient(sdf)
    dt = 0.025
    for t in np.arange(0, 60, dt):
        # step
        for dot in dots:
            dv = at(dx, dot.position) + 1j * at(dy, dot.position)
            dot.velocity += 20 * -dv * dt
            dot.position += dot.velocity * dt
            if not inside(resolution, dot.position):
                new_dot = random_dot(resolution, 5)
                dot.position = new_dot.position
                dot.velocity = new_dot.velocity
        
        # draw
        frame = np.zeros(resolution)
        for dot in dots:
            frame[int(dot.position.imag), int(dot.position.real)] = 1
        sys.stdout.buffer.write(encode_frame(from_gray(frame)))
    
    #frame = autoscale(sdf)
    


if __name__ == "__main__":
    main()
