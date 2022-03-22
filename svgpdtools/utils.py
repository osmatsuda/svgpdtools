from typing import Protocol


class PointLike(Protocol):
    x: float
    y: float


def number_repr(num: float, *, precision: int) -> str:
    if precision == 0:
        return str(round(num))

    s = str(num)
    dp = -1
    for c in s:
        if dp > -1 and c.isnumeric():
            dp += 1
            continue
        
        if c == '.': dp = 0
        
    if dp >= precision:
        s = (f'{{:.{precision}f}}').format(num)
        
    if s.find('.') > -1:
        s = s.rstrip('0')
        if s[-1] == '.':
            s = s[:-1]

    return s
