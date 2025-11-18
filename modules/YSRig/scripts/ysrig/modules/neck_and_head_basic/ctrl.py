from importlib import *
from maya import cmds
from ysrig import core, ctrl_base
reload(core)
reload(ctrl_base)

class Ctrl(ctrl_base.CtrlBace):
    def create(self):
        ctrls = [None] * (self.joint_count - 1)
        ctrl_spaces = [None] * (self.joint_count - 1)
        for i, name in enumerate(self.joint_names[:-1]):
            if name == self.joint_names[-2]:
                ctrl = core.EditCurve(name, "Head")

            else:
                ctrl = core.EditCurve(name, "Neck")

            ctrls[i] = ctrl.parent_node
            ctrl_spaces[i] = core.create_space(ctrls[i])
            core.create_hierarchy(
                self.grp,
                    ctrl_spaces[i], ":",
                        ctrls[i]
            )

        self.ctrls = ctrls
        self.ctrl_spaces = ctrl_spaces

    def set_space_transform(self):
        core.auto_scale_chain_ctrls(self.ctrl_spaces, self.guide_world_matrices, 1.75, True)


class CtrlColor(ctrl_base.CtrlColorBase):
    def set_color(self, ctrls, side):
        super().set_color(ctrls, side)

        if side == "L":
            core.set_ctrl_shape_color(ctrls[-1], core.LEFT_SECOND_COLOR)

        elif side == "R":
            core.set_ctrl_shape_color(ctrls[-1], core.RIGHT_SECOND_COLOR)

        else:
            core.set_ctrl_shape_color(ctrls[-1], core.CENTER_SECOND_COLOR)