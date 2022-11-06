from __future__ import annotations
from collections import UserList
from typing import Literal

from .command import Command, Moveto, Lineto, Close, HorizontalAndVerticalLineto, EllipticalArc, \
    set_force_repr_relative
from .transform import Transform
from .graphics import TupledPoint


class PDTransformFailed(Exception):
    def __init__(self, pd: PathData, message: str) -> None:
        self.source = str(pd)
        self.message = message

# ISSUES:
#   - it may be bad idea to use UserList
#   - should be immutable data
class PathData(UserList[Command]):
    """
    UserList of `svgpdtools.Command` objects.
    This class has some methods which are major task of the `svgpdtools`.
    `transform`, `absolutize`, and `normalize`, those methods are
    destructive operations.
    """
    def __init__(self, cmds: list[Command] = []) -> None:
        self._absolutized = False

        super().__init__([])
        for cmd in cmds:
            self.append(cmd)

    def __repr__(self) -> str:
        r = ''
        for cmd in self:
            r += f' {cmd}'
        return r[1:]

    def append(self, cmd: Command) -> None:
        if self.data:
            cmd.start_point = self[-1].end_point.clone()

            if isinstance(cmd, Close):
                for i in range(len(self), 0, -1):
                    prev_cmd = self[i-1]
                    if isinstance(prev_cmd, Moveto):
                        cmd.end_point = prev_cmd.moveto_point.clone()
                        break
        else:
            if not isinstance(cmd, Moveto):
                raise Exception('The begining command should be a moveto command.')
            cmd.is_first_command = True

        if cmd.fn.islower():
            self._absolutized = False
            
        super().append(cmd)

    def transform(self, t: Transform, *,
                  noexception=False,
                  collapse_hv_lineto=False,
                  collapse_elliptical_arc=False) -> None:
        """
        Each point of a pathdata is transformed into another point by a
        `svgpdtools.Transform` object.

        It is almost the same manner of the `transform` attribute of the
        SVG. But when the transform contains rotation or skew commands,
        `horizontal/vertical lineto (H/h, V/v)` and `elliptical arc (A/a)`
        command drawings may not be transformed to the same drawings of the
        SVG graphical element with a transform attribute. So this method can
        convert those commands into `lineto (L/l)` and `curveto (C/c)`
        commands.
        By default, raises PDTransformFailed exception when meets that case.

        :param noexception: if True, convert H/h and V/v commands into
            L/l commands. But A/a commands are changed only their coords.
            (default False)
        :param collapse_hv_lineto: if True, convert only H/h and V/v
            commands into L/l commands. (default False)
        :param collapse_elliptical_arc: if True, convert only A/a commands
            into C/c commands. (default False)
        """
        if not self._absolutized:
            self.absolutize(called_internally=True)

        if noexception:
            for i in range(len(self.data)):
                cmd = self[i]
                if isinstance(cmd, HorizontalAndVerticalLineto):
                    self[i] = cmd.converted_to_lineto()
                elif isinstance(cmd, EllipticalArc) and collapse_elliptical_arc:
                    self[i] = cmd.converted_to_curves()

                self[i].transform(t)
        else:
            transformed = []
            for i in range(len(self)):
                cmd = self[i]
                failed = False
                if isinstance(cmd, HorizontalAndVerticalLineto):
                    if collapse_hv_lineto:
                        transformed.append(cmd.converted_to_lineto().transformed(t))
                    else:
                        failed = True
                elif isinstance(cmd, EllipticalArc):
                    if collapse_elliptical_arc:
                        transformed.append(cmd.converted_to_curves().transformed(t))
                    else:
                        failed = True
                else:
                    transformed.append(cmd.transformed(t))

                if failed:
                    errmsg = f'The pathdata includes `{cmd.fn}` ({cmd.fn_description}) command.'
                    errmsg += '''
A command `horizontal_lineto (H/h)`, `vertical_lineto (V/v)`, or
`elliptical_arc (A/a)` may as well be converted to `lineto (L/l)` or
`curveto (C/c)` before transforming.
You can continue to transform by the followings:
  - Convert H/h V/v into L/l:
    - pd.transform(t, noexception=True)
      - If there are A/a commands, they are transformed as-is.
    - pd.transform(t, collapse_hv_lineto=True)
      - If there are A/a commands, raise PDTransformFailed.
  - Convert A/a into C/c:
    - pd.transform(t, collapse_elliptical_arc=True)
  - Convert H/h, V/v into L/l and A/a into C/c:
    - pd.transform(t, noexception=True, collapse_elliptical_arc=True)
    - pd.transform(t, collapse_hv_lineto=True, collapse_elliptical_arc=True)'''
                    raise PDTransformFailed(self, errmsg)

            self.data = transformed

    def absolutize(self, *, called_internally=False) -> None:
        """
        Converts relative coordinates into absolute coordinates.
        """
        self._absolutized = True

        if not self.data: return

        curr_p = self[0].start_point
        for cmd in self:
            curr_p = cmd.absolutize(curr_p, called_internally=called_internally)

    def normalize(self, *,
                  repr_relative=False,
                  collapse_hv_lineto=False,
                  collapse_elliptical_arc=False,
                  allow_implicit_lineto=False,
                  ) -> None:
        """
        Normalize in this module means:

        - Use absolute coordinates
        - Use lineto command rather than implicit lineto command (M/m is
          followed by multiple pairs of coords)

        :param repr_relative: if True, convert into absolute coords, but
            show in relative coords. (default False)
        :param collapse_hv_lineto: if True, convert H/h, V/v commands into
            L/l commands. (default False)
        :param collapse_elliptical_arc: if True, convert A/a commands into
            C/c commands. (default False)
        :param allow_implicit_lineto: if True, keep implicit lineto
            commands. (default False)
        """
        
        if not self._absolutized:
            self.absolutize()

        if not self.data: return

        if not allow_implicit_lineto:
            cmds = _collapse_implicit_lineto(self[0])
        else:
            cmds = [self[0]]

        for i in range(1, len(self)):
            prev_cmd = cmds[-1]
            cmd = self[i]
            if collapse_elliptical_arc and isinstance(cmd, EllipticalArc):
                cmd = cmd.converted_to_curves()

            if collapse_hv_lineto and isinstance(cmd, HorizontalAndVerticalLineto):
                cmd = cmd.converted_to_lineto()

            if cmd.fn == 'M':
                if not allow_implicit_lineto:
                    cmds += _collapse_implicit_lineto(cmd)
                else:
                    cmds.append(cmd)

            elif cmd.fn == 'L':
                if ((allow_implicit_lineto and prev_cmd.fn == 'M') or
                    prev_cmd.fn == 'L'):
                    prev_cmd.data += cmd.data
                else:
                    cmds.append(cmd)

            elif cmd.fn == prev_cmd.fn:
                if cmd.fn in 'HVZ':
                    prev_cmd.data = cmd.data[-1:]
                else:
                    prev_cmd.data += cmd.data
                    
            else:
                if cmd.fn in 'HVZ':
                    cmd.data = cmd.data[-1:]
                    
                cmds.append(cmd)
            
        for cmd in cmds:
            cmd.repr_relative = repr_relative

        self.data = cmds

    def segmented_points(self) -> list[TupledPoint]:
        """
        Return list of Points. Each Point is segmentation point by commands,
        either explicit or implicit, and is shown as tuple `(x, y)`. All
        coordinates are absolute.
        """
        ps = self[0].segmented_points()
        last_cmd = Moveto
        for cmd in self.data[1:]:
            if isinstance(cmd, Moveto) or isinstance(cmd, Close) or isinstance(last_cmd, Moveto):
                ps.extend(cmd.segmented_points())
            else:
                ps.extend(cmd.segmented_points()[1:])
            last_cmd = type(cmd)
        return ps


def _collapse_implicit_lineto(moveto: Command) -> list[Command]:
    assert isinstance(moveto, Moveto)
    
    if len(moveto.data) < 2:
        return [moveto]

    lineto = Lineto('L', moveto.data[1:])
    lineto.start_point = moveto.start_point
    moveto.data = moveto.data[0:1]
    return [moveto, lineto]


class temporary_repr_relative:
    def __init__(self, repr_relative: bool) -> None:
        self.repr_relative = repr_relative
        self._old_value: bool
    
    def __enter__(self) -> None:
        self._old_value = set_force_repr_relative(self.repr_relative)

    def __exit__(self, *exc) -> Literal[False]:
        _ = set_force_repr_relative(self._old_value)
        return False
