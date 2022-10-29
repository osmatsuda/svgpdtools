from __future__ import annotations
import argparse, pathlib, weakref, errno, sys, traceback, re
import xml.sax as SAX
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import AttributesImpl, Locator
from xml.sax.saxutils import XMLGenerator
from dataclasses import dataclass, field
from collections.abc import Iterator
from typing import Any, Protocol, Optional, Union, TextIO

from svgpdtools import PathData, Transform, precision
import svgpdtools.parser as myparser
from svgpdtools.pathdata import temporary_repr_relative, PDTransformFailed
from svgpdtools.command import Command, Moveto, Lineto, Curveto, HorizontalAndVerticalLineto,\
    EllipticalArc, EllipticalArcItem, Close
from svgpdtools.utils import number_repr


def _arg_parses() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='svgpdtools',
        usage='%(prog)s <command> [options] [arguments]',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''\
Available commands:
  transform
  normalize
  view''',
        add_help=False,
        exit_on_error=False,
    )

    general = parser.add_argument_group('General Options')
    general.add_argument(
        '-h', '--help',
        help='Show this help message.',
        action='store_true'
    )
    general.add_argument(
        '-f', '--file',
        help='SVG file to load. If not provided, read from stdin.',
        metavar='<file>',
        type=pathlib.Path,
    )
    general.add_argument(
        '-p', '--precision',
        help='Set the max lenght of fractional part of the number. (default: %(default)d)',
        type=int,
        metavar='N',
        default=6
    )
    general.add_argument(
        '-i', '--index',
        help='Set indexes of the paths which you want to manipulate. If not provided, all paths are objects.',
        type=int,
        metavar='N1 N2',
        nargs='*',
        default=[-1],
    )
    coord_repr_type = general.add_mutually_exclusive_group()
    coord_repr_type.add_argument(
        '-r', '--repr-relative',
        action='store_true',
        help='Use representing relative coordinates. Not allowed with “-a/--repr-absolute”.',
    )
    coord_repr_type.add_argument(
        '-a', '--repr-absolute',
        action='store_true',
        help='Use representing absolute coordinates. Not allowed with “-r/--repr-relative”.',
    )

    transform = parser.add_argument_group(
        'Command “transform”',
        '''\
Apply transform functions to the pathdata.
usage: svgpdtools transform [options] [--] "<transform-list>"'''
    )
    transform.add_argument(
        'transform',
        type=str,
        metavar='<transform-list>',
        nargs='?',
        default='',
        help='Syntax of <transform-list> is the same as the SVG’s transform attribute.',
    )

    normalize = parser.add_argument_group(
        'Command “normalize”',
        '''\
