from .graphics import Point
from .transform import Transform
from .pathdata import PathData
import svgpdtools.utils
import svgpdtools.parser


__version__ = "0.0.1"


def precision(value: int) -> None:
    svgpdtools.utils.precision(value)

def pathdata_from_string(src: str) -> PathData:
    return svgpdtools.parser.pathdata(src)

def transform_from_string(src: str) -> Transform:
    return svgpdtools.parser.transform(src)
