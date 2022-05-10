import unittest
import svgpdtools as PD


class TestPD(unittest.TestCase):
    def setUp(self):
        self.pd1 = PD.pathdata_from_string('m 10,20 10,-10 v 60 m -10,0 l 20,0 m 20,-60 c -10,0 -20,10 -20,30 0,20 10,30 20,30 C 60,70 70,60 70,40 c 0,-20 -10,-30 -20,-30 z m 0,10 v 40')
        self.pd2 = PD.pathdata_from_string('M 45,30 Q 35,30 35,40 q 0,10 10,10 z m 10,20 q 10,0 10,-10 0,-10 -10,-10 z')
        self.pd3 = PD.pathdata_from_string('m 30,45 a 20 20 0 11 20,0 z m 20,0 a 25 15 25 11 -20,0 24 12 345 10 20,0 m 5,-20 -30,0 m 15,0 0,15')
        
    def test_absolutize(self):
        PD.precision(0)
        self.pd1.absolutize()
        self.assertEqual(str(self.pd1), 'M 10,20 20,10 V 70 M 10,70 L 30,70 M 50,10 C 40,10 30,20 30,40 30,60 40,70 50,70 C 60,70 70,60 70,40 C 70,20 60,10 50,10 Z M 50,20 V 60')
        self.pd3.absolutize()
        self.assertEqual(str(self.pd3), 'M 30,45 A 20 20 0 11 50,45 Z M 50,45 A 25 15 25 11 30,45 24 12 345 10 50,45 M 55,25 25,25 M 40,25 40,40')

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
        self.pd1.transform(t)
        self.assertEqual(str(self.pd1), 'm 20,150 -10,-10 l 60,0 m 0,10 l 0,-20 m -60,-20 c 0,10 10,20 30,20 20,0 30,-10 30,-20 C 70,100 60,90 40,90 c -20,0 -30,10 -30,20 z m 10,0 l 40,0')

    def test_transform_rotate60(self):
        self.maxDiff = None
        PD.precision(6)
        t = PD.Transform.rotate(60, 40, 40)
        self.pd1.transform(t)
        self.assertEqual(str(self.pd1), 'm 42.320508,4.019238 13.660254,3.660254 l -51.961524,30 m -5,-8.660254 l 10,17.320508 m 61.961524,-12.679492 c -5,-8.660254 -18.660254,-12.320508 -35.980762,-2.320508 -17.320508,10 -20.980762,23.660254 -15.980762,32.320508 C 24.019238,72.320508 37.679492,75.980762 55,65.980762 c 17.320508,-10 20.980762,-23.660254 15.980762,-32.320508 z m -8.660254,5 l -34.641016,20')
        self.pd2.transform(t)
        self.assertEqual(str(self.pd2), 'M 51.160254,39.330127 Q 46.160254,30.669873 37.5,35.669873 q -8.660254,5 -3.660254,13.660254 z m -12.320508,18.660254 q 5,8.660254 13.660254,3.660254 8.660254,-5 3.660254,-13.660254 z')
        self.pd3.transform(t)
        self.assertEqual(str(self.pd3), 'm 30.669873,33.839746 a 20 20 60 11 10,17.320508 z m 10,17.320508 a 25 15 85 11 -10,-17.320508 24 12 45 10 10,17.320508 m 19.820508,-5.669873 -15,-25.980762 m 7.5,12.990381 -12.990381,7.5')


if __name__ == '__main__':
    unittest.main()