Convert pathdata to the following representations:
- Using absolute coordinates
- Merging continuous commands into one command
- Splitting a implict lineto command into a moveto and a lineto'''
    )
    normalize.add_argument(
        '--collapse-transform-attribute',
        action='store_true',
        help='If the path-element has a transform attribute, apply that transformation to the coordinates and remove that attribute.',
    )
    normalize.add_argument(
        '--allow-implicit-lineto',
        action='store_true',
        help='Convert a moveto and following lineto commands into one moveto command.',
    )

    common_to_trns_norm = parser.add_argument_group(
        'Common to “transform” and “normalize”'
    )
    common_to_trns_norm.add_argument(
        '--collapse-elliptical-arc',
        action='store_true',
        help='Convert a elliptical-arc command to a curveto command.',
    )
    common_to_trns_norm.add_argument(
        '--collapse-hv-lineto',
        action='store_true',
        help='Convert a horizontal- or vertical-lineto command to a lineto command.',
    )

    view = parser.add_argument_group(
        'Command “view”',
        'Search path-elements from the input, and print each path-element nicely formatted.',
    )
    
    return parser


def _head_tail(lst: list[str]) -> tuple[str, list[str]]:
    if len(lst) == 0:
        return '', []
    if lst[0].startswith('-'):
        return '', lst
    return lst[0], lst[1:]

def main(test_args: list[str]=[]) -> None:
    args_parser = _arg_parses()
    show_help = True
    exit_code = 2
    try:
        if test_args:
            show_help = False
            cmd_name, rest_args = _head_tail(test_args)
        else:
            cmd_name, rest_args = _head_tail(sys.argv[1:])
            
        args: Any = args_parser.parse_args(rest_args, namespace=_Args())
            
        if not args.help:
            command(cmd_name, args)
            show_help = False
            exit_code = 0
        elif not show_help:
            show_help = True
            exit_code = 0

    except SAX.SAXReaderNotAvailable:
        print('No XML parsers available.\n', file=sys.stderr)

    except FileNotFoundError as e:
        print(f'File not found: {e.filename}\n', file=sys.stderr)

    except _UnknownCommand as e:
        if e.name:
            print(f'Unknown command: {e.name}\n', file=sys.stderr)
        else:
            print('Command name required\n', file=sys.stderr)

    except argparse.ArgumentError as e:
        if cmd_name == 'transform' and \
           re.search(r'\b(translate|scale|matrix|rotate|skewX|skewY)\b', e.message):
            print(f'ArgumentError: you can insert a pseudo-argument "--" before the <transform-list>\n', file=sys.stderr)
        else:
            print(f'ArgumentError: {e}\n', file=sys.stderr)
        exit_code = 1

    except PDTransformFailed as e:
        print(e.message, file=sys.stderr)
        
    except:
        traceback.print_exc()
        show_help = False

    finally:
        if show_help:
            if exit_code > 0:
                args_parser.print_help(sys.stderr)
            else:
                args_parser.print_help()
        if exit_code > 0:
            sys.exit(exit_code)


class _UnknownCommand(Exception):
    def __init__(self, name: str) -> None:
        self.name = name

class _ArgsProto(Protocol):
    help: bool
    file: Optional[pathlib.Path]
    precision: int
    index: list[int]
    repr_relative: bool
    repr_absolute: bool
    transform: str
    collapse_transform_attribute: bool
    collapse_elliptical_arc: bool
    collapse_hv_lineto: bool
    allow_implicit_lineto: bool

class _Args: pass


class _Handler(Protocol):
    delegate: weakref.ProxyType
    def startElement(self, name: str, attrs: AttributesImpl) -> None: ...

class _ParserDelegate:
    def __init__(self, handler: _Handler) -> None:
        handler.delegate = weakref.proxy(self)
        self._parser = make_parser()
        self._parser.setContentHandler(handler)

    def parse(self, src: Union[TextIO, pathlib.Path]) -> None:
        self._parser.parse(src)

    @property
    def line_number(self) -> int:
        if isinstance(self._parser, Locator):
            return self._parser.getLineNumber()
        return -1


def command(name: str, args: _ArgsProto) -> None:
    input: Union[TextIO, pathlib.Path]
    if args.file is not None:
        if not args.file.is_file():
            raise FileNotFoundError(errno.ENOENT, '', str(args.file))
        input = args.file
    else:
        input = sys.stdin

    if any([n < 0 for n in args.index]):
        args.index = []
        
    precision(args.precision)
    
    handler: _Handler
    if name == 'view':
        handler = PathViewHandler(
            target_indexes = args.index,
            repr_relative = args.repr_relative,
            repr_absolute = args.repr_absolute,
        )

    elif name == 'normalize':
        handler = PathNormalizeHandler(
            target_indexes = args.index,
            repr_relative = args.repr_relative,
            collapse_hv_lineto = args.collapse_hv_lineto,
            collapse_elliptical_arc = args.collapse_elliptical_arc,
            collapse_transform_attribute = args.collapse_transform_attribute,
            allow_implicit_lineto = args.allow_implicit_lineto,
        )
        
    elif name == 'transform':
        transform = Transform.concat(myparser.transforms(args.transform.strip('\'"')))
        handler = PathTransformHandler(
            target_indexes = args.index,
            transform = transform,
            repr_relative = args.repr_relative,
            repr_absolute = args.repr_absolute,
            collapse_hv_lineto = args.collapse_hv_lineto,
            collapse_elliptical_arc = args.collapse_elliptical_arc,
        )

    else:
        raise _UnknownCommand(name)
    
    parser = _ParserDelegate(handler)
    parser.parse(input)


class PathTransformHandler(XMLGenerator):
    def __init__(self, *,
                 target_indexes: list[int],
                 transform: Transform,
                 repr_relative: bool,
                 repr_absolute: bool,
                 collapse_hv_lineto: bool,
                 collapse_elliptical_arc: bool) -> None:
        self.transform = transform
        self.repr_relative = repr_relative
        self.repr_absolute = repr_absolute
        self.collapse_hv_lineto = collapse_hv_lineto
        self.collapse_elliptical_arc = collapse_elliptical_arc
        
        self.delegate = None
        
        self.target_indexes = target_indexes
        self.index = 0
        super().__init__(sys.stdout, encoding='utf-8', short_empty_elements=True)
        
    def startElement(self, name: str, attrs: AttributesImpl) -> None:
        if name != 'path':
            super().startElement(name, attrs)
            return

        index = self.index
        self.index += 1
        if self.target_indexes and index not in self.target_indexes:
            super().startElement(name, attrs)
            return

        _attrs = {}
        transforms = [self.transform]
        for k in attrs.keys():
            if k == 'd':
                pd = myparser.pathdata(attrs[k])
            elif k == 'transform':
                transforms.extend(myparser.transforms(attrs[k]))
            else:
                _attrs[k] = attrs[k]

        pd.transform(
            Transform.concat(transforms),
            collapse_elliptical_arc=self.collapse_elliptical_arc,
            collapse_hv_lineto=self.collapse_hv_lineto,
        )

        if self.repr_absolute:
            pd.absolutize()
        with temporary_repr_relative(self.repr_relative):
            pd_str = str(pd)

        _attrs['d'] = pd_str
        super().startElement(name, AttributesImpl(_attrs))

    def endDocument(self):
        sys.stdout.write('\n')


class PathNormalizeHandler(XMLGenerator):
    def __init__(self, *,
                 target_indexes: list[int],
                 repr_relative: bool,
                 collapse_transform_attribute: bool,
                 collapse_elliptical_arc: bool,
                 collapse_hv_lineto: bool,
                 allow_implicit_lineto: bool) -> None:
        self.repr_relative = repr_relative
        self.collapse_transform_attribute = collapse_transform_attribute
        self.collapse_hv_lineto = collapse_hv_lineto
        self.collapse_elliptical_arc = collapse_elliptical_arc
        self.allow_implicit_lineto = allow_implicit_lineto

        self.delegate = None

        self.target_indexes = target_indexes
        self.index = 0
        super().__init__(sys.stdout, encoding='utf-8', short_empty_elements=True)
        
    def startElement(self, name: str, attrs: AttributesImpl) -> None:
        if name != 'path':
            super().startElement(name, attrs)
            return

        index = self.index
        self.index += 1
        if self.target_indexes and index not in self.target_indexes:
            super().startElement(name, attrs)
            return
        
        _attrs = {}
        transforms = []
        for k in attrs.keys():
            if k == 'd':
                pd = myparser.pathdata(attrs[k])
            elif k == 'transform':
                transforms = myparser.transforms(attrs[k])
            else:
                _attrs[k] = attrs[k]

        if transforms:
            if self.collapse_transform_attribute:
                pd.transform(
                    Transform.concat(transforms),
                    collapse_elliptical_arc=self.collapse_elliptical_arc,
                    collapse_hv_lineto=self.collapse_hv_lineto,
                )
            else:
                _attrs['transform'] = ' '.join([str(t) for t in transforms])

        pd.normalize(
            repr_relative=self.repr_relative,
            collapse_hv_lineto=self.collapse_hv_lineto,
            collapse_elliptical_arc=self.collapse_elliptical_arc,
            allow_implicit_lineto=self.allow_implicit_lineto,
        )
        _attrs['d'] = str(pd)
        super().startElement(name, AttributesImpl(_attrs))

    def endDocument(self):
        sys.stdout.write('\n')


class PathViewHandler(ContentHandler):
    def __init__(self, *,
                 target_indexes: list[int],
                 repr_relative: bool,
                 repr_absolute: bool,) -> None:
        self.repr_relative = repr_relative
        self.repr_absolute = repr_absolute
        
        self.delegate = None

        self.target_indexes = target_indexes
        self.index = 0

        from mako.template import Template
        self.template = Template(text='''\
