from importlib import *
from maya import cmds
from ysrig import core, ctrl_base
reload(core)
reload(ctrl_base)

class Ctrl(ctrl_base.CtrlBace):
    def setup(self):
        self.ctrl_shape_type = core.get_enum_attribute(self.meta_node, "ControllrShapeType")
        self.scale_uniformly = True

    def create(self):
        ctrls = [None] * (self.joint_count - 1)
        ctrl_spaces = [None] * (self.joint_count - 1)
        for i, name in enumerate(self.joint_names[:-1]):
            ctrl = core.EditCurve(name, self.ctrl_shape_type)
            self.scale_uniformly = ctrl.scale_uniformly

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
        core.auto_scale_chain_ctrls(self.ctrl_spaces, self.guide_world_matrices, 0.25, self.scale_uniformly)


class CtrlColor(ctrl_base.CtrlColorBase):
    def set_color(self, ctrls, side):
        if side == "L":
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.LEFT_SECOND_COLOR)

        elif side == "R":
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.RIGHT_SECOND_COLOR)

        else:
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.CENTER_SECOND_COLOR)