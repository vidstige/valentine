from typing import Tuple

import numpy as np
from svg.path import parse_path, Path


HEART = parse_path("M348.151,54.514c-19.883-19.884-46.315-30.826-74.435-30.826c-28.124,0-54.559,10.942-74.449,30.826l-9.798,9.8l-9.798-9.8 c-19.884-19.884-46.325-30.826-74.443-30.826c-28.117,0-54.56,10.942-74.442,30.826c-41.049,41.053-41.049,107.848,0,148.885 l147.09,147.091c2.405,2.414,5.399,3.892,8.527,4.461c1.049,0.207,2.104,0.303,3.161,0.303c4.161,0,8.329-1.587,11.498-4.764 l147.09-147.091C389.203,162.362,389.203,95.567,348.151,54.514z M325.155,180.404L189.47,316.091L53.782,180.404 c-28.368-28.364-28.368-74.514,0-102.893c13.741-13.739,32.017-21.296,51.446-21.296c19.431,0,37.702,7.557,51.438,21.296 l21.305,21.312c6.107,6.098,16.897,6.098,23.003,0l21.297-21.312c13.737-13.739,32.009-21.296,51.446-21.296 c19.431,0,37.701,7.557,51.438,21.296C353.526,105.89,353.526,152.039,325.155,180.404z")


def distance(p0: complex, n: complex, p: complex) -> float:
    c = -n.real * p0.real - n.imag * p0.imag
    return abs(n.real * p.real + n.imag + p.imag + c) / abs(n)


def compute_sdf(shape: Path, size: Tuple[float, float], resolution: Tuple[int, int]) -> np.ndarray:
    x, y = np.meshgrid(
        np.linspace(0, size[0], resolution[0]),
        np.linspace(0, size[1], resolution[1]))
    
    N = 100
    ps = []
    for i in range(N):
        t = i / N
        p = shape.point(t)
        n = shape.tangent(t) * -1j
        if abs(n) > 0:
            d = distance(p, n, x + 1j * y)
            print(d)
        ps.append(p)


def main():
    sdf = compute_sdf(HEART, (400, 400), (10, 10))

if __name__ == "__main__":
    main()
