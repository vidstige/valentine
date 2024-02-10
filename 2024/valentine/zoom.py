from typing import Tuple

import numpy as np

from valentine.resolution import Resolution


# xmin, ymin, xmax, ymax
Bounds = Tuple[float, float, float, float]


class Zoom:
    def __init__(self, scale: float, offset: np.ndarray):
        self.scale = scale
        self.offset = offset
    
    def transform(self, points: np.ndarray) -> np.ndarray:
        return points * self.scale + self.offset


def zoom_to(bounds: Bounds, resolution: Resolution, padding: float = 0.0) -> Zoom:
    xmin, ymin, xmax, ymax = bounds
    width, height = resolution
    sx, sy = (width - padding * 2) / (xmax - xmin), (height - padding * 2) / (ymax - ymin)
    scale = min(sx, sy)
    offset = np.array([
        -xmin * scale + 0.5 * (width - (xmax - xmin) * scale),
        -ymin * scale + 0.5 * (height - (ymax - ymin) * scale),
    ])
    return Zoom(scale, offset)
