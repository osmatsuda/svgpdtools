import unittest, pathlib, math
import xml.etree.ElementTree as ET

import svgpdtools as PD


class TestPDTransforms(unittest.TestCase):
    def test_tranform_inverse(self):
        t = PD.Transform.translate(-10, -20) * PD.Transform.rotate(30) * PD.Transform.scale(.5) * PD.Transform.translate(10,20)
        t_inv = t.inversed()
        self.assertTrue(is_identity(t*t_inv))
        self.assertTrue(is_identity(t_inv*t))

        p = PD.Point(100, 200)
        p_ = p.transformed(t).transformed(t_inv)
        self.assertEqual(p, p_)
        
    @unittest.skip('test_pd_transforms.svg')
    def test_make_test_path_svg(self):
        make_test_path_svg()


def is_identity(t: PD.Transform) -> bool:
    return all([
        math.isclose(t.a, 1),
        math.isclose(t.b, 0, abs_tol=1e-7),
        math.isclose(t.c, 0, abs_tol=1e-7),
        math.isclose(t.d, 1),
        math.isclose(t.e, 0, abs_tol=1e-7),
        math.isclose(t.f, 0, abs_tol=1e-7),
    ])
    
def make_test_path_svg():
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    curdir = pathlib.Path(__file__).parent

    root = ET.parse(curdir / 'test_pd_transforms_src.svg').getroot()
    PD.precision(4)
    _make_row_1(root)
    _make_row_2(root)
    _make_row_3(root)
    _make_row_4(root)
    _make_row_5(root)
    _make_row_6(root)

    _tree = ET.ElementTree(root)
    _tree.write(curdir / 'images/test_pd_transforms.svg', encoding='unicode')

