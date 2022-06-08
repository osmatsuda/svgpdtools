import unittest
import svgpdtools as PD


class TestPD(unittest.TestCase):
    def setUp(self):
        self.pd1 = PD.pathdata_from_string('m 10,20 10,-10 v 60 m -10,0 l 20,0 m 20,-60 c -10,0 -20,10 -20,30 0,20 10,30 20,30 C 60,70 70,60 70,40 c 0,-20 -10,-30 -20,-30 z m 0,10 v 40')
        self.pd2 = PD.pathdata_from_string('M 45,30 Q 35,30 35,40 q 0,10 10,10 z m 10,20 q 10,0 10,-10 0,-10 -10,-10 z')
        self.pd3 = PD.pathdata_from_string('m 30,45 a 20 20 0 11 20,0 z m 20,0 a 25 15 25 11 -20,0 24 12 345 10 20,0 m 5,-20 -30,0 m 15,0 0,15')

    def test_basic(self):
        pd = PD.pathdata_from_string('')
        pd.normalize()
        self.assertEqual(str(pd), '')
        
    #@unittest.skip('')
    def test_normalize2(self):
        self.pd1.normalize(collapse_hv_lineto=True, repr_relative=True)
        self.assertEqual(str(self.pd1),
                         'm 10,20 l 10,-10 0,60 m -10,0 l 20,0 m 20,-60 c -10,0 -20,10 -20,30 0,20 10,30 20,30 10,0 20,-10 20,-30 0,-20 -10,-30 -20,-30 z m 0,10 l 0,40')
        self.pd2.normalize(repr_relative=True)
        self.pd2.normalize()
        self.assertEqual(str(self.pd2),
                         'M 45,30 Q 35,30 35,40 35,50 45,50 Z M 55,50 Q 65,50 65,40 65,30 55,30 Z')
        PD.precision(3)
        self.pd3.normalize(collapse_elliptical_arc=True, allow_implicit_lineto=True)
        self.maxDiff = None
        self.assertEqual(str(self.pd3),
                         'M 30,45 C 23.844,41.446 20,34.787 20,27.679 20,20.572 23.844,13.913 30,10.359 36.156,6.805 43.844,6.805 50,10.359 56.156,13.913 60,20.572 60,27.679 60,32.924 57.85,38.113 54.142,41.822 52.926,43.038 51.489,44.14 50,45 Z M 50,45 C 58.328,47.809 65.728,53.381 69.247,59.494 72.767,65.606 71.961,71.486 67.152,74.789 62.343,78.092 54.139,78.4 45.81,75.591 37.482,72.782 30.082,67.209 26.563,61.097 23.966,56.587 23.69,52.039 25.811,48.701 26.756,47.215 28.218,45.923 30,45 21.743,47.134 14.525,51.382 11.226,56.05 7.926,60.718 8.962,65.216 13.919,67.75 18.877,70.284 27.13,70.533 35.387,68.399 43.644,66.265 50.862,62.017 54.161,57.349 56.596,53.905 56.698,50.427 54.439,47.871 53.416,46.715 51.867,45.712 50,45 M 55,25 25,25 M 40,25 40,40')

    def test_normalize(self):
        self.pd1.normalize()
        self.assertEqual(str(self.pd1),
                         'M 10,20 L 20,10 V 70 M 10,70 L 30,70 M 50,10 C 40,10 30,20 30,40 30,60 40,70 50,70 60,70 70,60 70,40 70,20 60,10 50,10 Z M 50,20 V 60')
        self.pd1.normalize(collapse_hv_lineto=True)
        self.assertEqual(str(self.pd1),
                         'M 10,20 L 20,10 20,70 M 10,70 L 30,70 M 50,10 C 40,10 30,20 30,40 30,60 40,70 50,70 60,70 70,60 70,40 70,20 60,10 50,10 Z M 50,20 L 50,60')
        self.pd2.normalize()
        self.assertEqual(str(self.pd2),
                         'M 45,30 Q 35,30 35,40 35,50 45,50 Z M 55,50 Q 65,50 65,40 65,30 55,30 Z')
        self.pd3.normalize()
        self.assertEqual(str(self.pd3),
                         'M 30,45 A 20 20 0 1 1 50,45 Z M 50,45 A 25 15 25 1 1 30,45 24 12 345 1 0 50,45 M 55,25 L 25,25 M 40,25 L 40,40')
        
    def test_absolutize(self):
        PD.precision(0)
        self.pd1.absolutize()
        self.assertEqual(str(self.pd1), 'M 10,20 20,10 V 70 M 10,70 L 30,70 M 50,10 C 40,10 30,20 30,40 30,60 40,70 50,70 C 60,70 70,60 70,40 C 70,20 60,10 50,10 Z M 50,20 V 60')
        self.pd3.absolutize()
        self.assertEqual(str(self.pd3), 'M 30,45 A 20 20 0 1 1 50,45 Z M 50,45 A 25 15 25 1 1 30,45 24 12 345 1 0 50,45 M 55,25 25,25 M 40,25 40,40')

    def test_transform_moveto_abs(self):
        PD.precision(0)
        pd = PD.pathdata_from_string('m 0,0 100,0 0,100 -100,0 0,-100')
        t = PD.Transform.translate(100, 0)
        pd.transform(t)
        pd.absolutize()
        self.assertEqual(str(pd), 'M 100,0 200,0 200,100 100,100 100,0')
        
    def test_transform_moveto(self):
        PD.precision(0)
        pd = PD.pathdata_from_string('m 0,0 100,0 0,100 -100,0 0,-100')
        t = PD.Transform.translate(100, 0)
        pd.transform(t)
        self.assertEqual(str(pd), 'm 100,0 100,0 0,100 -100,0 0,-100')
        
    def test_transform(self):
        PD.precision(0)
        # translate(0,160) rotate(-90)
        t = PD.Transform.translate(0, 160) * PD.Transform.rotate(-90)
        self.pd1.transform(t, warning=False)
        self.assertEqual(str(self.pd1), 'm 20,150 -10,-10 l 60,0 m 0,10 l 0,-20 m -60,-20 c 0,10 10,20 30,20 20,0 30,-10 30,-20 C 70,100 60,90 40,90 c -20,0 -30,10 -30,20 z m 10,0 l 40,0')

    def test_transform_rotate60(self):
        self.maxDiff = None
        PD.precision(6)
        t = PD.Transform.rotate(60, 40, 40)
        self.pd1.transform(t, warning=False)
        self.assertEqual(str(self.pd1), 'm 42.320508,4.019238 13.660254,3.660254 l -51.961524,30 m -5,-8.660254 l 10,17.320508 m 61.961524,-12.679492 c -5,-8.660254 -18.660254,-12.320508 -35.980762,-2.320508 -17.320508,10 -20.980762,23.660254 -15.980762,32.320508 C 24.019238,72.320508 37.679492,75.980762 55,65.980762 c 17.320508,-10 20.980762,-23.660254 15.980762,-32.320508 z m -8.660254,5 l -34.641016,20')
        self.pd2.transform(t)
        self.assertEqual(str(self.pd2), 'M 51.160254,39.330127 Q 46.160254,30.669873 37.5,35.669873 q -8.660254,5 -3.660254,13.660254 z m -12.320508,18.660254 q 5,8.660254 13.660254,3.660254 8.660254,-5 3.660254,-13.660254 z')
        self.pd3.transform(t, warning=False)
        self.assertEqual(str(self.pd3), 'm 30.669873,33.839746 a 20 20 60 1 1 10,17.320508 z m 10,17.320508 a 25 15 85 1 1 -10,-17.320508 24 12 45 1 0 10,17.320508 m 19.820508,-5.669873 -15,-25.980762 m 7.5,12.990381 -12.990381,7.5')


if __name__ == '__main__':
    unittest.main()
