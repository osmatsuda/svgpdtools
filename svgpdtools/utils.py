from typing import Protocol
from dataclasses import dataclass
import math


class PointLike(Protocol):
    x: float
    y: float


DEFAULT_PRECISION = 6
_precision_ = DEFAULT_PRECISION

def precision(value: int) -> None:
    global _precision_
    _precision_ = value
    


def number_repr(num: float) -> str:
    if _precision_ == 0:
        return str(round(num))

    s = str(num)
    dp = -1
    for c in s:
        if dp > -1 and c.isnumeric():
            dp += 1
            continue
        
        if c == '.':
            dp = 0
        
    if dp >= _precision_:
        s = (f'{{:.{_precision_}f}}').format(num)
        
    if s.find('.') > -1:
        s = s.rstrip('0')
        if s[-1] == '.':
            s = s[:-1]
            if s == '-0':
                s = '0'

    return s


def rad2deg(rad: float) -> float:
    return rad * 180 / math.pi

def deg2rad(deg: float) -> float:
    return deg * math.pi / 180.0
