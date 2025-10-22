from importlib import *
from maya import cmds
from ysrig import core, ctrl_base
reload(core)
reload(ctrl_base)

class Ctrl(ctrl_base.CtrlBace):
    def _create_grp(self):
        ctrl_grp = core.create_labeled_node("transform", core.get_controller_edit_group(), name=core.get_controller_edit_group())
        cmds.parent(ctrl_grp, core.get_root_group())
        super()._create_grp()

    def create(self):
        root_ctrl = core.EditCurve(self.joint_names[0], "Root")
        root_ctrl.set_scale(50)
        root_ctrl.set_shape_color(core.ROOT_MAIN_COLOR)
        offset_ctrl = core.EditCurve("Root_Offset", "Root_Offset")
        offset_ctrl.set_scale(50)
        offset_ctrl.set_shape_color(core.ROOT_SECOND_COLOR)
        offset_ctrl.reparent_shape(root_ctrl.parent_node)

        root_space = core.create_space(root_ctrl.parent_node)
        core.create_hierarchy(
            self.grp,
                root_space, ":",
                    root_ctrl.parent_node
        )

        self.ctrls = [root_ctrl.parent_node]
        self.ctrl_spaces = [root_space]

    def set_color(self):
        pass

    def set_space_transform(self):
        scale = core.decompose_matrix(self.guide_world_matrices[0])[2]
        cmds.setAttr(f"{self.ctrl_spaces[0]}.scale", *scale)


class CtrlColor(ctrl_base.CtrlColorBase):
    pass