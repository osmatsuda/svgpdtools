from .transform import Transform
from .pathdata import PathData
import svgpdtools.utils as utils
import svgpdtools.parser as parser


__version__ = "0.1.0"


def precision(value: int) -> None:
    """
    Set the max length of fractional part of a real number. The default
    value is 6. Each coordinate number of the pathdata is calculated as a
    Python float value, and formatted with that length.
    """
    utils.precision(value)

def pathdata_from_string(src: str) -> PathData:
    """
    Convert a path data string to a `svgpdtools.PathData` object. A path
    data string is a value of the `d` property of the SVG-path element.
    """
    return parser.pathdata(src)

def transform_from_string(src: str) -> Transform:
    """
    Convert a string representation of SVG transfom functions to a
    `svgpdtools.Transform` object. The syntax of transform functions are the
    same as the SVG `transform` attribute, differ from the CSS property.
    """
    return Transform.concat(parser.transforms(src))
