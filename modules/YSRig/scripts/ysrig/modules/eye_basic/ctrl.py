from importlib import *
from maya import cmds
from ysrig import core, ctrl_base
reload(core)
reload(ctrl_base)

class Ctrl(ctrl_base.CtrlBace):
    def setup(self):
        self.other_guide_world_matrices = core.get_list_attributes(self.meta_node, "OtherGuidesWorldMatrix")

    def create(self):
        self.ctrls = []
        self.ctrl_spaces = []
        names = [jt.replace("L_", "") for jt in self.joint_names]

        for side in "LR":
            ctrl = core.EditCurve(f"{side}_{names[0]}", "Eye")
            self.ctrls += [ctrl.parent_node]
            self.ctrl_spaces += [core.create_space(ctrl.parent_node)]

            ctrl = core.EditCurve(f"{side}_{names[0]}_Aim", "Aim")
            ctrl.show_pivot()
            self.ctrls += [ctrl.parent_node]
            self.ctrl_spaces += [core.create_space(ctrl.parent_node)]

        ctrl = core.EditCurve(f"{self.grp_name}_Aim_All", "Aim_All")
        self.ctrls += [ctrl.parent_node]
        self.ctrl_spaces += [core.create_space(ctrl.parent_node)]

        for ctrl, space in zip(self.ctrls, self.ctrl_spaces):
            core.create_hierarchy(
                self.grp,
                    space, ":",
                        ctrl
            )

        self.mirror_offset = cmds.createNode("transform", name=f"{self.grp_name}_Mirror_Offset")
        core.create_hierarchy(
            self.grp,
                self.mirror_offset, ":",
                    self.ctrl_spaces[2],
                    self.ctrl_spaces[3]
        )

        """
        self.ctrls
        [0] [-5] -> Edit_L_Eye
        [1] [-4] -> Edit_L_Eye_Aim
        [2] [-3] -> Edit_R_Eye
        [3] [-2] -> Edit_R_Eye_Aim
        [4] [-1] -> Edit_Eyes_Aim_All
        """

    def set_space_transform(self):
        depth = core.auto_scale_chain_ctrls([self.ctrl_spaces[0]], self.guide_world_matrices, 3, True)
        cmds.setAttr(f"{self.ctrl_spaces[0]}.rotate", 0, 0, 0)
        aim_pos = core.decompose_matrix(self.other_guide_world_matrices[0])[0]

        pos = aim_pos
        scl = [aim_pos[0]] * 3
        cmds.setAttr(f"{self.ctrl_spaces[1]}.translate", *pos)
        cmds.setAttr(f"{self.ctrl_spaces[1]}.scale", *scl)

        for l_space, r_space in zip(self.ctrl_spaces[:2], self.ctrl_spaces[2:-1]):
            matrix = cmds.getAttr(f"{l_space}.matrix")
            pos, rot, scl = core.decompose_matrix(matrix)
            for attr, value in zip(["translate", "rotate", "scale"], [pos, rot, scl]):
                cmds.setAttr(f"{r_space}.{attr}", *value)

        pos = [0] + aim_pos[1:]
        cmds.setAttr(f"{self.ctrl_spaces[4]}.translate", *pos)
        cmds.setAttr(f"{self.ctrl_spaces[4]}.scale", *scl)

        cmds.setAttr(f"{self.mirror_offset}.scaleX", -1)

    def connect(self):
        for l_ctrl, r_ctrl in zip(self.ctrls[:2], self.ctrls[2:-1]):
            core.connect_same_attr(l_ctrl, r_ctrl, ["translate", "rotate", "scale"])

    def lock_attributes(self):
        for ctrl in self.ctrls:
            self.lock_attrs += [ctrl, ["translate"]]

        for ctrl in self.ctrls[2:-1]:
            self.lock_attrs += [ctrl, ["rotate", "scale"]]

        self.lock_attrs += [self.ctrls[1], ["rotate"]]
        self.lock_attrs += [self.ctrls[-1], ["rotate"]]


class CtrlColor(ctrl_base.CtrlColorBase):
    def set_color(self, ctrls, side):
        core.set_ctrl_shape_color(ctrls[0], core.FACIAL_COLOR_1)
        core.set_ctrl_shape_color(ctrls[1], core.LEFT_SECOND_COLOR)
        core.set_ctrl_shape_color(ctrls[2], core.FACIAL_COLOR_1)
        core.set_ctrl_shape_color(ctrls[3], core.RIGHT_SECOND_COLOR)
        core.set_ctrl_shape_color(ctrls[4], core.CENTER_SARD_COLOR)