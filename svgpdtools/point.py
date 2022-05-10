from __future__ import annotations
from dataclasses import dataclass
import math

from .utils import number_repr
from .transform import Transform


@dataclass
class Point:
    x: float = 0
    y: float = 0
    
    def __repr__(self) -> str:
        return number_repr(self.x) + ',' + number_repr(self.y)

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __iadd__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return Point(self.x - other.x, self.y - other.y)

    def distance_to(self, other: Point) -> float:
        dx, dy = other.x - self.x, other.y - self.y
        return math.sqrt(dx*dx + dy*dy)
        
    def transform(self, t: Transform) -> None:
        self.x, self.y = t.apply_point(self)

    def transformed(self, t: Transform) -> Point:
        return Point(*t.apply_point(self))
    
    def clone(self) -> Point:
        return Point(self.x, self.y)
