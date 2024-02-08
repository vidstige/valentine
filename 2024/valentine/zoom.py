from typing import Sequence

from valentine.linesegment import Point
from valentine.resolution import Resolution


class Zoom:
    def __init__(self, scale: float, offset: Point):
        self.scale = scale
        self.offset = offset
    
    def transform(self, point: Point) -> Point:
        x, y = point
        ox, oy = self.offset
        return x * self.scale + ox, y * self.scale + oy


def zoom_to(points: Sequence[Point], resolution: Resolution, padding: float = 0.0) -> Zoom:
    xmin, xmax = min(x for x, _ in points), max(x for x, _ in points)
    ymin, ymax = min(y for _, y in points), max(y for _, y in points)
    width, height = resolution
    sx, sy = width / (xmax - xmin), height / (ymax - ymin)
    scale = min(sx, sy)
    offset = (
        -xmin * scale + 0.5 * (width - (xmax - xmin) * scale),
        -ymin * scale + 0.5 * (height - (ymax - ymin) * scale),
    )
    return Zoom(scale, offset)
