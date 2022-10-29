from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Iterable, Iterator
from typing import Optional, NewType
import math

from .utils import number_repr
from .transform import Transform


TupledPoint = tuple[float, ...]

@dataclass
class Point(Iterable[float]):
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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Point):
            return math.isclose(self.x, other.x) and math.isclose(self.y, other.y)
        return False

    def __iter__(self) -> Iterator[float]:
        return iter([self.x, self.y])
    
    def distance_to(self, other: Point) -> float:
        dx, dy = other.x - self.x, other.y - self.y
        return math.sqrt(dx*dx + dy*dy)

    def between_to(self, to_p: Point, u: float) -> Point:
        return Point(
            x = self.x + (to_p.x - self.x) * u,
            y = self.y + (to_p.y - self.y) * u,
        )
        
    def transform(self, t: Transform) -> None:
        self.x, self.y = t.apply_point(self)

    def transformed(self, t: Transform) -> Point:
        return Point(*t.apply_point(self))
    
    def clone(self) -> Point:
        return Point(self.x, self.y)



@dataclass
class Line:
    # ax + by = c
    a: float
    b: float
    c: float

    def perpendicular_through(self, p: Point) -> Line:
        a = self.b
        b = -self.a
        c = a*p.x + b*p.y
        return Line(a, b, c)

    def intersection(self, other: Line) -> Optional[Point]:
        det = self.a * other.b - other.a * self.b
        if math.isclose(det, 0, abs_tol=1e-7):
            return None
        return Point(
            x = (other.b * self.c - self.b * other.c) / det,
            y = (self.a * other.c - other.a * self.c) / det,
        )


def line_through(*points: Point) -> Line:
    assert len(points) > 1

    p1, p2 = points[0], points[-1]
    a = p1.y - p2.y
    b = p2.x - p1.x
    c = a * p1.x + b * p1.y
    return Line(a, b, c)




@dataclass
class Circle:
    c: Point = field(default_factory=Point)
    r: float = 0.

    def angle_from_x_axis(self, p: Point) -> float:
        assert math.isclose(self.c.distance_to(p), self.r), f'{self.c.distance_to(p)}, {self.r}'
        x = p.x - self.c.x
        y = p.y - self.c.y
        r = self.r

        if math.isclose(y, 0, abs_tol=1e-7):
            if x > 0:
                return 0.
            return math.pi

        if math.isclose(x, 0, abs_tol=1e-7):
            if y > 0:
                return math.pi * .5
            return math.pi * 1.5

        theta = math.atan(y / x)
        if math.isclose(math.acos(x / r), math.asin(y / r)):
            return theta

        if x < 0 and y > 0:
            return math.pi + theta
        if x > 0 and y < 0:
            return 2 * math.pi - abs(theta)
        return math.pi + theta

    def point_from_x_axis(self, theta: float) -> Point:
        return Point(
            x = self.c.x + self.r * math.cos(theta),
            y = self.c.y + self.r * math.sin(theta),
        )

    def tangent_through(self, p: Point) -> Line:
        po = line_through(self.c, p)
        return po.perpendicular_through(p)
