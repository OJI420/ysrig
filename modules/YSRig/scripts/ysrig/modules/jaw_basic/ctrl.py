from importlib import *
from maya import cmds
from ysrig import core, ctrl_base
reload(core)
reload(ctrl_base)

class Ctrl(ctrl_base.CtrlBace):
    def create(self):
        ctrl = core.EditCurve(self.joint_names[0], "Jaw")
        ctrls = [ctrl.parent_node]
        ctrl_spaces = [core.create_space(ctrls[0])]
        core.create_hierarchy(
            self.grp,
                ctrl_spaces[0], ":",
                    ctrls[0]
        )

        self.ctrls = ctrls
        self.ctrl_spaces = ctrl_spaces

    def set_space_transform(self):
        core.auto_scale_chain_ctrls(self.ctrl_spaces, self.guide_world_matrices, 1, True)

class CtrlColor(ctrl_base.CtrlColorBase):
    def set_color(self, ctrls, side):
        core.set_ctrl_shape_color(ctrls[0], core.FACIAL_COLOR_1)