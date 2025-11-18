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

            ctrl = core.EditCurve(f"{side}_{names[2]}", "Eyelid")
            ctrl.set_rotate([-20, 0, 0])
            self.ctrls += [ctrl.parent_node]
            self.ctrl_spaces += [core.create_space(ctrl.parent_node)]

            ctrl = core.EditCurve(f"{side}_{names[3]}", "Eyelid")
            ctrl.set_rotate([-20, 0, 0])
            ctrl.set_rotate([0, 0, 180])
            self.ctrls += [ctrl.parent_node]
            self.ctrl_spaces += [core.create_space(ctrl.parent_node)]

            ctrl = core.EditCurve(f"{side}_{names[0]}_UI", "Face_UI")
            ctrl.set_display_type(1)
            ctrl.set_scale(3, 1, 1)
            self.ctrls += [ctrl.parent_node]
            self.ctrl_spaces += [core.create_space(ctrl.parent_node)]

            # 目のUI
            for i in range(3):
                s = core.EditCurve("tmp", "Scale")
                s.set_display_type(2)
                s.set_translate([i - 1, 0, 0])
                s.reparent_shape(ctrl.parent_node)

                s = core.EditCurve("tmp", f"Pointer_{i + 1}")
                s.set_translate([i - 1, 0, 0])
                s.reparent_shape(ctrl.parent_node)

            for i, name in enumerate(["OpenClose", "ClosePos", "Scale"]):
                ctrl = core.EditCurve(f"{side}_{names[0]}_{name}", f"Pointer_{i + 1}")
                cmds.setAttr(f"{ctrl.shape_node}.visibility", False)
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
        cmds.parent(self.mirror_offset, self.grp)
        for space in self.ctrl_spaces[8:-1]:
            cmds.parent(space, self.mirror_offset)

        """
        self.ctrls
        [0] [-17] -> Edit_L_Eye
        [1] [-16] -> Edit_L_Eyelid_Top
        [2] [-15] -> Edit_L_Eyelid_Bottom
        [3] [-14] -> Edit_L_Eye_UI
        [4] [-13] -> Edit_L_Eye_OpenClose
        [5] [-12] -> Edit_L_Eye_ClosePos
        [6] [-11] -> Edit_L_Eye_Scale
        [7] [-10] -> Edit_L_Eye_Aim
        [8] [-9] -> Edit_R_Eye
        [9] [-8] -> Edit_R_Eyelid_Top
        [10] [-7] -> Edit_R_Eyelid_Bottom
        [11] [-6] -> Edit_R_Eye_UI
        [12] [-5] -> Edit_R_Eye_OpenClose
        [13] [-4] -> Edit_R_Eye_ClosePos
        [14] [-3] -> Edit_R_Eye_Scale
        [15] [-2] -> Edit_R_Eye_Aim
        [16] [-1] -> Edit_Eyes_Aim_All
        """

    def set_space_transform(self):
        depth = core.auto_scale_chain_ctrls([self.ctrl_spaces[0]], self.guide_world_matrices, 3, True)
        cmds.setAttr(f"{self.ctrl_spaces[0]}.rotate", 0, 0, 0)

        scale = [depth * 0.2] * 3
        pos, rot = core.decompose_matrix(self.guide_world_matrices[0])[:-1]
        for space in self.ctrl_spaces[1:3]:
            cmds.setAttr(f"{space}.translate", *pos)
            cmds.setAttr(f"{space}.rotate", *rot)
            cmds.setAttr(f"{space}.scale", *scale)

        scale = [depth * 0.5] * 3
        pos = core.decompose_matrix(self.guide_world_matrices[1])[0]
        pos[0] += depth * 2
        cmds.setAttr(f"{self.ctrl_spaces[3]}.translate", *pos)
        cmds.setAttr(f"{self.ctrl_spaces[3]}.scale", *scale)

        for i, space in enumerate(self.ctrl_spaces[4:7]):
            p = pos[:] # p = pos だと参照渡しになってしまうのでスライスでコピーを作る
            p[0] += (i - 1) * (depth * 0.5)
            cmds.setAttr(f"{space}.translate", *p)
            cmds.setAttr(f"{space}.scale", *scale)

        pos = core.decompose_matrix(self.other_guide_world_matrices[0])[0]
        scl = [pos[0]] * 3
        cmds.setAttr(f"{self.ctrl_spaces[7]}.translate", *pos)
        cmds.setAttr(f"{self.ctrl_spaces[7]}.scale", *scl)

        pos = [0] + pos[1:]
        cmds.setAttr(f"{self.ctrl_spaces[-1]}.translate", *pos)
        cmds.setAttr(f"{self.ctrl_spaces[-1]}.scale", *scl)

        for l_space, r_space in zip(self.ctrl_spaces[:8], self.ctrl_spaces[8:-1]):
            matrix = cmds.getAttr(f"{l_space}.matrix")
            pos, rot, scl = core.decompose_matrix(matrix)
            for attr, value in zip(["translate", "rotate", "scale"], [pos, rot, scl]):
                cmds.setAttr(f"{r_space}.{attr}", *value)

        cmds.setAttr(f"{self.mirror_offset}.scaleX", -1)

    def connect(self):
        for l_ctrl, r_ctrl in zip(self.ctrls[:8], self.ctrls[8:-1]):
            core.connect_same_attr(l_ctrl, r_ctrl, ["translate", "rotate", "scale"])

    def lock_attributes(self):
        for ctrl in self.ctrls[:1] + self.ctrls[4:]:
            self.lock_attrs += [ctrl, ["translate"]]

        for ctrl in self.ctrls[8:-1]:
            self.lock_attrs += [ctrl, ["rotate", "scale"]]

        self.lock_attrs += [self.ctrls[7], ["rotate"]]
        self.lock_attrs += [self.ctrls[-1], ["rotate"]]


class CtrlColor(ctrl_base.CtrlColorBase):
    def set_color(self, ctrls, side):
        core.set_ctrl_shape_color(ctrls[0], core.FACIAL_COLOR_1)
        core.set_ctrl_shape_color(ctrls[8], core.FACIAL_COLOR_1)
        for ctrl in ctrls[1:7] + ctrls[9:15]:
            core.set_ctrl_shape_color(ctrl, core.FACIAL_COLOR_2)

        core.set_ctrl_shape_color(ctrls[7], core.LEFT_SECOND_COLOR)
        core.set_ctrl_shape_color(ctrls[15], core.RIGHT_SECOND_COLOR)
        core.set_ctrl_shape_color(ctrls[16], core.CENTER_SARD_COLOR)