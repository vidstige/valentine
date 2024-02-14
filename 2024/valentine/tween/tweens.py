def linear(t: float) -> float:
    return t

def ease_in_quad(t: float) -> float:
    return t ** 2

def ease_out_quad(t: float) -> float:
    return -t * (t - 2)
