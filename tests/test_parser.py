import unittest

from svgpdtools import Point, Transform, precision, pathdata_from_string, transform_from_string
import svgpdtools.parser as P


class TestParserCommand(unittest.TestCase):
    #@unittest.skip('')
    def test_from_string_close(self):
        precision(0)
        src = 'm 10,20 10,-10 v 60 m -10,0 l 20,0 m 20,-60 c -10,0 -20,10 -20,30 0,20 10,30 20,30 C 60,70 70,60 70,40 c 0,-20 -10,-30 -20,-30 z m 0,10 v 40'
        pd = pathdata_from_string(src)
        self.assertEqual(str(pd), src)
        
    def test_from_string_elliptical_arc(self):
        precision(6)
        src = 'm 30,45 a 20 20 0 11 20,0 z m 20,0 a 25 15 25 11 -20,0 24 12 345 10 20,0 m 5,-20 -30,0 m 15,0 0,15'
        pd = pathdata_from_string(src)
        self.assertEqual(len(pd.data), 7)
        arcs = [] + pd.data[1].data + pd.data[4].data
        arc_starts = [str(e._from_point) for e in arcs]
        earc_centers = [str(e._elliptical_arc_center) for e in arcs]
        earc_starts = [str(e._elliptical_arc_start) for e in arcs]
        self.assertEqual(arc_starts, ['30,45', '50,45', '30,45'])
        self.assertEqual(earc_centers, ['40,27.679492', '47.905081,60.295468', '32.693603,56.699606'])
        self.assertEqual(earc_starts, ['60,27.679492', '70.562775,70.860925', '55.875823,50.487949'])

        self.assertEqual(str(pd), 'm 30,45 a 20 20 0 1 1 20,0 z m 20,0 a 25 15 25 1 1 -20,0 24 12 345 1 0 20,0 m 5,-20 -30,0 m 15,0 0,15')

    def test_from_string_basic(self):
        precision(0)
        pd = pathdata_from_string('m 0,0')
        self.assertEqual(str(pd), 'm 0,0')
        pd = pathdata_from_string('m1 0')
        self.assertEqual(str(pd), 'm 1,0')
        pd = pathdata_from_string('M 2.0.0')
        self.assertEqual(str(pd), 'M 2,0')

    def test_from_string_basic2(self):
        precision(0)
        pd = pathdata_from_string('m 10 20 10-10-10,0 l 20,0 20 -60 -10 0')
        self.assertEqual(str(pd), 'm 10,20 10,-10 -10,0 l 20,0 20,-60 -10,0')

        pd_src = 'm 0,0 c 100,-300 300,-300 400,0 s 300,300 400,0 q 200,-600 -400,0 t -400,0 400,0 400,0 q 100,-300 -400,0 t -400,0'
        pd = pathdata_from_string(pd_src)
        self.assertEqual(str(pd), pd_src)

        pd_src = 'm 0,0 h 100 100 50 v 200,50 h-250 v 250'
        pd = pathdata_from_string(pd_src)
        self.assertEqual(str(pd), 'm 0,0 h 100 100 50 v 200 50 h -250 v 250')

class TestParserPrivate(unittest.TestCase):
    def test_consume_flags(self):
        src = '11 20,0'
        flgs, rest = P._consume_flags(src, 2)
        self.assertEqual(flgs, [True, True])
        self.assertEqual(rest, ' 20,0')
        
    def test_consume_float_nums(self):
        src = '20 20 0 11 20,0'
        (rx, ry, phi), rest = P._consume_float_nums(src, 3)
        self.assertEqual([rx, ry, phi], [20.0, 20.0, 0.0])
        self.assertEqual(rest, ' 11 20,0')
        
    def test_consume_comma_wsp(self):
        self.assertEqual(P._consume_comma_wsp('  ,1'), '1')
        self.assertEqual(P._consume_comma_wsp(',  1'), '1')
        self.assertEqual(P._consume_comma_wsp('1'), '1')
        self.assertEqual(P._consume_wsp('  1'), '1')

    def test_consume_number(self):
        src = '123, 456'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '123')
        self.assertEqual(rest, ', 456')

        src = '119.28572 36.428571 '
        n, rest = P._consume_number(src)
        self.assertEqual(n, '119.28572')
        self.assertEqual(rest, ' 36.428571 ')

        src = '-119.28572 36.428571'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '-119.28572')
        self.assertEqual(rest, ' 36.428571')
        src = '+119.28572 36.428571'
        n, rest = P._consume_number(src)

        self.assertEqual(n, '+119.28572')
        self.assertEqual(rest, ' 36.428571')

        src = '+.28572 36.428571'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '+.28572')
        self.assertEqual(rest, ' 36.428571')

        src = '.28572,36.428571'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '.28572')
        self.assertEqual(rest, ',36.428571')

        src = '1.28572.36'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '1.28572')
        self.assertEqual(rest, '.36')

        src = '.28572.36'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '.28572')
        self.assertEqual(rest, '.36')

        src = '1.28572-36'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '1.28572')
        self.assertEqual(rest, '-36')

        src = '-1.2857e-2+36'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '-1.2857E-2')
        self.assertEqual(rest, '+36')

        src = '2.e-1 ,36.428571'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '2.E-1')
        self.assertEqual(rest, ' ,36.428571')
        
        src = '+e1,36.428571'
        with self.assertRaises(Exception):
            n, rest = P._consume_number(src)

        src = 'e1,36.428571'
        with self.assertRaises(Exception):
            n, rest = P._consume_number(src)

        src = '123e,36.428571'
        with self.assertRaises(Exception):
            n, rest = P._consume_number(src)
        
        src = '2.123e56,36.428571'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '2.123E56')
        self.assertEqual(rest, ',36.428571')

        src = '123e-5,36.428571'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '123E-5')
        self.assertEqual(rest, ',36.428571')

        src = '\n'
        n, rest = P._consume_number(src)
        self.assertEqual(n, '')
        self.assertEqual(rest, '\n')

        src = '1 2 3, 4'
        ns, rest = P._consume_float_nums(src)
        self.assertEqual(ns, [1,2,3,4])
        self.assertEqual(rest, '')
        ns, rest = P._consume_float_nums(src, 3)
        self.assertEqual(ns, [1,2,3])
        self.assertEqual(rest, ', 4')
        

if __name__ == '__main__':
    unittest.main()
