from __future__ import annotations
import math
from dataclasses import dataclass

from svgpdtools.utils import PointLike


class Transform:
    def __init__(self, a=1., b=0., c=0., d=1., e=0., f=0.):
        self.a, self.b, self.c, self.d, self.e, self.f = a, b, c, d, e, f

    def __repr__(self) -> str:
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

    @staticmethod
    def translate(dx: float, dy = 0., /) -> Transform:
        return Transform(e=dx, f=dy)

    @staticmethod
    def scale(sx: float, sy=None, /) -> Transform:
        if sy is None:
            sy = sx
            
        return Transform(a=sx, d=sy)

    @staticmethod
    def rotate(deg: float, cx=0., cy=0., /) -> Transform:
        t1 = Transform.translate(cx, cy)
        t2 = Transform.translate(-cx, -cy)

        cos, sin = math.cos(_deg2rad(deg)), math.sin(_deg2rad(deg))
        tr = Transform(a=cos, b=sin, c=-sin, d=cos)

        return t1.concatenated(tr, t2)


def _deg2rad(deg: float) -> float:
    return deg * math.pi / 180.0