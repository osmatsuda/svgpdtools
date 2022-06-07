import unittest

from svgpdtools import PathData, Transform, precision, pathdata_from_string, transform_from_string
from svgpdtools.terminal_command import _PathDataViewer, _IndentedBox
import svgpdtools.parser as P


class TestPathView(unittest.TestCase):
    def setUp(self):
        self.src1 = 'm 10,20 10,-10 v 60 m -10,0 l 20,0 m 20,-60 c -10,0 -20,10 -20,30 0,20 10,30 20,30 C 60,70 70,60 70,40 c 0,-20 -10,-30 -20,-30 z m 0,10 v 40'
        self.pd1 = pathdata_from_string(self.src1)

        self.src2 = 'M 621.233134,535.81687 C 446.824765,508.269704 266.375834,530.368135 151.857303,593.298337 37.338772,656.228539 3.220491,752.039044 63.11033,842.516412 123.000168,932.99378 269.330818,1006.705854 443.739188,1034.25302 618.147557,1061.800186 798.596488,1039.701755 913.115019,976.771553 973.631197,943.516714 1014.07925,898.892637 1026.669807,851.492898'
        self.pd2 = pathdata_from_string(self.src2)

    def test_pd_view_repr(self):
        view_repr = _PathDataViewer(self.pd1)
        self.assertEqual(list(view_repr),
                         [('m', ['10,20', '10,-10']),
                          ('v', ['60']),
                          ('m', ['-10,0']),
                          ('l', ['20,0']),
                          ('m', ['20,-60']),
                          ('c', ['-10,0 -20,10 -20,30',
                                 '0,20 10,30 20,30',]),
                          ('C', ['60,70 70,60 70,40']),
                          ('c', ['0,-20 -10,-30 -20,-30']),
                          ('z', []),
                          ('m', ['0,10']),
                          ('v', ['40'])])

    def test_indent_box(self):
        box = _IndentedBox(padding=4, max_column=80)
        for w in self.src2.split():
            box.append_words(' ' + w)

        self.maxDiff = None
        self.assertEqual(box.text, '''\
    M 621.233134,535.81687 C 446.824765,508.269704 266.375834,530.368135
    151.857303,593.298337 37.338772,656.228539 3.220491,752.039044
    63.11033,842.516412 123.000168,932.99378 269.330818,1006.705854
    443.739188,1034.25302 618.147557,1061.800186 798.596488,1039.701755
    913.115019,976.771553 973.631197,943.516714 1014.07925,898.892637
    1026.669807,851.492898''')

    def test_indent_box_with_pd(self):
        box = _IndentedBox(padding=4, max_column=80)
        for fn, data in _PathDataViewer(self.pd2):
            box.append_words(fn + ' ')
            dbox = _IndentedBox(padding=4+2, max_column=80)
            for w in data:
                dbox.append_words('    ' + w)
            box.append_box(dbox)
            box.feed_line()

        self.maxDiff = None
        self.assertEqual(box.text, '''\
    M 621.233134,535.81687
    C 446.824765,508.269704 266.375834,530.368135 151.857303,593.298337
      37.338772,656.228539 3.220491,752.039044 63.11033,842.516412
      123.000168,932.99378 269.330818,1006.705854 443.739188,1034.25302
      618.147557,1061.800186 798.596488,1039.701755 913.115019,976.771553
      973.631197,943.516714 1014.07925,898.892637 1026.669807,851.492898''')

    def test_indent_box_with_pd2(self):
        precision(0)
        box = _IndentedBox(padding=4, max_column=80)
        for fn, data in _PathDataViewer(self.pd2):
            box.append_words(fn + ' ')
            dbox = _IndentedBox(padding=4+2, max_column=80)
            for w in data:
                dbox.append_words('    ' + w)
            box.append_box(dbox)
            box.feed_line()

        self.maxDiff = None
        self.assertEqual(box.text, '''\
    M 621,536
    C 447,508 266,530 152,593    37,656 3,752 63,843
      123,933 269,1007 444,1034    618,1062 799,1040 913,977
      974,944 1014,899 1027,851''')

    def test_view_transform(self):
        precision(0)
        src = 'translate(40.0,40.00009) rotate(60) translate(-40, -40)'
        ts = P.transforms(src)
        box = _IndentedBox(padding=4, max_column=80)
        for t in ts:
            box.append_words(str(t))
            box.feed_line()

        self.assertEqual(box.leading_stripped,
                         '''translate(40, 40)
    rotate(60)
    translate(-40, -40)''')
            

if __name__ == '__main__':
    unittest.main()
