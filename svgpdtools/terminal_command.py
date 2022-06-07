from __future__ import annotations
import argparse, pathlib, weakref, errno
import xml.sax as SAX
from xml.sax import parse, make_parser
from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import AttributesImpl, Locator
from xml.sax.saxutils import XMLGenerator
from dataclasses import dataclass, field
from collections.abc import Iterator
from typing import Any, Protocol

from svgpdtools import PathData, parser
from svgpdtools.command import Command, Moveto, Lineto, Curveto, HorizontalAndVerticalLineto,\
    EllipticalArc, EllipticalArcItem, Close
from svgpdtools.utils import number_repr


def _arg_parses() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='svgpdtools',
        usage='%(prog)s <command> [options]',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''\
Available commands:
  normalize
  view''',
        add_help=False,
    )
    parser.add_argument(
        'command',
        help=argparse.SUPPRESS,
        nargs='?',
        default=''
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

    normalize = parser.add_argument_group(
        'Command ‘normalize’',
        '''\
Convert pathdata to the following representations:
- Use absolute coordinates
- Merge continuous commands into one command
- Split a implict lineto command into a moveto and a lineto'''
    )
    normalize.add_argument(
        '--repr-relative',
        action='store_true',
        help='Use relative coordinates.'
    )
    normalize.add_argument(
        '--collapse-transform-attribute',
        action='store_true',
        help='If the path-element has a transform attribute, apply that transformation to the coordinates and remove that attribute.',
    )
    normalize.add_argument(
        '--collapse-elliptical-arc',
        action='store_true',
        help='Convert a elliptical-arc command to a curveto command.',
    )
    normalize.add_argument(
        '--collapse-hv-lineto',
        action='store_true',
        help='Convert a horizontal- or vertical-lineto command to a lineto command.',
    )
    normalize.add_argument(
        '--allow-implicit-lineto',
        action='store_true',
        help='Convert a moveto and following lineto commands into one moveto command.',
    )

    view = parser.add_argument_group(
        'Command ‘view’',
        'Search path-elements from the input, and print each path-element in pretty style.',
    )
    
    return parser


def main() -> None:
    args_parser = _arg_parses()
    try:
        args: Any = args_parser.parse_args(namespace=_Args())
        if args.help:
            args_parser.print_help()
            return

        cmd = globals().get(args.command)
        if callable(cmd):
            cmd(args)
        else:
            if args.command:
                print(f'Unknown command: {args.command}\n')
            args_parser.print_help()
            return

    except SAX.SAXReaderNotAvailable:
        print('No XML parsers available.\n')
        args_parser.print_help()

    except FileNotFoundError as e:
        print(f'File not found: {e.filename}\n')
        args_parser.print_help()
        
#    except Exception as e:
#        print(f'Error: {type(e)}: {e}')
#        args_parser.print_help()


class _ArgsProto(Protocol):
    help: bool
    file: pathlib.Path
    command: str
    precision: int
    repr_relative: bool
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

    def parse(self, src: pathlib.Path) -> None:
        self._parser.parse(src)

    @property
    def line_number(self) -> int:
        if isinstance(self._parser, Locator):
            return self._parser.getLineNumber()
        return -1


def normalize(args: _ArgsProto) -> None:
    """
    Normalize pathdata in the svg file and output to the stdout.
    """
    print(args.__dict__)


class PathNormalizeHandler(XMLGenerator):
    def startElement(self, name: str, attrs: AttributesImpl) -> None:
        if name != 'path':
            super().startElement(name, attrs)
            return

        _attrs = {}
        for k in attrs.keys():
            if k == 'd':
                pd = attrs[k]
                _attrs[k] = pd
            else:
                _attrs[k] = attrs[k]

        super().startElement(name, AttributesImpl(_attrs))


def view(args: _ArgsProto) -> None:
    """List up path-elements and pretty print."""
    if not args.file.is_file():
        raise FileNotFoundError(errno.ENOENT, '', str(args.file))

    handler = PathViewHandler()
    parser = _ParserDelegate(handler)
    parser.parse(args.file)


class PathViewHandler(ContentHandler):
    def __init__(self) -> None:
        self.delegate = None

        from mako.template import Template
        self.template = Template(text='''\
%if line_number:
@ ${line_number}
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

        print(self.template.render(**_attrs))

    def _boxed_attrs(self, attrs: list[str]) -> str:
        box = _IndentedBox(padding=4, max_column=self.max_column)
        for attr in attrs:
            box.append_words(attr)
        return box.text

    def _boxed_transforms(self, transform: str) -> str:
        box = _IndentedBox(padding=15, max_column=self.max_column)
        for t in parser.transforms(transform):
            box.append_words(str(t))
            box.feed_line()
        return box.leading_stripped

    def _boxed_pd(self, d: str) -> str:
        box = _IndentedBox(padding=7, max_column=self.max_column)
        for fn, data in  _PathDataViewer(parser.pathdata(d)):
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
        cmd = self.pd.data[self._i]
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

