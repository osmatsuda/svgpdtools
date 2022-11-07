# SVG PathData Tools

The `svgpdtools` module defines utilities to manipulate pathdata (value of `d` attribute) of a SVG `path`-element. Also there is a command line interface.

## Install

```
% pip install svgpdtools
```

## Examples

```python
import xml.etree.ElementTree as ET
import svgpdtools as PD

def apply_translates():
    PD.precision(3)
    tree = ET.parse('infile.svg')
    t_parent = PD.Transform.translate(25, 25)
    for path in tree.findall('.//{*}path'):
        pd = PD.pathdata_from_string(path.get('d'))
        t_child = path.get('transform', '')
        if t_child:
            path.set('transform', '')
        pd.transform(t_parent * PD.transform_from_string(t_child))
        path.set('d', str(pd))
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    tree.write('outfile.svg', encoding='utf-8')
```

Below is using CLI to get almost equivalent output as the above code.

With the CLI to handle SVG data, this module uses ‘xml.sax.make_parser’ and ‘xml.sax.saxutils.XMLGenerator’. So you should not parse untrusted data.

```
% svgpdtools normalize --collapse-transform-attribute -f infile.svg |\
      svgpdtools transform -p 3 "translate(25,25)" > outfile.svg
```

## Module contents

### svgpdtools.precision(value: int) -> None

Set the max length of fractional part of a real number. The default value is 6. Each coordinate of the pathdata is calculated as a Python float value, and formatted with that length when shown.

### svgpdtools.pathdata_from_string(src: str) -> PathData

Convert a pathdata string to a `svgpdtools.PathData` object. A pathdata string is a value of the `d` property of the SVG-path element.

### svgpdtools.transform_from_string(src: str) -> Transform

Convert a string representation of SVG transfom functions to a `svgpdtools.Transform` object. The syntax of transform functions are the same as the SVG `transform` attribute.

### class svgpdtools.PathData

UserList of `svgpdtools.Command` objects. This class has some methods which are major task of the `svgpdtools` module. `transform()`, `absolutize()`, and `normalize()`, those methods are destructive operations.

### class svgpdtools.Transform

This class represents a transform matrix, which is the same as the SVG's presentation attribute `transform`. Transform functions are provided as static functions. Each function's syntax is also same as the SVG's transform functions.

- Transform.matrix(a, b, c, d, e, f)
- Transform.translate(dx, dy)
- Transform.scale(sx, sy)
- Transform.rotate(deg, cx, cy)
- Transform.skewX(deg)
- Transform.skewY(deg)

For example, the current transformation matrix (CTM) is represent multiple functions in SVG:

```svg
<g transform="translate(10,10) rotate(45) translate(-10,-10)">
  ...
</g>
```

The above transformation of the SVGGElement is equivalent to the following:

```python
import svgpdtools.Transform as T
T1, T2, T3 = T.translate(10,10), T.rotate(45), T.translate(-10,-10)
ctm = T1 * T2 * T3
# or
ctm = T.concat([T1, T2, T3])
# or
ctm = T1.concatenated(T2, T3)
```

`svgpdtools.Transform()` is an identity matrix.

## Future considerations

- Change the PathData object to a immutable object.
- Implement editing functions that common bezier path tools have.
