# SVG PathData Tools

The `svgpdtools` module defines utilities to manipulate pathdata (value of `d` attribute) of a SVG `path`-element. Also there is a command line interface.

## Install

```
% pip install svgpdtools
```

## Examples

``` python
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

In the CLI to handle SVG this module uses ‘xml.sax.make_parser’ and ‘xml.sax.saxutils.XMLGenerator’. So you should not parse untrusted data.

```
% svgpdtools normalize --collapse-transform-attribute -f infile.svg |\
      svgpdtools transform -p 3 "translate(25,25)" > outfile.svg
```

## Module contents

### svgpdtools.precision(value: int) -> None

### svgpdtools.pathdata_from_string(src: str) -> PathData

### svgpdtools.transform_from_string(src: str) -> Transform

### class svgpdtools.PathData

### class svgpdtools.Transform

## Future considerations

- Change the PathData object to a immutable object.
- Implement the editing functions that common bezier path tools have.
