from textwrap import wrap
from typing import Sequence, Tuple

import cairo

from valentine.resolution import Resolution


def parse_color(color: str) -> Tuple[float, float, float]:
    return tuple(int(channel, 16) / 255 for channel in wrap(color.removeprefix('#'), 2))


def gradient(resolution: Resolution, stops: Sequence[str]) -> cairo.Pattern:
    width, height = resolution
    gradient = cairo.LinearGradient(width/2, 0, width/2, height)
    n = len(stops)
    for i, color in enumerate(stops):
        offset = i / (n - 1)
        gradient.add_color_stop_rgb(offset, *parse_color(color))
    return gradient