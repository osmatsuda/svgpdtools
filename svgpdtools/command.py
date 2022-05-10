from __future__ import annotations
from typing import Protocol, TypeVar, Generic, Optional
from collections import UserList
from dataclasses import dataclass, field, asdict
import math

from .point import Point
from .transform import Transform
from .utils import number_repr, rad2deg, deg2rad



CommandDataType = TypeVar('CommandDataType')

class Command(Protocol[CommandDataType]):
    """
    self.start_point and self.end_point should be absolute coordinates.
    """
    fn: str
    start_point: Point
    data: list[CommandDataType]

    def transform(self, t: Transform) -> None: ...
    def absolutize(
            self,
            prev_point: Point,
            *,
            called_internally: bool,
    ) -> Point: ...
    @property
    def end_point(self) -> Point: ...



class CommandBase(Generic[CommandDataType]):
    def __init__(self, fn: str, data: list[CommandDataType]):
        self.fn = fn
        self.data = data
        self._repr_relative = fn.islower()
        self._start_point: Optional[Point] = None

    @property
    def start_point(self) -> Point:
        if self._start_point is not None:
            return self._start_point
        raise Exception(f'uninitialized start point: {self.fn}, {self.data}')

    @start_point.setter
    def start_point(self, value: Point) -> None:
        self._start_point = value.clone()

        

class SegmentalLineAndCurve(CommandBase[Point]):
    def __repr__(self) -> str:
        force_relative = self._repr_relative and self.fn.isupper()
        rpr = self.fn.lower() if force_relative else self.fn
        for p in (self._relatived_data() if force_relative else self.data):
            rpr += f' {p}'

        return rpr

    def _relatived_data(self) -> list[Point]:
        if self.fn.islower():
            return self.data

        cur = self.start_point.clone()
        step = 1
        if self.fn == 'C':
            step = 3
        elif self.fn in 'SQ':
            step = 2

        data = []
        for i in range(0, len(self.data), step):
            for j in range(step):
                data.append(self.data[i+j] - cur)
            cur = self.data[i+j].clone()
            
        return data

    @property
    def end_point(self) -> Point:
        if self.fn.isupper(): return self.data[-1]

        cur = self.start_point.clone()
        step = 1
        if self.fn == 'c':
            step = 3
        elif self.fn in 'sq':
            step = 2

        for i in range(step-1, len(self.data), step):
            cur += self.data[i]

        return cur

    def transform(self, t: Transform) -> None:
        self.start_point.transform(t)

        for p in self.data:
            p.transform(t)

    def absolutize(self, prev_point: Point, *, called_internally=False) -> Point:
        self._repr_relative = called_internally and self._repr_relative
        if self.fn.isupper(): return self.end_point

        cur = prev_point.clone()
        step = 1
        if self.fn.lower() == 'c':
            step = 3
        elif self.fn.lower() in 'sq':
            step = 2

        for i in range(0, len(self.data), step):
            for j in range(step):
                self.data[i+j] += cur
            cur = self.data[i+j]

        self.fn = self.fn.upper()
        return self.end_point
            

    
class Curveto(SegmentalLineAndCurve):
    """
    C/c: curveto                  (cp1, cp2, p)+
    S/s: smooth_curveto           (cp2, p)+
    Q/q: quadratic_curveto        (cp, p)+
    T/q: smooth_quadratic_curveto (p)+
    """
    pass
    


class Moveto(CommandBase[Point]):
    """
    M/m: moveto (p)+
    """
    def __init__(self, fn: str, data: list[Point], is_first_command: bool=False):
        self.is_first_command = is_first_command
        super().__init__(fn, data)
        
    def __repr__(self) -> str:
        force_relative = self._repr_relative and self.fn.isupper()
        rpr = self.fn.lower() if force_relative else self.fn

        start = 0
        curr_p = self.start_point
        if self.is_first_command:
            rpr += f' {curr_p}'
            start = 1

        for i in range(start, len(self.data)):
            if force_relative:
                rpr += f' {self.data[i] - curr_p}'
            else:
                rpr += f' {self.data[i]}'
            curr_p = self.data[i]

        return rpr
    
    @property
    def start_point(self) -> Point:
        if self.is_first_command:
            return self.data[0]
            
        if self._start_point is not None:
            return self._start_point

        raise Exception(f'uninitialized start point')

    @start_point.setter
    def start_point(self, val: Point) -> None:
        if not self.is_first_command:
            self._start_point = val.clone()
        
    @property
    def end_point(self) -> Point:
        if self.fn.isupper(): return self.data[-1]

        cur = self.start_point.clone()
        start = 1 if self.is_first_command else 0
        for i in range(start, len(self.data)):
            cur += self.data[i]

        return cur
    
    @property
    def moveto_point(self) -> Point:
        """
        A target point of a moveto command. Return an absolute point.
        """
        if self.fn.islower() and not self.is_first_command:
            return Point(
                x = self.start_point.x + self.data[0].x,
                y = self.start_point.y + self.data[0].y,
            )
        return self.data[0]

    def transform(self, t: Transform) -> None:
        if not self.is_first_command:
            self.start_point.transform(t)

        for p in self.data:
            p.transform(t)
            
    def absolutize(self, prev_point: Point, *, called_internally=False) -> Point:
        self._repr_relative = called_internally and self._repr_relative
        if self.fn.isupper():
            return self.end_point

        cur = prev_point.clone()
        start = 1 if self.is_first_command else 0
        for i in range(start, len(self.data)):
            self.data[i] += cur
            cur = self.data[i]

        self.fn = self.fn.upper()
        return self.end_point


    
    
