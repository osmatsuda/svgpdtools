from __future__ import annotations
from dataclasses import dataclass, field

from svgpdtools.utils import number_repr
from svgpdtools.transform import Transform


_precision_ = 6


@dataclass
class Point:
    x: float = 0
    y: float = 0
    
    def __repr__(self) -> str:
        return f'{number_repr(self.x, precision=_precision_)},{number_repr(self.y, precision=_precision_)}'

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __iadd__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return Point(self.x - other.x, self.y - other.y)

    def transform(self, t: Transform) -> None:
        self.x, self.y = t.apply_point(self)

    def clone(self) -> Point:
        return Point(self.x, self.y)
