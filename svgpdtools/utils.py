from typing import Protocol
import math


class PointLike(Protocol):
    x: float
    y: float


DEFAULT_PRECISION = 6
_precision_ = DEFAULT_PRECISION

def precision(value: int) -> None:
    assert value >= 0
    global _precision_
    _precision_ = value
    


def number_repr(num: float) -> str:
    """
    Convert a float number to a string representation with a precision
    setting. The precision is set by `precision(int)` function. When
    formatting, this function uses the fixed-point notation and the
    precision. Then trimming trailing zeros after the decimal point.
    """
    if _precision_ == 0:
        return str(round(num))

    s = str(num)
    pos = -1
    for c in s:
        if pos > -1 and c.isnumeric():
            pos += 1
            continue
        
        if c == '.':
            pos = 0
        
    if pos >= _precision_:
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
