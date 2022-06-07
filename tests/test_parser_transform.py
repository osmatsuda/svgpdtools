import unittest

from svgpdtools import Point, Transform, precision, pathdata_from_string, transform_from_string
import svgpdtools.parser as P


class TestParserTransformBasic(unittest.TestCase):
    def test_from_string(self):
        p = Point(1,1)
        t = P.transforms('translate( 40, 40)')
        _t = Transform.translate(40, 40)
        self.assertEqual(p.transformed(t.pop()), p.transformed(_t))

        t = P.transforms('scale(10 )')
        _t = Transform.scale(10)
        self.assertEqual(p.transformed(t.pop()), p.transformed(_t))

        t = P.transforms('scale(10, 20)')
        _t = Transform.scale(10, 20)
        self.assertEqual(p.transformed(t.pop()), p.transformed(_t))

        t = P.transforms('rotate(30)')
        _t = Transform.rotate(30)
        self.assertEqual(p.transformed(t.pop()), p.transformed(_t))
        
        t = P.transforms('rotate(30, 40, 40)')
        _t = Transform.rotate(30, 40, 40)
        self.assertEqual(p.transformed(t.pop()), p.transformed(_t))
        
        t = P.transforms('skewX(20)')
        _t = Transform.skewX(20)
        self.assertEqual(p.transformed(t.pop()), p.transformed(_t))
        
        t = P.transforms('skewY(20)')
        _t = Transform.skewY(20)
        self.assertEqual(p.transformed(t.pop()), p.transformed(_t))
        
        t = P.transforms('matrix(1,2,3,4,5,6)')
        _t = Transform.matrix(1,2,3,4,5,6)
        self.assertEqual(p.transformed(t.pop()), p.transformed(_t))

        t = P.transforms('')
        self.assertEqual(len(t), 0)

    def test_from_string_complex(self):
        t_str = '''
        translate(40,40)
        rotate(60)
        translate(-40,-40)
        '''
        ts = P.transforms(t_str)
        self.assertEqual(' '.join([str(t) for t in ts]),
                         'translate(40, 40) rotate(60) translate(-40, -40)')

        t0 = Transform.rotate(60, 40, 40)
        t1 = Transform.concat(ts)
        t2 = transform_from_string(t_str)
        t3 = transform_from_string('rotate(60, 40, 40)')
        p = Point(100, 100)
        p_moved = p.transformed(t0)
        self.assertEqual(p.transformed(t1), p_moved)
        self.assertEqual(p.transformed(t2), p_moved)
        self.assertEqual(p.transformed(t3), p_moved)

        self.assertEqual(p.transformed(t1).transformed(t1.inversed()), p)

    def test_parse_error(self):
        with self.assertRaises(Exception):
            transform_from_string(',translate(1)')

        with self.assertRaises(Exception):
            transform_from_string('transform(1)')

        with self.assertRaises(Exception):
            transform_from_string('translate(1,2,3)')
