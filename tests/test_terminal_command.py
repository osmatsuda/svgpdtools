import unittest, contextlib, io, pathlib

from svgpdtools import PathData, Transform, precision, pathdata_from_string, transform_from_string
from svgpdtools.terminal_command import _PathDataViewer, _IndentedBox, _arg_parses, _Args
import svgpdtools.parser as P
import svgpdtools.terminal_command as CMD


class TestCMDMain(unittest.TestCase):
    def setUp(self):
        self.stream = io.StringIO()
        self.curdir = pathlib.Path(__file__).parent
        self.test_svg = self.curdir / 'test_terminal_command.svg'
        self.maxDiff = None

    @unittest.skip('test_terminal_command.TestCMDMain.test_view')
    def test_view(self):
        wanted_file = self.curdir / 'test_terminal_command.TestCMDMain.test_view'
        with contextlib.redirect_stdout(self.stream):
            CMD.main(f'view -i 1 -a -f {self.test_svg.absolute()}'.split())
        with open(wanted_file) as wf:
            self.assertEqual(self.stream.getvalue(), wf.read())

    @unittest.skip('test_terminal_command.TestCMDMain.test_transform.svg')
    def test_transform(self):
        wanted_file = self.curdir / 'test_terminal_command.TestCMDMain.test_transform.svg'
        with contextlib.redirect_stdout(self.stream):
            CMD.main(f'transform -p 3 -i 1 --collapse-elliptical-arc -f {self.test_svg.absolute()} --'.split() + ['"translate(80,0)"'])
        with open(wanted_file) as wf:
            self.assertEqual(self.stream.getvalue(), wf.read())


class TestArgParser(unittest.TestCase):
    def setUp(self):
        self.parser = _arg_parses()
        
    def test_basic(self):
        test = ['-f', 'yama']
        args = self.parser.parse_args(test, namespace=_Args())
        self.assertEqual(args.file.name, 'yama')

    def test_argparse_indexes(self):
        test = ['-i', '1', '2', '-f', 'yama']
        args = self.parser.parse_args(test, namespace=_Args())
        self.assertEqual(args.index, [1, 2])
        self.assertEqual(args.file.name, 'yama')

    def test_argparse_transform(self):
        test = ['"scale(-1) translate(-10)"', '-f', 'yama', '-i', '1']
        args = self.parser.parse_args(test, namespace=_Args())
        self.assertEqual(args.transform, test[0])
        self.assertEqual(args.file.name, 'yama')
        self.assertEqual(args.index, [1])

    def test_argparse_transform2(self):
        test = ['-p', '3', '-i', '1', '2', '--', '"scale(-1) translate(-10)"']
        args = self.parser.parse_args(test, namespace=_Args())
        self.assertEqual(args.transform, '"scale(-1) translate(-10)"')
        self.assertEqual(args.precision, 3)
        self.assertEqual(args.index, [1, 2])
        
    def test_argparse_transform3(self):
        test = ['-i', '1', '2', '-p', '3', '"scale(-1) translate(-10)"', '-f', 'yama']
        args = self.parser.parse_args(test, namespace=_Args())
        self.assertEqual(args.transform, '"scale(-1) translate(-10)"')
        self.assertEqual(args.precision, 3)
        self.assertEqual(args.index, [1, 2])
        

class TestCMDMainArgParseError(unittest.TestCase):
    def setUp(self):
        self.stream = io.StringIO()
        
    def test_arg_errors(self):
        err_str = 'ArgumentError: argument -p/--precision: expected one argument\n\n'
        with contextlib.redirect_stdout(self.stream):
            CMD.main('view -i -p'.split())
        self.assertEqual(self.stream.getvalue(), err_str)

    def test_arg_errors_repr_type(self):
        err_str = 'ArgumentError: argument -r/--repr-relative: not allowed with argument -a/--repr-absolute\n\n'
        with contextlib.redirect_stdout(self.stream):
            CMD.main('view -a -r'.split())
        self.assertEqual(self.stream.getvalue(), err_str)

    def test_arg_errors_transform(self):
        err_str = 'ArgumentError: you can insert a pseudo-argument "--" before the <transform-list>\n\n'
        with contextlib.redirect_stdout(self.stream):
            CMD.main('transform -i 1 2'.split() + ['"scale(-1) translate(10)"'])
        self.assertEqual(self.stream.getvalue(), err_str)

    
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
        precision(6)
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
