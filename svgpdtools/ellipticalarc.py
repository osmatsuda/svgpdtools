from dataclasses import dataclass, field
from typing import Optional
import math, os

from .transform import Transform
from .utils import rad2deg, deg2rad, number_repr
from .graphics import Point, Circle, Line, line_through

@dataclass
class EllipticalArcItem:
    radii: tuple[float, float]
    x_axis_rotation: float
    is_large_arc: bool
    is_sweep: bool
    to_point: Point = field(default_factory=Point)
    _from_point: Optional[Point] = field(default=None)
    _elliptical_arc_center: Optional[Point] = field(default=None)
    _elliptical_arc_start: Optional[Point] = field(default=None)

    def _init_with_start_point(self, sp: Point, is_abs: bool) -> None:
        self._from_point = sp.clone()
        if not is_abs:
            self.to_point += sp

        phi = deg2rad(self.x_axis_rotation)
        self._elliptical_arc_center = _elliptical_arc_center(
            phi = phi,
            rx = self.rx,
            ry = self.ry,
            is_large_arc = self.is_large_arc,
            is_sweep = self.is_sweep,
            from_p = sp,
            to_p = self.to_point,
        )
        self._elliptical_arc_start = Point(
            x = self._elliptical_arc_center.x + math.cos(phi) * self.rx,
            y = self._elliptical_arc_center.y + math.sin(phi) * self.rx,
        )

    @property
    def rx(self) -> float:
        return self.radii[0]
    @property
    def ry(self) -> float:
        return self.radii[1]

    def repr(self, is_abs: bool) -> str:
        if self._from_point is None:
            raise Exception('Should be initialized with start_point.')

        flags = '1' if self.is_large_arc else '0'
        flags += ' 1' if self.is_sweep else ' 0'
        to_p = self.to_point if is_abs else (self.to_point - self._from_point)

        rpr = f'{number_repr(self.rx)} {number_repr(self.ry)}'
        rpr += f' {number_repr(self.x_axis_rotation)} {flags} {to_p}'
        return rpr

    def transform(self, t: Transform) -> None:
        if self._from_point is None or self._elliptical_arc_center is None or self._elliptical_arc_start is None:
            raise Exception('Should be initialized with start_point.')

        self.to_point.transform(t)
        self._from_point.transform(t)
        self._elliptical_arc_center.transform(t)
        self._elliptical_arc_start.transform(t)

        rx2 = self._elliptical_arc_center.distance_to(self._elliptical_arc_start)
        if not math.isclose(self.rx, rx2):
            ry2 = self.ry * rx2 / self.rx
            self.radii = (rx2, ry2)

        self.x_axis_rotation = rad2deg(_x_axis_rotation(
            cp = self._elliptical_arc_center,
            sp = self._elliptical_arc_start,
            rx = rx2,
        ))

        if t.a * t.d < 0:
            self.is_sweep = not self.is_sweep

    def converted_to_curve_points(self) -> list[Point]:
        cp = self._elliptical_arc_center
        from_p = self._from_point
        assert cp is not None and from_p is not None
        
        guide_circle = Circle(c=cp, r=self.rx)
        to_O = Transform.translate(-cp.x, -cp.y)
        rotate_to_normal = Transform.rotate(-self.x_axis_rotation)
        scale_to_circle = Transform.scale(1, self.rx / self.ry)
        to_beginning = Transform.translate(cp.x, cp.y)
        t = to_beginning * scale_to_circle * rotate_to_normal * to_O
        from_p_td = from_p.transformed(t)
        to_p_td = self.to_point.transformed(t)
        curve_points = _split_arc(guide_circle, self.is_sweep, from_p_td, to_p_td)

        t = to_beginning * rotate_to_normal.inversed() * scale_to_circle.inversed() * to_O
        return [p.transformed(t) for p in curve_points]
    

        
