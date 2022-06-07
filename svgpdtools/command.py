from __future__ import annotations
from typing import Protocol, TypeVar, Generic, Optional
from collections import UserList
from dataclasses import dataclass, field, asdict
import math

from .graphics import Point
from .transform import Transform
from .ellipticalarc import EllipticalArcItem
from .utils import number_repr, rad2deg, deg2rad



CommandDataType = TypeVar('CommandDataType')

class Command(Protocol[CommandDataType]):
    """
    self.start_point and self.end_point should be absolute coordinates.
    """
    fn: str
    start_point: Point
    data: list[CommandDataType]
    repr_relative: bool

    def transform(self, t: Transform) -> None: ...
    def transformed(self, t: Transform) -> Command: ...
    def absolutize(
            self,
            prev_point: Point,
            *,
            called_internally: bool,
    ) -> Point: ...
    @property
    def end_point(self) -> Point: ...



class CommandBase(Generic[CommandDataType]):
    def __init__(self, fn: str, data: list[CommandDataType]) -> None:
        self.fn = fn
        self.data = data
        self.repr_relative = fn.islower()
        self._start_point: Optional[Point] = None

    @property
    def start_point(self) -> Point:
        if self._start_point is not None:
            return self._start_point
        raise Exception(f'uninitialized start point: {self.fn}, {self.data}')

    @start_point.setter
    def start_point(self, value: Point) -> None:
        self._start_point = value.clone()

    @property
    def end_point(self) -> Point:
        raise NotImplementedError

    def absolutize(self, prev_point: Point, *, called_internally: bool=False) -> Point:
        raise NotImplementedError
    
    def transform(self, t: Transform) -> None:
        raise NotImplementedError
    
    def transformed(self, t: Transform) -> Command:
        me = self.__class__(self.fn, self.data)
        me.start_point = self.start_point
        me.repr_relative = self.repr_relative
        me.transform(t)
        return me

        

class SegmentalLineAndCurve(CommandBase[Point]):
    def __repr__(self) -> str:
        force_relative = self.repr_relative and self.fn.isupper()
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
        self.repr_relative = called_internally and self.repr_relative
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
    def __init__(self, fn: str, data: list[Point], is_first_command: bool=False) -> None:
        self.is_first_command = is_first_command
        super().__init__(fn, data)
        
    def __repr__(self) -> str:
        force_relative = self.repr_relative and self.fn.isupper()
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
            
    def transformed(self, t: Transform) -> Moveto:
        me = self.__class__(self.fn, self.data)
        me.start_point = self.start_point
        me.repr_relative = self.repr_relative
        me.is_first_command = self.is_first_command
        me.transform(t)
        return me
    
    def absolutize(self, prev_point: Point, *, called_internally=False) -> Point:
        self.repr_relative = called_internally and self.repr_relative
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
        if self.repr_relative and self.fn.isupper():
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

    def transformed(self, t: Transform) -> Command:
        assert False, 'Never be reached'

    def absolutize(self, prev_point: Point, *, called_internally=False) -> Point:
        self.repr_relative = called_internally and self.repr_relative
        if self.fn.isupper(): return self.end_point

        if self.fn == 'h':
            self.data = [x + prev_point.x for x in self.data]
        else:
            self.data = [y + prev_point.y for y in self.data]

        self.fn = self.fn.upper()
        return self.end_point

    def converted_to_lineto(self) -> Lineto:
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
        cmd.repr_relative = self.repr_relative
        return cmd



class EllipticalArc(CommandBase[EllipticalArcItem]):
    def __repr__(self) -> str:
        force_relative = self.repr_relative and self.fn.isupper()
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
        self.start_point.transform(t)
        for a in self.data:
            a.transform(t)

    def transformed(self, t: Transform) -> Command:
        me = self.converted_to_curves()
        me.transform(t)
        return me

    def absolutize(self, prev_point: Point, *, called_internally=False) -> Point:
        self.repr_relative = called_internally and self.repr_relative
        self.fn = self.fn.upper()
        return self.end_point

    def converted_to_curves(self) -> Curveto:
        data = []
        for arc in self.data:
            data += arc.converted_to_curve_points()
            
        fn = 'C' if self.fn.isupper() else 'c'
        curveto = Curveto(fn, data)
        curveto.start_point = self.start_point
        curveto.repr_relative = self.repr_relative
        return curveto
        


class Close(CommandBase[Point]):
    def __init__(self, fn: str) -> None:
        self.fn = fn
        super().__init__(fn, [])

    def __repr__(self) -> str:
        if self.repr_relative and self.fn.isupper():
            return self.fn.lower()
        return self.fn

    @property
    def end_point(self) -> Point:
        if self.data:
            return self.data[0]
        raise Exception('uninitialized start_point and end_point')

    @end_point.setter
    def end_point(self, val: Point) -> None:
        self.data.insert(0, val.clone())
        if len(self.data) > 1:
            self.data.pop()

    def transform(self, t: Transform) -> None:
        self.start_point.transform(t)
        self.data[0].transform(t)

    def transformed(self, t: Transform) -> Close:
        me = self.__class__(self.fn)
        me.start_point = self.start_point
        me.end_point = self.end_point
        me.repr_relative = self.repr_relative
        me.transform(t)
        return me
    
    def absolutize(self, _: Point, *, called_internally=False) -> Point:
        self.repr_relative = called_internally and self.repr_relative
        self.fn = 'Z'
        return self.end_point
    
