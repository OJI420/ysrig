from importlib import *
from maya import cmds
from ysrig import core, ctrl_base
reload(core)
reload(ctrl_base)

class Ctrl(ctrl_base.CtrlBace):
    def create(self):
        ctrls = [None] * (self.joint_count + 1)
        ctrl_spaces = [None] * (self.joint_count + 1)
        for i, name in enumerate(self.joint_names + [self.grp_name]):
            if i == self.joint_count:
                ctrl = core.EditCurve(f"{name}_Torso", "Torso")

            elif i:
                ctrl = core.EditCurve(name, "Spine")

            else:
                ctrl = core.EditCurve(name, "Hip")

            ctrls[i] = ctrl.parent_node
            ctrl_spaces[i] = core.create_space(ctrls[i])
            core.create_hierarchy(
                self.grp,
                    ctrl_spaces[i], ":",
                        ctrls[i]
            )

        self.ctrls = ctrls
        self.ctrl_spaces = ctrl_spaces

        """
        self.ctrls
        [0] [-5] -> Edit_Hip
        [1] [-4] -> Edit_Spine_01
        [2] [-3] -> Edit_Spine_02
        [3] [-2] -> Edit_Spine_03
        [4] [-1] -> Edit_Spine_Torso
        """

    def set_space_transform(self):
        scale = core.auto_scale_chain_ctrls(self.ctrl_spaces[:-2], self.guide_world_matrices, 1.5, True)

        pos, rot = core.decompose_matrix(self.guide_world_matrices[-1])[:-1]
        cmds.setAttr(f"{self.ctrl_spaces[-2]}.translate", *pos)
        cmds.setAttr(f"{self.ctrl_spaces[-2]}.rotate", *rot)
        cmds.setAttr(f"{self.ctrl_spaces[-2]}.scale", scale, scale, scale)

        cmds.matchTransform(self.ctrl_spaces[-1], self.ctrl_spaces[0])
        for space in self.ctrl_spaces[1:]:
            rotate = cmds.getAttr(f"{space}.rotate")[0]
            rotate = core.get_round_rotate(rotate)
            cmds.setAttr(f"{space}.rotate", *rotate)


class CtrlColor(ctrl_base.CtrlColorBase):
    def set_color(self, ctrls, side):
        super().set_color(ctrls, side)

        if side == "L":
            core.set_ctrl_shape_color(ctrls[0], core.LEFT_SECOND_COLOR)
            core.set_ctrl_shape_color(ctrls[-1], core.LEFT_SARD_COLOR)

        elif side == "R":
            core.set_ctrl_shape_color(ctrls[0], core.RIGHT_SECOND_COLOR)
            core.set_ctrl_shape_color(ctrls[-1], core.RIGHT_SARD_COLOR)

        else:
            core.set_ctrl_shape_color(ctrls[0], core.CENTER_SECOND_COLOR)
            core.set_ctrl_shape_color(ctrls[-1], core.CENTER_SARD_COLOR)