def _x_axis_rotation(cp: Point, sp: Point, rx: float) -> float:
    dx, dy = sp.x - cp.x, sp.y - cp.y

    if math.isclose(dy, 0, abs_tol=1e-7):
        if dx > 0:
            return 0.
        return math.pi
    if math.isclose(dx, 0, abs_tol=1e-7):
        if dy > 0:
            return math.pi * .5
        return math.pi * 1.5

    phi = math.atan(dy/dx)
    if math.isclose(math.acos(dx/rx), math.asin(dy/rx)):
        return phi

    if dx*dy < 0:
        if dx < 0:
            return math.pi + phi
        return math.pi * 2 - abs(phi)
    return math.pi + phi


def _elliptical_arc_center(phi: float,
                           rx: float, ry: float,
                           is_large_arc: bool, is_sweep: bool,
                           from_p: Point, to_p: Point) -> Point:
    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)
    x1_x2_d2 = (from_p.x - to_p.x) / 2
    y1_y2_d2 = (from_p.y - to_p.y) / 2
    x1dsh = cos_phi * x1_x2_d2 + sin_phi * y1_y2_d2
    y1dsh = -sin_phi * x1_x2_d2 + cos_phi * y1_y2_d2

    sign = 1 if is_large_arc ^ is_sweep else -1
    sqr_rx, sqr_ry = rx * rx, ry * ry
    sqr_x1dsh, sqr_y1dsh = x1dsh * x1dsh, y1dsh * y1dsh
    numr = sqr_rx * sqr_ry - sqr_rx * sqr_y1dsh - sqr_ry * sqr_x1dsh
    denm = sqr_rx * sqr_y1dsh + sqr_ry * sqr_x1dsh
    c = sign * math.sqrt(numr / denm)
    cxdsh = c * rx * y1dsh / ry
    cydsh = -c * ry * x1dsh / rx
    return Point(
        x = cos_phi * cxdsh - sin_phi * cydsh + (from_p.x + to_p.x) / 2,
        y = sin_phi * cxdsh + cos_phi * cydsh + (from_p.y + to_p.y) / 2,
    )


@dataclass
class Arc:
    theta: float
    from_point: Point = field(default_factory=Point)
    to_point: Point = field(default_factory=Point)


def _split_arc(circle: Circle, is_sweep: bool, from_p: Point, to_p: Point) -> list[Point]:
    arcs = _split_arc_60_or_45(circle, is_sweep, from_p, to_p)
    ps = []
    for arc in arcs:
        tan1 = circle.tangent_through(arc.from_point)
        tan2 = circle.tangent_through(arc.to_point)
        quadratic_cp = tan1.intersection(tan2)
        assert quadratic_cp is not None
        u = _cp_param(arc.theta)
        cp1 = arc.from_point.between_to(quadratic_cp, u)
        cp2 = arc.to_point.between_to(quadratic_cp, u)
        ps += [cp1, cp2, arc.to_point]
    return ps


def _cp_param(rad: float) -> float:
    deg = rad2deg(rad)
    return 0.6555555555555556 - deg*deg/90000


def _split_arc_60_or_45(circle: Circle, is_sweep: bool, from_p: Point, to_p: Point) -> list[Arc]:
    two_pi = math.pi * 2
    _60 = 60 * math.pi / 180
    _45 = 45 * math.pi / 180
    _30 = 30 * math.pi / 180
    _15 = 15 * math.pi / 180

    start = circle.angle_from_x_axis(from_p)
    end = circle.angle_from_x_axis(to_p)
    theta = (end - start) % two_pi
    if not is_sweep:
        theta = two_pi - theta

    segments_count = int(theta / _60)
    mod = max(0.0, theta - (_60 * segments_count))
    if mod < _30:
        if segments_count == 0:
            segs = [theta]
        else:
            segs = [_60] * (segments_count-1) + [_45, _15 + mod]
    else:
        segs = [_60] * segments_count + [mod]

    acc = start
    items = []
    for span in segs:
        _acc = acc + span if is_sweep else acc - span
        items.append(Arc(
            theta = span,
            from_point = circle.point_from_x_axis(acc),
            to_point = circle.point_from_x_axis(_acc),
        ))
        acc = _acc
        
    return items
