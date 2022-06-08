from __future__ import annotations
from collections import UserList

from .command import Command, Moveto, Lineto, Close, HorizontalAndVerticalLineto, EllipticalArc
from .transform import Transform


class PathData(UserList[Command]):
    def __init__(self, cmds: list[Command] = []) -> None:
        self._absolutized = False
        super().__init__(cmds)

    def __repr__(self) -> str:
        r = ''
        for cmd in self.data:
            r += f' {cmd}'
        return r[1:]

    def append(self, cmd: Command) -> None:
        if self.data:
            cmd.start_point = self.data[-1].end_point.clone()

            if isinstance(cmd, Close):
                for i in range(len(self.data), 0, -1):
                    prev_cmd = self.data[i-1]
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

    def transform(self, t: Transform, *, warning=True, collapse_elliptical_arc=False) -> None:
        if not self._absolutized:
            self.absolutize(called_internally=True)

        if not warning:
            for i in range(len(self.data)):
                cmd = self.data[i]
                if isinstance(cmd, HorizontalAndVerticalLineto):
                    self.data[i] = cmd.converted_to_lineto()
                elif isinstance(cmd, EllipticalArc) and collapse_elliptical_arc:
                    self.data[i] = cmd.converted_to_curves()

                self.data[i].transform(t)
        else:
            transformed = []
            for i in range(len(self.data)):
                cmd = self.data[i]
                if (isinstance(cmd, HorizontalAndVerticalLineto) or
                    isinstance(cmd, EllipticalArc)):
                    warning = 'The pathdata includes `'
                    if cmd.fn.lower() == 'h': warning += 'horizontal_lineto'
                    elif cmd.fn.lower() == 'v': warning += 'vertical_lineto'
                    elif cmd.fn.lower() == 'a': warning += 'elliptical_arc'
                    warning += f'`, {cmd.fn}, command.'
                    warning += '''
Command `horizontal_lineto`, `vertical_lineto`, or `elliptical_arc` will be converted to `lineto` or `curveto` before transforming.
If it's OK, you can continue to transform by the followings:
    pathdata.transform(t, warning=False)
      # `horizontal_lineto` and `vertical_lineto` are converted to `lineto`
    pathdata.transform(t, warning=False, collapse_elliptical_arc=True)
      # `elliptical_arc` is also converted to `curveto`'''
                    raise Exception(warning)
                else:
                    transformed.append(cmd.transformed(t))

            self.data = transformed

    def absolutize(self, *, called_internally=False) -> None:
        self._absolutized = True

        if not self.data: return

        curr_p = self.data[0].start_point
        for cmd in self.data:
            curr_p = cmd.absolutize(curr_p, called_internally=called_internally)

    def normalize(self, *,
                  repr_relative=False,
                  collapse_hv_lineto=False,
                  collapse_elliptical_arc=False,
                  allow_implicit_lineto=False,
                  ) -> None:
        
        if not self._absolutized:
            self.absolutize()

        if not self.data: return

        if not allow_implicit_lineto:
            cmds = _collapse_implicit_lineto(self.data[0])
        else:
            cmds = [self.data[0]]

        for i in range(1, len(self.data)):
            prev_cmd = cmds[-1]
            cmd = self.data[i]
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


def _collapse_implicit_lineto(moveto: Command) -> list[Command]:
    assert isinstance(moveto, Moveto)
    
    if len(moveto.data) < 2:
        return [moveto]

    lineto = Lineto('L', moveto.data[1:])
    lineto.start_point = moveto.start_point
    moveto.data = moveto.data[0:1]
    return [moveto, lineto]
