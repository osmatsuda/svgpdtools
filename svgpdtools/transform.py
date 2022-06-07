from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional, Iterable

from svgpdtools.utils import PointLike, deg2rad, number_repr


@dataclass
class _OrgReprForm:
    command: str
    values: list[float] = field(default_factory=list)


class Transform:
    def __init__(self, a=1., b=0., c=0., d=1., e=0., f=0.) -> None:
        self.a, self.b, self.c, self.d, self.e, self.f = a, b, c, d, e, f
        self._org_repr_form: Optional[_OrgReprForm] = None

    def __repr__(self) -> str:
        if self._org_repr_form is None:
            return self.raw_repr()

        vals = [number_repr(n) for n in self._org_repr_form.values]
        return f"{self._org_repr_form.command}({', '.join(vals)})"
        
    def raw_repr(self) -> str:
        l = max([len(str(self.__getattribute__(attr))) for attr in 'abcdef'])
        r = ''
        for attrs in ['ace', 'bdf']:
            _r = ''
            
            for attr in attrs:
                _r += ' ' + f'{self.__getattribute__(attr):#}'.rjust(l)
            r += _r[1:] + '\n'
            
        r += f"{'0'.rjust(l)} {'0'.rjust(l)} {'1'.rjust(l)}"
        return r

    def apply_point(self, p: PointLike) -> tuple[float, float]:
        return (
            self.a * p.x + self.c * p.y + self.e,
            self.b * p.x + self.d * p.y + self.f
        )

    def concatenated(self, *ts: Transform) -> Transform:
        r = self.__mul__(ts[0])
        for t in ts[1:]:
            r = r.__mul__(t)
        return r
        
    def __mul__(self, other: Transform) -> Transform:
        a = self.a * other.a + self.c * other.b
        b = self.b * other.a + self.d * other.b
        c = self.a * other.c + self.c * other.d
        d = self.b * other.c + self.d * other.d
        e = self.a * other.e + self.c * other.f + self.e
        f = self.b * other.e + self.d * other.f + self.f
        return Transform(a, b, c, d, e, f)

    def inversed(self) -> Transform:
        det = self.a * self.d - self.b * self.c
        assert not math.isclose(det, 0, abs_tol=1e-7)

        a = self.d / det
        b = -self.b / det
        c = -self.c / det
        d = self.a / det
        e = (self.c * self.f - self.d * self.e) / det
        f = (self.b * self.e - self.a * self.f) / det
        return Transform(a, b, c, d, e, f)

    @staticmethod
    def matrix(a: float, b: float, c: float, d: float, e: float, f: float) -> Transform:
        t = Transform(a, b, c, d, e, f)
        t._org_repr_form = _OrgReprForm('matrix', list(locals().values()))
        return t
    
    @staticmethod
    def translate(dx: float, dy=None, /) -> Transform:
        org_args = list(filter(lambda v: v is not None, locals().values()))
        if dy is None:
            dy = 0.
        t = Transform(e=dx, f=dy)
        t._org_repr_form = _OrgReprForm('translate', org_args)
        return t

    @staticmethod
    def scale(sx: float, sy=None, /) -> Transform:
        org_args = list(filter(lambda v: v is not None, locals().values()))
        if sy is None:
            sy = sx
        t = Transform(a=sx, d=sy)
        t._org_repr_form = _OrgReprForm('scale', org_args)
        return t

    @staticmethod
    def rotate(deg: float, cx=None, cy=None, /) -> Transform:
        org_args = list(filter(lambda v: v is not None, locals().values()))
        if cx is None: cx = 0.
        if cy is None: cy = 0.
        t1 = Transform.translate(cx, cy)
        t2 = Transform.translate(-cx, -cy)
        cos = math.cos(deg2rad(deg))
        sin = math.sin(deg2rad(deg))
        tr = Transform(a=cos, b=sin, c=-sin, d=cos)
        t = t1.concatenated(tr, t2)
        t._org_repr_form = _OrgReprForm('rotate', org_args)
        return t

    @staticmethod
    def skewX(deg: float) -> Transform:
        t = Transform(c=math.tan(deg2rad(deg)))
        t._org_repr_form = _OrgReprForm('skewX', [deg])
        return t

    @staticmethod
    def skewY(deg: float) -> Transform:
        t = Transform(b=math.tan(deg2rad(deg)))
        t._org_repr_form = _OrgReprForm('skewY', [deg])
        return t

    @staticmethod
    def concat(ts: Iterable[Transform]) -> Transform:
        t = Transform()
        for _t in ts:
            t = t * _t
        return t
