from typing import Tuple


Resolution = Tuple[int, int]


def parse_resolution(resolution: str) -> Resolution:
    width, height = (int(d) for d in resolution.split('x'))
    return width, height
