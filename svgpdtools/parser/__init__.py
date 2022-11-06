from typing import Sequence

from svgpdtools import PathData
from svgpdtools import Transform
from svgpdtools.command import Command, Moveto, Lineto, Curveto, HorizontalAndVerticalLineto,\
    EllipticalArc, EllipticalArcItem, Close
from svgpdtools.graphics import Point



def pathdata(d: str) -> PathData:
    """
    Convert a path data string to a `svgpdtools.PathData` object. A path
    data string is a value of the `d` property of the SVG-path element.
    """
    pd = PathData()
    buff = ''
    for c in d:
        if c.lower() in 'mzlhvcsqta':
            if buff:
                pd.append(_make_command(buff.lstrip()))
            buff = c
        else:
            buff += c
        
    buff = buff.lstrip()
    if buff:
        pd.append(_make_command(buff))

    return pd



def transforms(src: str) -> list[Transform]:
    """
    Convert a string representation of SVG transfom functions to a list of
    `svgpdtools.Transform` objects.
    The syntax of transform functions are the same as the SVG `transform`
    attribute.
    """
    funs = []
    rest = _consume_wsp(src)
    while rest:
        _rest = rest
        fun, rest = _make_transform_function(rest)
        funs.append(fun)
        rest = _consume_comma_wsp(rest)
        if rest == _rest:
            break

    if rest:
        raise Exception(f'Failed parsing transform functions: {src}')

    return funs



def _make_transform_function(src: str) -> tuple[Transform, str]:
    fn, rest = _consume_tf_name(src)
    args, rest = _consume_tf_args(_consume_wsp(rest), fn)
    def unknown_function(*args):
        raise Exception(f'Unknown transform function: {fn}{args}')
    
    factory = getattr(Transform, fn, unknown_function)
    return factory(*args), rest

def _consume_tf_name(src: str) -> tuple[str, str]:
    for fn in 'matrix translate scale rotate skewX skewY'.split():
        if src.startswith(fn):
            return fn, src[len(fn):]

    raise Exception(f'Unknown transform function: {src}')

_tf_args_size_table = {
    # command_name: (required, optional)
    'matrix': (6, 0),
    'translate': (1, 1),
    'scale': (1, 1),
    'rotate': (1, 2),
    'skewX': (1, 0),
    'skewY': (1, 0),
}
def _consume_tf_args(src: str, fn: str) -> tuple[list[float], str]:
    if src[0] != '(':
        raise Exception(f'Cannot parse transform function\'s arguments {src}')

    args_size = _tf_args_size_table[fn]
    args, rest = _consume_float_nums(_consume_wsp(src[1:]), args_size[0])

    rest = _consume_wsp(rest)
    if rest[0] == ')':
        return args, rest[1:]
    
    args_opt, rest = _consume_float_nums(_consume_comma_wsp(rest), args_size[1])
    rest = _consume_wsp(rest)
    if rest[0] != ')':
        raise Exception(f'Cannot parse transform function\'s arguments {src}')

    return args + args_opt, rest[1:]



def _make_command(src: str) -> Command:
    fn = src[0]
    fn_ = src[0].lower()
    rest = _consume_wsp(src[1:])
    cmd: Command
    prms: Sequence
    
    if fn_ ==  'm':
        prms, rest = _consume_points(rest, 1)
        cmd = Moveto(fn, prms)
    elif fn_ == 'l':
        prms, rest = _consume_points(rest, 1)
        cmd = Lineto(fn, prms)
    elif fn_ == 't':
        prms, rest = _consume_points(rest, 1)
        cmd = Curveto(fn, prms)
    elif fn_ == 'c':
        prms, rest = _consume_points(rest, 3)
        cmd = Curveto(fn, prms)
    elif fn_ in 'sq':
        prms, rest = _consume_points(rest, 2)
        cmd = Curveto(fn, prms)
    elif fn_ in 'hv':
        prms, rest = _consume_float_nums(rest)
        cmd = HorizontalAndVerticalLineto(fn, prms)
    elif fn_ == 'a':
        prms, rest = _consume_elliptical_params(rest)
        cmd = EllipticalArc(fn, prms)
    else:
        if fn_ != 'z':
            raise Exception(f'Unknown command: {src}')
        cmd = Close(fn)

    if _consume_wsp(rest):
        raise Exception(f'Incorrect set of parameters: {src}')

    return cmd

