import unittest

from svgpdtools import Point, Transform


class TestPoint(unittest.TestCase):
    def test_point(self):
        p = Point(1, 1)
        r = Transform.rotate(90)
        self.assertEqual(f'{p}', '1,1')
        p.transform(r)
        self.assertEqual(f'{p}', '-1,1')

        p = Point(1, 1)
        t = Transform.translate(1)
        p.transform(r * t)
        self.assertEqual(f'{p}', '-1,2')


if __name__ == '__main__':
    unittest.main()
