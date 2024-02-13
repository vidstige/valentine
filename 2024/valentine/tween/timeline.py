from abc import ABC, abstractmethod
from typing import Dict, List, Sequence, Tuple


class Tween(ABC):
    duration: float

    @abstractmethod
    def __call__(self, t: float) -> float:
        pass


class Linear(Tween):
    def __init__(self, start: float, stop: float, duration: float = 1) -> None:
        self.start = start
        self.stop = stop
        self.duration = duration

    def __call__(self, t: float) -> float:
        nt = t / self.duration
        return (1 - nt) * self.start + nt * self.stop


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