def _make_row_1(root):
    B1 = _g(root, 'B1')
    for path in _g_paths(root, 'A1'):
        pd = PD.pathdata_from_string(path.get('d'))
        pd.absolutize()
        _append_path(B1, path, pd)
        
    D1 = _g(root, 'D1')
    for path in _g_paths(root, 'A1'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = PD.Transform.rotate(60, 40, 40)
        pd.transform(t, noexception=True)
        _append_path(D1, path, pd)
        
    E1 = _g(root, 'E1')
    for path in _g_paths(root, 'A1'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = PD.Transform.rotate(-90, 40, 40)
        pd.transform(t, noexception=True)
        _append_path(E1, path, pd)
        
    F1 = _g(root, 'F1')
    for path in _g_paths(root, 'A1'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = PD.Transform.rotate(180, 40, 40)
        pd.transform(t, noexception=True)
        _append_path(F1, path, pd)

def _make_row_2(root):
    toc = PD.Transform.translate(-40,-40)
    _toc = PD.Transform.translate(40,40)

    B2 = _g(root, 'B2')
    for path in _g_paths(root, 'A1'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = _toc * PD.Transform.scale(-1,1) * toc
        pd.transform(t, noexception=True)
        _append_path(B2, path, pd)

    D2 = _g(root, 'D2')
    for path in _g_paths(root, 'A1'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = _toc * PD.Transform.scale(.8,-.8) * toc
        pd.transform(t, noexception=True)
        _append_path(D2, path, pd)

    E2 = _g(root, 'E2')
    for path in _g_paths(root, 'A1'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = _toc * PD.Transform.rotate(60) * PD.Transform.scale(.8) * toc
        pd.transform(t, noexception=True)
        _append_path(E2, path, pd)

def _make_row_3(root):
    toc = PD.Transform.translate(-40,-40)
    _toc = PD.Transform.translate(40,40)

    B3 = _g(root, 'B3')
    for path in _g_paths(root, 'A3'):
        pd = PD.pathdata_from_string(path.get('d'))
        pd.absolutize()
        _append_path(B3, path, pd)

    D3 = _g(root, 'D3')
    for path in _g_paths(root, 'A3'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = PD.Transform.rotate(120, 40, 40)
        pd.transform(t, noexception=True)
        _append_path(D3, path, pd)

    E3 = _g(root, 'E3')
    for path in _g_paths(root, 'A3'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = PD.Transform.rotate(180, 40, 40)
        pd.transform(t, noexception=True)
        _append_path(E3, path, pd)

    F3 = _g(root, 'F3')
    for path in _g_paths(root, 'A1'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = _toc * PD.Transform.skewX(20) * toc
        pd.transform(t, noexception=True)
        _append_path(F3, path, pd)
        
def _make_row_4(root):
    toc = PD.Transform.translate(-40,-40)
    _toc = PD.Transform.translate(40,40)

    B4 = _g(root, 'B4')
    for path in _g_paths(root, 'A3'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = _toc * PD.Transform.scale(-1,1) * toc
        pd.transform(t, noexception=True)
        _append_path(B4, path, pd)

    D4 = _g(root, 'D4')
    for path in _g_paths(root, 'A3'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = _toc * PD.Transform.scale(.8,-.8) * toc
        pd.transform(t, noexception=True)
        _append_path(D4, path, pd)

    F4 = _g(root, 'F4')
    for path in _g_paths(root, 'A5'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = _toc * PD.Transform.skewY(20) * toc
        pd.transform(t, noexception=True)
        _append_path(F4, path, pd)
        
def _make_row_5(root):
    toc = PD.Transform.translate(-40,-40)
    _toc = PD.Transform.translate(40,40)

    B5 = _g(root, 'B5')
    for path in _g_paths(root, 'A5'):
        pd = PD.pathdata_from_string(path.get('d'))
        pd.absolutize()
        _append_path(B5, path, pd)

    D5 = _g(root, 'D5')
    for path in _g_paths(root, 'A5'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = _toc * PD.Transform.rotate(-60) * toc
        pd.transform(t, noexception=True)
        _append_path(D5, path, pd)

    E5 = _g(root, 'E5')
    for path in _g_paths(root, 'A5'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = _toc * PD.Transform.rotate(-90) * toc
        pd.transform(t, noexception=True)
        _append_path(E5, path, pd)

def _make_row_6(root):
    toc = PD.Transform.translate(-40,-40)
    _toc = PD.Transform.translate(40,40)

    B6 = _g(root, 'B6')
    for path in _g_paths(root, 'A5'):
        pd = PD.pathdata_from_string(path.get('d'))
        t = _toc * PD.Transform.scale(-.8,-.8) * toc
        pd.transform(t, noexception=True)
        _append_path(B6, path, pd)

    C6 = _g(root, 'C6')
    for path in _g_paths(root, 'A1'):
        pd = PD.pathdata_from_string(path.get('d'))
        pd.normalize(collapse_hv_lineto=True, repr_relative=True)
        _append_path(C6, path, pd)

    D6 = _g(root, 'D6')
    for path in _g_paths(root, 'A3'):
        pd = PD.pathdata_from_string(path.get('d'))
        pd.normalize(allow_implicit_lineto=True)
        _append_path(D6, path, pd)

    E6 = _g(root, 'E6')
    for path in _g_paths(root, 'A5'):
        pd = PD.pathdata_from_string(path.get('d'))
        pd.normalize(repr_relative=True)
        _append_path(E6, path, pd)

    F6 = _g(root, 'F6')
    for path in _g_paths(root, 'A3'):
        pd = PD.pathdata_from_string(path.get('d'))
        pd.normalize(collapse_elliptical_arc=True, allow_implicit_lineto=True)
        t = _toc * PD.Transform.skewY(-15) * PD.Transform.skewX(-15) * toc
        pd.transform(t)
        _append_path(F6, path, pd)

        
def _append_path(container, src_path, pd):
    _path = ET.fromstring(ET.tostring(src_path, encoding='unicode'))
    _path.set('d', str(pd))
    container.append(_path)

def _g(root, gid):
    return root.find(f'./{{*}}g[@id="{gid}"]')
    
def _g_paths(root, gid):
    return root.iterfind(f'./{{*}}g[@id="{gid}"]/{{*}}path')

if __name__ == '__main__':
    unittest.main()
