from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import math, random

from svgpdtools.utils import number_repr
from svgpdtools.transform import Transform


@dataclass
class Point:
    x: float = 0.
    y: float = 0.

    def __repr__(self) -> str:
        return number_repr(self.x) + ',' + number_repr(self.y)

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, t: float) -> Point:
        return Point(self.x * t, self.y * t)
    
    def distance_to(self, other: Point) -> float:
        delta = other - self
        return math.sqrt(delta.x**2 + delta.y**2)

    def point_between(self, other: Point, t: float) -> Point:
        delta = other - self
        return self + delta * t
        
    def transform(self, t: Transform) -> None:
        self.x, self.y = t.apply_point(self)

    def transformed(self, t: Transform) -> Point:
        return Point(*t.apply_point(self))
    
    def svg_repr(self, r: float, *, color: str='', dot: str='O') -> str:
        if dot == 'A':
            dx = .8660254037844386 * r
            dy = .5 * r
            s = f'<path d="M {Point(self.x, self.y-r)} {Point(self.x+dx, self.y+dy)} {Point(self.x-dx, self.y+dy)} Z"'
        else:
            s = f'<circle cx="{number_repr(self.x)}" cy="{number_repr(self.y)}" r="{number_repr(r)}"'

        if color:
            return s + f' fill="{color}"/>'
        return s + '/>'


@dataclass
class Circle:
    c: Point = field(default_factory=Point)
    r: float = 0.

    def svg_repr(self, *, fill: str='none', stroke: str='', stroke_width: str='', transform: str='') -> str:
        s = f'<circle fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}"'
            if stroke_width:
                s += f' stroke-width="{stroke_width}"'

        if transform:
            s += f' transform="{transform}"'

        s += f' cx="{number_repr(self.c.x)}" cy="{number_repr(self.c.y)}" r="{number_repr(self.r)}"/>'
        return s
    

@dataclass
class Line:
    """a*x + b*y = c"""
    a: float
    b: float
    c: float

    def perpendicular_through(self, p: Point) -> Line:
        a = self.b
        b = -self.a
        c = a * p.x + b * p.y
        return Line(a, b, c)

    def intersection(self, other: Line) -> Optional[Point]:
        det = self.a * other.b - other.a * self.b
        if math.isclose(det, 0, abs_tol=1e-7):
            return None

        return Point(
            x = (other.b * self.c - self.b * other.c) / det,
            y = (self.a * other.c - other.a * self.c) / det,
        )

    @staticmethod
    def through_points(*ps: Point) -> Line:
        assert len(ps) > 1
        a =   ps[0].y - ps[1].y
        b = -(ps[0].x - ps[1].x)
        c = a * ps[0].x + b * ps[0].y
        return Line(a, b, c)



def random_3points(span: float, min_distance: float) -> list[Point]:
    t = .1
    x0, x1 = span*t, span*(1 - t*2)
    y0, y1 = span*t, span*(1 - t*2)
    def randp():
        return Point(
            x = x0 + x1 * random.random(),
            y = y0 + y1 * random.random(),
        )
    
    ps = [randp()]
    while len(ps) < 3:
        _p = randp()
        if any([_p.distance_to(p) < min_distance for p in ps]):
            continue
        
        if len(ps) == 2:
            l1 = Line.through_points(*ps)
            l2 = l1.perpendicular_through(_p)
            x = l1.intersection(l2)
            if x is not None and math.isclose(_p.distance_to(x), 0, abs_tol=min_distance):
                continue

        ps.append(_p)

    return ps


def circle_from_3points(A: Point, B: Point, C: Point) -> Circle:
    ab = Line.through_points(A, B)
    bc = Line.through_points(B, C)
    ab_to_O = ab.perpendicular_through(A.point_between(B, .5))
    bc_to_O = bc.perpendicular_through(B.point_between(C, .5))
    O = ab_to_O.intersection(bc_to_O)
    assert O is not None
    return Circle(
        c = O,
        r = O.distance_to(A)
    )


@dataclass
class EllipticalArc:
    radii: tuple[float, float]
    x_axis_rotation: float
    flags: tuple[bool, bool]
    from_point: Point = field(default_factory=Point)
    to_point: Point = field(default_factory=Point)

    def svg_repr(self, *, fill: str='none', stroke: str='', stroke_width: str='') -> str:
        s = f'<path fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}"'
            if stroke_width:
                s += f' stroke-width="{stroke_width}"'

        s += f' d="M {self.from_point} A {number_repr(self.radii[0])} {number_repr(self.radii[1])} {number_repr(self.x_axis_rotation)} '
        s += '1' if self.flags[0] else '0'
        s += '1' if self.flags[1] else '0'
        s += f' {self.to_point}"/>'
        return s
        
