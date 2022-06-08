from .graphics import Point
from .transform import Transform
from .pathdata import PathData
import svgpdtools.utils as utils
import svgpdtools.parser as parser


__version__ = "0.1.0"


def precision(value: int) -> None:
    utils.precision(value)

def pathdata_from_string(src: str) -> PathData:
    return parser.pathdata(src)

def transform_from_string(src: str) -> Transform:
    return Transform.concat(parser.transforms(src))