%if index:
@${index}
%endif
<path
%if attrs:
    ${attrs}
%endif
%if transform:
    transform="${transform}"
%endif
    d="${d}"/>''')

        import subprocess
        tput_result = subprocess.run(['tput', 'cols'], capture_output=True, text=True)
        if tput_result.returncode == 0:
            self.max_column = max(int(tput_result.stdout), 60)
        else:
            self.max_column = 80
        
    def startElement(self, name: str, attrs: AttributesImpl) -> None:
        if name != 'path':
            return

        index = self.index
        self.index += 1
        if self.target_indexes and index not in self.target_indexes:
            return

        _attrs = {}
        others = []
        for k in attrs.keys():
            if k == 'd':
                _attrs['d'] = self._boxed_pd(attrs[k])
            elif k == 'transform':
                _attrs[k] = self._boxed_transforms(attrs[k])
            else:
                others.append(f'{k}="{attrs[k]}"')

        if others:
            _attrs['attrs'] = self._boxed_attrs(others)

        if self.delegate and (ln := self.delegate.line_number) and ln > 0:
            _attrs['line_number'] = ln

        _attrs['index'] = str(index)
        print(self.template.render(**_attrs))

    def _boxed_attrs(self, attrs: list[str]) -> str:
        box = _IndentedBox(padding=4, max_column=self.max_column)
        for attr in attrs:
            box.append_words(' ' + attr)
        return box.leading_stripped

    def _boxed_transforms(self, transform: str) -> str:
        box = _IndentedBox(padding=15, max_column=self.max_column)
        for t in myparser.transforms(transform):
            box.append_words(str(t))
            box.feed_line()
        return box.leading_stripped

    def _boxed_pd(self, d: str) -> str:
        box = _IndentedBox(padding=7, max_column=self.max_column)
        pd = myparser.pathdata(d)
        if self.repr_absolute:
            pd.absolutize()

        with temporary_repr_relative(self.repr_relative):
            for fn, data in  _PathDataViewer(pd):
                box.append_words(fn + ' ')
                dbox = _IndentedBox(padding=9, max_column=self.max_column)
                for w in data:
                    dbox.append_words('    ' + w)
                box.append_box(dbox)
                box.feed_line()
                
        return box.leading_stripped


_PathDataViewItem = tuple[str, list[str]]

class _PathDataViewer(Iterator[_PathDataViewItem]):
    def __init__(self, pd: PathData) -> None:
        self.pd = pd
        self._i = -1

    def __iter__(self) -> _PathDataViewer:
        return self

    def __next__(self) -> _PathDataViewItem:
        self._i += 1
        if self._i >= len(self.pd):
            raise StopIteration
        cmd = self.pd[self._i]
        return _cmd_data_views(cmd)


def _cmd_data_views(cmd: Command) -> _PathDataViewItem:
    if isinstance(cmd, Close):
        return cmd.fn, []

    if isinstance(cmd, HorizontalAndVerticalLineto):
        return cmd.fn, [number_repr(n) for n in cmd.data]

    if isinstance(cmd, EllipticalArc):
        return cmd.fn, [item.repr(cmd.fn.isupper()) for item in cmd.data]

    fn = cmd.fn
    coords = [str(p) for p in cmd.data]

    step = 1
    if fn in 'qQ': step = 2
    elif fn in 'cC': step = 3
    if step > 1:
        _coords = []
        for i in range(0, len(coords), step):
            _coords.append(' '.join(coords[i:i+step]))
        return fn, _coords
    
    return fn, coords


@dataclass
class _IndentedBox:
    padding: int
    max_column: int
    _current_column: int = field(init=False)
    _text: str = field(init=False)
    def __post_init__(self):
        self._current_column = self.padding
        self._text = ' '*self.padding

    def append_words(self, words: str) -> None:
        succ_new_line = words.endswith('\n')
        if succ_new_line:
            words = words[:-1]
            if words.endswith('\r'):
                words = words[:-1]
        
        if self._text == ' '*self.padding or\
           self._text.endswith('\n' + ' '*self.padding):
            words = words.lstrip()
            
        words_length = len(words)
        if self._current_column + words_length > self.max_column:
            self._text += '\n' + ' '*self.padding + words.lstrip()
            self._current_column = self.padding + words_length
        else:
            self._text += words
            self._current_column += words_length

        if succ_new_line:
            self._text += '\n' + ' '*self.padding
            self._current_column = self.padding

    def feed_line(self, n: int=1) -> None:
        self._text = self._text.rstrip(' \t')
        self._text += '\n'*n + ' '*self.padding

    def append_box(self, other: _IndentedBox, next_line=False) -> None:
        if next_line:
            self.feed_line()
        self._text += other.leading_stripped
        
    @property
    def text(self) -> str:
        return self._text.rstrip()
    @property
    def leading_stripped(self) -> str:
        return self.text.lstrip()
    

if __name__ == '__main__':
    main()

