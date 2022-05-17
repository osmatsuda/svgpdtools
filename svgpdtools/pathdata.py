from __future__ import annotations
from collections import UserList

from .command import Command, Moveto, Close, HorizontalAndVerticalLineto
from .transform import Transform


class PathData(UserList[Command]):
    def __init__(self, cmds: list[Command] = []):
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

    def transform(self, t: Transform) -> None:
        if not self._absolutized:
            self.absolutize(called_internally=True)

        for i in range(len(self.data)):
            cmd = self.data[i]
            if isinstance(cmd, HorizontalAndVerticalLineto):
                self.data[i] = cmd.converted_to_lineto()

            self.data[i].transform(t)

    def absolutize(self, *, called_internally=False) -> None:
        self._absolutized = True

        curr_p = self.data[0].start_point
        for cmd in self.data:
            curr_p = cmd.absolutize(curr_p, called_internally=called_internally)
        
