from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Sequence, Tuple

from . import tweens


def lerp(a: float, b: float, t: float) -> float:
    return (1 - t) * a + t * b


class Tween(ABC):
    f: Callable[[float], float]
    def __init__(self, start: float, stop: float, duration: float = 1) -> None:
        self.start = start
        self.stop = stop
        self.duration = duration

    def __call__(self, t: float) -> float:
        normalized_t = t / self.duration
        return lerp(self.start, self.stop, self.__class__.f(normalized_t))


class Linear(Tween):
    f = tweens.linear


class EaseInQuad(Tween):
    f = tweens.ease_in_quad


class EaseOutQuad(Tween):
    f = tweens.ease_out_quad


class Constant(Tween):
    def __init__(self, value: float, duration = 1) -> None:
        self.value = value
        self.duration = duration

    def __call__(self, t: float) -> float:
        del t
        return self.value


class TweenSequence(Tween):
    def __init__(self, tweens: Sequence[Tween]) -> None:
        self.tweens = tweens
    
    def _find_tween(self, t: float) -> Tuple[Tween, float]:
        start = 0
        for tween in self.tweens:
            if t >= start and t < tween.duration + start:
                #return tween, start
                break
            start += tween.duration
        return tween, start

    def __call__(self, t: float) -> float:
        # find correct tween
        tween, start = self._find_tween(t)
        return tween(t - start)
    
    def duration(self) -> float:
        return sum(tween.duration for tween in self.tweens)


class Timeline:
    def __init__(self):
        self.tags: Dict[str, List[Tuple[Tween, float]]] = {}

    def add(self, tag: str, tween: Tween) -> None:
        self.tags[tag] = tween

    def tag(self, tag: str) -> Tween:
        return self.tags[tag]

    def duration(self) -> float:
        return max(tween.duration() for tween in self.tags.values())