def _consume_elliptical_params(src: str) -> tuple[list[EllipticalArcItem], str]:
    item, rest = _consume_elliptical_param(src)
    items = [item]
    while True:
        rest = _consume_comma_wsp(rest)
        if rest:
            item, rest = _consume_elliptical_param(rest)
            items.append(item)
        else:
            break
        
    return items, rest

def _consume_elliptical_param(src: str) -> tuple[EllipticalArcItem, str]:
    (rx, ry, phi), rest = _consume_float_nums(src, 3)
    flags, rest = _consume_flags(_consume_comma_wsp(rest), 2)
    to_p, rest = _consume_point(_consume_comma_wsp(rest))
    return EllipticalArcItem((rx, ry), phi, flags[0], flags[1], to_p), rest

def _consume_flags(src: str, length: int) -> tuple[list[bool], str]:
    fs = []
    filled = False
    for i in range(len(src)):
        f = src[i]
        if f == '0':
            fs.append(False)
        elif f == '1':
            fs.append(True)
        elif ord(f) in (0x9, 0xA, 0xC, 0xD, 0x20, 0x2c):
            continue
        else:
            raise Exception(f'A flag token should be "0" or "1": {src}')
            
        if len(fs) == length:
            filled = True
            break

    if not filled:
        raise Exception('Be short of flag tokens.')

    return fs, src[i+1:]
    
def _consume_float_nums(src: str, length: int=-1) -> tuple[list[float], str]:
    ns = []
    rest = src
    while True:
        if length == 0:
            break 
        n, rest = _consume_number(_consume_comma_wsp(rest))
        ns.append(float(n))
        if length > 0:
            length -= 1
        elif not rest.strip():
            break

    return ns, rest    
    
def _consume_points(src: str, unit_length: int=1) -> tuple[list[Point], str]:
    p, rest = _consume_point(src)
    ps = [p]
    while True:
        rest = _consume_comma_wsp(rest)
        if rest:
            p, rest = _consume_point(rest)
            ps.append(p)
        else:
            break

    if len(ps) % unit_length != 0:
        raise Exception(f'Incorrect set of parameters: {src}')

    return ps, rest

def _consume_point(src: str) -> tuple[Point, str]:
    (x, y), rest = _consume_float_nums(src, 2)
    return Point(x, y), rest
    
def _consume_number(src: str) -> tuple[str, str]:
    buff = ''
    state = 0
    for c in src:
        if c in '+-':
            if not (state == 0 or state == 4):
                break
            buff += c
        elif c.isdigit():
            buff += c
            if state == 0:
                state = 1
            elif state == 2:
                state = 3
            elif state == 4:
                state = 5
        elif state < 2 and c == '.':
            buff += c
            if state == 1:
                state = 3
            else:
                state = 2
        elif c in 'eE':
            if state == 0 or state == 2 or state == 4:
                raise Exception(f'illegal number token: {buff+c}')
            buff += c.upper()
            state = 4
        else:
            break

    if state == 4:
        raise Exception(f'illegal number token: {buff}')
    return buff, src[len(buff):]

def _consume_wsp(src: str) -> str:
    i = 0
    for c in src:
        if ord(c) in (0x9, 0xA, 0xB, 0xC, 0xD, 0x20):
            i+=1
        else:
            break
    return src[i:]
    
def _consume_comma_wsp(src: str) -> str:
    i = 0
    for c in src:
        if ord(c) in (0x9, 0xA, 0xB, 0xC, 0xD, 0x20, 0x2c):
            i+=1
        else:
            break
    return src[i:]
