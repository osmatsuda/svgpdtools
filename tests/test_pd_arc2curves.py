import unittest, pathlib, math, random
import xml.etree.ElementTree as ET

import svgpdtools as PD


class TestPDArc2Curves(unittest.TestCase):
    @unittest.skip('')
    def test_main(self):
        _make_test_arc2curves_src_svg()
        _make_test_arc2curves_svg()



from .graphics import circle_from_3points, random_3points

def _make_test_arc2curves_svg():
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    curdir = pathlib.Path(__file__).parent
    tree = ET.parse(curdir / 'images/test_pd_arc2curves_src.svg')
    
    svg = tree.getroot()
    for g in svg.iterfind('./{*}g'):
        path = g.find('./{*}path[@class="test_pd_arc2curves"]')
        pd = PD.pathdata_from_string(path.get('d'))
        for i in range(len(pd.data)):
            cmd = pd.data[i]
            if isinstance(cmd, PD.command.EllipticalArc):
                cmd = cmd.converted_to_curves()
                break
        pd.data[i] = cmd
        _path = ET.fromstring(f'<path fill="none" stroke="red" stroke-width="3" d="{pd}"/>')
        g.append(_path)        

    tree.write(curdir / 'images/test_pd_arc2curves.svg', encoding='unicode')

    

def _make_test_arc2curves_src_svg():
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    curdir = pathlib.Path(__file__).parent
    tree = ET.parse(curdir / 'test_pd_arc2curves_src_src.svg')
    
    svg = tree.getroot()
    for row in '1234':
        for col in 'ABCD':
            g = svg.find(f'./{{*}}g[@id="{col+row}"]')
            _make_elliptical_arc(g)

    tree.write(curdir / 'images/test_pd_arc2curves_src.svg', encoding='unicode')



from .graphics import Point, Circle, EllipticalArc

def _out_of_range(p: Point, rect_size: float) -> bool:
    return p.x < 0 or p.x > rect_size or p.y < 0 or p.y > rect_size

def _make_elliptical_arc(container):
    rect_size = 1000.
    abc = random_3points(rect_size, rect_size*.1)
    circle = circle_from_3points(*abc)
    while _out_of_range(circle.c, rect_size):
        abc = random_3points(rect_size, rect_size*.1)
        circle = circle_from_3points(*abc)

    container.append(ET.fromstring(circle.svg_repr(stroke='pink', stroke_width='10')))

    a = abc[0].svg_repr(10, color='red')
    container.append(ET.fromstring(a))
    b = abc[1].svg_repr(10)
    container.append(ET.fromstring(b))
    c = abc[2].svg_repr(10, color='blue')
    container.append(ET.fromstring(c))

    phi = 5 * math.floor(72 * random.random())
    sx = 1.5 - .75*random.random()
    sy = .7 + .25 * random.random() if sx > 1 else 1.1 + .25*random.random()
    rotate = PD.Transform.rotate(phi, circle.c.x, circle.c.y)
    mrotate = PD.Transform.rotate(-phi, circle.c.x, circle.c.y)
    scale = PD.Transform.scale(sx, sy)
    translate = PD.Transform.translate(circle.c.x, circle.c.y)
    mtranslate = PD.Transform.translate(-circle.c.x, -circle.c.y)
    t_for_abc =  rotate * translate * scale * mtranslate * mrotate
    flags = _large_arc_and_sweep_flags(
        _angle_from_x_axis(circle, abc[0]),
        _angle_from_x_axis(circle, abc[1]),
        _angle_from_x_axis(circle, abc[2]),
    )
    
    e_arc = EllipticalArc(
        radii = (sx*circle.r, sy*circle.r),
        x_axis_rotation = phi,
        flags = flags,
        from_point = abc[0].transformed(t_for_abc),
        to_point = abc[2].transformed(t_for_abc),
    )
    e_arc_element = ET.fromstring(e_arc.svg_repr(stroke='aqua', stroke_width='10'))
    e_arc_element.set('class', 'test_pd_arc2curves')
    container.append(e_arc_element)
    a_on_arc = e_arc.from_point.svg_repr(15, color='red', dot='A')
    container.append(ET.fromstring(a_on_arc))
    b_on_arc = abc[1].transformed(t_for_abc).svg_repr(15, dot='A')
    container.append(ET.fromstring(b_on_arc))
    c_on_arc = e_arc.to_point.svg_repr(15, color='blue', dot='A')
    container.append(ET.fromstring(c_on_arc))

    
def _large_arc_and_sweep_flags(start: float, mid: float, end: float) -> tuple[bool, bool]:
    two_pi = math.pi * 2
    to_mid = (mid - start) % two_pi
    to_end = (end - start) % two_pi
    is_sweep = to_mid < to_end
    is_large = to_end > math.pi if is_sweep else to_end < math.pi
    return is_large, is_sweep


def _angle_from_x_axis(circle: Circle, p: Point) -> float:
    assert math.isclose(p.distance_to(circle.c), circle.r)
    x = p.x - circle.c.x
    y = p.y - circle.c.y
    r = circle.r

    if math.isclose(y, 0, abs_tol=1e-7):
        if x > 0:
            return 0.
        return math.pi

    if math.isclose(x, 0, abs_tol=1e-7):
        if y > 0:
            return math.pi * .5
        return math.pi * 1.5

    theta = math.atan(y / x)
    if math.isclose(math.acos(x / r), math.asin(y / r)):
        return theta

    if x < 0 and y > 0:
        return math.pi + theta
    if x > 0 and y < 0:
        return 2 * math.pi - abs(theta)

    return math.pi + theta
