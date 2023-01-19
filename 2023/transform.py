from svg.path import Path, Linear, QuadraticBezier, CubicBezier

def transform(path: Path, multiply: complex, add: complex) -> Path:
    for segment in path:
        if isinstance(segment, Linear):
            segment.start = segment.start * multiply + add
            segment.end = segment.end * multiply + add
        if isinstance(segment, QuadraticBezier):
            segment.start = segment.start * multiply + add
            segment.control = segment.control * multiply + add
            segment.end = segment.end * multiply + add
        if isinstance(segment, CubicBezier):
            segment.start = segment.start * multiply + add
            segment.control1 = segment.control1 * multiply + add
            segment.control2 = segment.control2 * multiply + add
            segment.end = segment.end * multiply + add
    return path