class Lineto(SegmentalLineAndCurve):
    """
    L/l: lineto (p)+
    """
    pass



class HorizontalAndVerticalLineto(CommandBase[float]):
    """
    H/h: horizontal_lineto (num)+
    V/v: vertical_lineto   (num)+
    """
    def __repr__(self) -> str:
        if self._repr_relative and self.fn.isupper():
            rpr = self.fn.lower()
            data = self._relatived_data()
        else:
            rpr = self.fn
            data = self.data

        for n in data:
            rpr += ' ' + number_repr(n)

        return rpr

    def _relatived_data(self) -> list[float]:
        if self.fn.islower(): return self.data

        cur = self.start_point.clone()
        data = []
        for n in self.data:
            if self.fn == 'H':
                dst = cur.x
                cur = Point(
                    x = n,
                    y = cur.y,
                )
            else: # V
                dst = cur.y
                cur = Point(
                    x = cur.x,
                    y = n,
                )
            data.append(n - dst)

        return data

    @property
    def end_point(self) -> Point:
        cur = self.start_point
        is_h = self.fn.lower() == 'h'
        if self.fn.isupper():
            return Point(
                x = self.data[-1] if is_h else cur.x,
                y = cur.y if is_h else self.data[-1],
            )
        
        total = sum(self.data)
        return  Point(
            x = cur.x + (total if is_h else .0),
            y = cur.y + (.0 if is_h else total),
        )

    def transform(self, t: Transform) -> None:
        assert False, 'Never be reached'

    def absolutize(self, prev_point: Point, *, called_internally=False) -> Point:
        self._repr_relative = called_internally and self._repr_relative
        if self.fn.isupper(): return self.end_point

        if self.fn == 'h':
            self.data = [x + prev_point.x for x in self.data]
        else:
            self.data = [y + prev_point.y for y in self.data]

        self.fn = self.fn.upper()
        return self.end_point

    def converted_into_lineto(self) -> Lineto:
        from_p = self.start_point
        is_abs = self.fn.isupper()
        
        if self.fn.lower() == 'h':
            to_p = Point(
                x = self.data[-1],
                y = from_p.y if is_abs else .0,
            )
        else:
            to_p = Point(
                x = from_p.x if is_abs else .0,
                y = self.data[-1],
            )

        cmd = Lineto(
            fn = 'L' if is_abs else 'l',
            data = [to_p],
        )

        cmd.start_point = from_p.clone()
        cmd._repr_relative = self._repr_relative
        return cmd



@dataclass
class EllipticalArcItem:
    radii: tuple[float, float]
    x_axis_rotation: float
    is_large_arc: bool
    is_sweep: bool
    to_point: Point = field(default_factory=Point)
    _arc_start: Optional[Point] = field(default=None)
    _elliptical_arc_center: Optional[Point] = field(default=None)
    _elliptical_arc_start: Optional[Point] = field(default=None)

    def _init_with_start_point(self, sp: Point, is_abs: bool) -> None:
        self._arc_start = sp.clone()
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
        if self._arc_start is None:
            raise Exception('Should be initialized with start_point.')

        flags = '1' if self.is_large_arc else '0'
        flags += '1' if self.is_sweep else '0'
        to_p = self.to_point if is_abs else (self.to_point - self._arc_start)

        rpr = f'{number_repr(self.rx)} {number_repr(self.ry)}'
        rpr += f' {number_repr(self.x_axis_rotation)} {flags} {to_p}'
        return rpr

    def transform(self, t: Transform) -> None:
        if self._arc_start is None or self._elliptical_arc_center is None or self._elliptical_arc_start is None:
            raise Exception('Should be initialized with start_point.')

        self.to_point.transform(t)
        self._arc_start.transform(t)
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

class EllipticalArc(CommandBase[EllipticalArcItem]):
    def __repr__(self) -> str:
        force_relative = self._repr_relative and self.fn.isupper()
        rpr = 'a' if force_relative else self.fn
        for a in self.data:
            rpr += f' {a.repr(self.fn.isupper() and not force_relative)}'

        return rpr
        
    @property
    def start_point(self) -> Point:
        if self._start_point is not None:
            return self._start_point
        raise Exception(f'uninitialized start point: {self.fn}, {self.data}')

    @start_point.setter
    def start_point(self, value: Point) -> None:
        self._start_point = value.clone()
        sp = value
        for a in self.data:
            a._init_with_start_point(sp, self.fn.isupper())
            sp = a.to_point

    @property
    def end_point(self) -> Point:
        return self.data[-1].to_point

    def transform(self, t: Transform) -> None:
        self.start_point.transformed(t)
        for a in self.data:
            a.transform(t)

    def absolutize(self, prev_point: Point, *, called_internally=False) -> Point:
        self._repr_relative = called_internally and self._repr_relative
        self.fn = self.fn.upper()
        return self.end_point

        


class Close(CommandBase[Point]):
    def __init__(self, fn: str):
        self.fn = fn
        super().__init__(fn, [])

    def __repr__(self) -> str:
        if self._repr_relative and self.fn.isupper():
            return self.fn.lower()
        return self.fn

    @property
    def end_point(self) -> Point:
        if self.data:
            return self.data[0]
        raise Exception('uninitialized start_point and end_point')

    @end_point.setter
    def end_point(self, val: Point) -> None:
        self.data.insert(0, val)
        if len(self.data) > 1:
            self.data.pop()

    def transform(self, t: Transform) -> None:
        self.start_point.transformed(t)
        self.data[0].transform(t)

    def absolutize(self, _: Point, *, called_internally=False) -> Point:
        self._repr_relative = called_internally and self._repr_relative
        self.fn = 'Z'
        return self.end_point
    
