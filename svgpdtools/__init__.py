from .transform import Transform
from .pathdata import PathData
import svgpdtools.utils as utils
import svgpdtools.parser as parser


__version__ = "0.1.1"


def precision(value: int) -> None:
    """
    Set the max length of fractional part of a real number. The default
    value is 6. Each coordinate of the pathdata is calculated as a Python
    float value, and formatted with that length when shown.
    """
    utils.precision(value)

def pathdata_from_string(src: str) -> PathData:
    """
    Convert a pathdata string to a `svgpdtools.PathData` object. A path-
    data string is a value of the `d` property of the SVG-path element.
    """
    return parser.pathdata(src)

def transform_from_string(src: str) -> Transform:
    """
    Convert a string representation of SVG transfom functions to a
    `svgpdtools.Transform` object. The syntax of transform functions are the
    same as the SVG `transform` attribute.
    """
    return Transform.concat(parser.transforms(src))
