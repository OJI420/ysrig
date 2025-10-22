from importlib import *
from maya import cmds
from ysrig import core, ctrl_base
reload(core)
reload(ctrl_base)

class Ctrl(ctrl_base.CtrlBace):
    def setup(self):
        self.pvctrl_shape_type = core.get_enum_attribute(self.meta_node, "PVControllrShapeType")
        self.root_matrix = cmds.getAttr(f"{self.meta_node}.RootMatrix")
        self.guide_joint_matrices = core.get_list_attributes(self.meta_node, "GuideJointsMatrix")
        self.other_guide_world_matrices = core.get_list_attributes(self.meta_node, "OtherGuidesWorldMatrix")

    def create(self):
        for i, name in enumerate(self.joint_names[:-1]):
            if i == 2:
                ctrl = core.EditCurve(name, "Cube")

            else:
                ctrl = core.EditCurve(name, "BoundingBox")

            space = core.create_space(ctrl.parent_node)
            self.ctrls.append(ctrl.parent_node)
            self.ctrl_spaces.append(space)

        for suffix, shape in zip(["PV", "IK", "REV_All"], [self.pvctrl_shape_type, "Foot_IK", "Pin"]):
            ctrl = core.EditCurve(f"{self.grp_name}_{suffix}", shape)
            space = core.create_space(ctrl.parent_node)
            self.ctrls.append(ctrl.parent_node)
            self.ctrl_spaces.append(space)

        for suffix in ["Heel", "OutSide", "InSide", "ToeTip", "Toe"]:
            ctrl = core.EditCurve(f"{self.grp_name}_REV_{suffix}", "Rev")
            space = core.create_space(ctrl.parent_node)
            self.ctrls.append(ctrl.parent_node)
            self.ctrl_spaces.append(space)

        for ctrl, space in zip(self.ctrls, self.ctrl_spaces):
            core.create_hierarchy(
                self.grp,
                    space, ":",
                        ctrl
            )

        """
        self.ctrls
        [0] [-13] -> Edit_L_UpperLeg
        [1] [-12] -> Edit_L_ForeLeg
        [2] [-11] -> Edit_L_Foot
        [3] [-10] -> Edit_L_Toe
        [4] [-9] -> Edit_L_TipToe
        [5] [-8] -> Edit_L_Leg_PV
        [6] [-7] -> Edit_L_Leg_IK
        [7] [-6] -> Edit_L_Leg_REV_All
        [8] [-5] -> Edit_L_Leg_REV_Heel
        [9] [-4] -> Edit_L_Leg_REV_OutSide
        [10] [-3] -> Edit_L_Leg_REV_InSide
        [11] [-2] -> Edit_L_Leg_REV_TipToe
        [12] [-1] -> Edit_L_Leg_REV_Toe
        """

    def set_space_transform(self):
        scale = core.auto_scale_chain_ctrls(self.ctrl_spaces[:2], self.guide_world_matrices[:3], 0.2, False)
        core.auto_scale_chain_ctrls(self.ctrl_spaces[3:-8], self.guide_world_matrices[3:], 1, False)

        # ForeLegの大きさを少し小さくする
        s = core.multiply_list(cmds.getAttr(f"{self.ctrl_spaces[1]}.scale")[0], 0.8)
        cmds.setAttr(f"{self.ctrl_spaces[1]}.scale", *s)

        # つま先の大きさ調整
        rev_distance = core.get_distance(core.decompose_matrix(self.other_guide_world_matrices[3])[0], core.decompose_matrix(self.other_guide_world_matrices[4])[0])

        if len(self.ctrls) == 13:
            s = cmds.getAttr(f"{self.ctrl_spaces[-10]}.scale")[0]
            s = [s[0], rev_distance*0.45, rev_distance*0.45]
            cmds.setAttr(f"{self.ctrl_spaces[-10]}.scale", *s)

            s = cmds.getAttr(f"{self.ctrl_spaces[-9]}.scale")[0]
            s = [s[0], rev_distance*0.4, rev_distance*0.4]
            cmds.setAttr(f"{self.ctrl_spaces[-9]}.scale", *s)

        else :
            s = cmds.getAttr(f"{self.ctrl_spaces[-9]}.scale")[0]
            s = [s[0], rev_distance*0.45, rev_distance*0.45]
            cmds.setAttr(f"{self.ctrl_spaces[-9]}.scale", *s)

        # Foot
        pos = core.decompose_matrix(self.guide_world_matrices[2])[0]
        rot = core.decompose_matrix(self.root_matrix)[1]
        rot = [r1 + r2 for r1, r2 in zip(rot, core.decompose_matrix(self.guide_joint_matrices[2])[1])]
        scl = [scale * 0.6] * 3

        cmds.setAttr(f"{self.ctrl_spaces[2]}.translate", *pos)
        cmds.setAttr(f"{self.ctrl_spaces[2]}.rotate", *rot)
        cmds.setAttr(f"{self.ctrl_spaces[2]}.scale", *scl)

        # PoleVector
        s = [scale * 0.4] * 3
        pos = core.decompose_matrix(self.other_guide_world_matrices[0])[0]
        cmds.setAttr(f"{self.ctrl_spaces[-8]}.translate", *pos)
        cmds.setAttr(f"{self.ctrl_spaces[-8]}.scale", *s)

        # IK
        center_mat = self.other_guide_world_matrices[1]
        heel_mat = self.other_guide_world_matrices[2]
        out_mat = self.other_guide_world_matrices[3]
        in_mat = self.other_guide_world_matrices[4]
        tiptoe_mat = self.other_guide_world_matrices[5]
        rev_all_mat = self.other_guide_world_matrices[6]

        pos = core.decompose_matrix(core.get_average_pos_matrix([heel_mat, tiptoe_mat]))[0]

        center_pos = core.decompose_matrix(center_mat)[0]
        heel_pos = core.decompose_matrix(heel_mat)[0]
        out_pos = core.decompose_matrix(out_mat)[0]
        in_pos = core.decompose_matrix(in_mat)[0]
        tiptoe_pos = core.decompose_matrix(tiptoe_mat)[0]
        rev_all_pos = core.decompose_matrix(rev_all_mat)[0]

        depth = core.get_distance(heel_pos, tiptoe_pos)
        width = core.get_distance(out_pos, in_pos)

        cmds.setAttr(f"{self.ctrl_spaces[-7]}.translate", *pos)
        cmds.setAttr(f"{self.ctrl_spaces[-7]}.scale", width * 0.9, 1, depth * 0.9)

        tmp = cmds.createNode("transform", name="tmp")
        cmds.setAttr(f"{tmp}.translate", *tiptoe_pos)
        aim = core.connect_aim_constraint(tmp, self.ctrl_spaces[-7], aim=[0, 0, 1], offset=False)
        cmds.delete(aim)
        cmds.delete(tmp)

        # Rev
        s = [scale] * 3
        tmp = cmds.createNode("transform")
        cmds.setAttr(f"{tmp}.translate", *center_pos)
        for i, space, pos in zip(range(5), self.ctrl_spaces[-6:-1], [rev_all_pos, heel_pos, out_pos, in_pos, tiptoe_pos]):
            cmds.setAttr(f"{space}.translate", *pos)
            cmds.setAttr(f"{space}.scale", *s)
            if i:
                aim = core.connect_aim_constraint(tmp, space, offset=False)
                cmds.delete(aim)

        cmds.delete(tmp)

        toe_mat = self.guide_world_matrices[3]
        tiptoe_mat = self.guide_world_matrices[-1]
        toe_pos, toe_rot = core.decompose_matrix(toe_mat)[:-1]
        tiptoe_pos = core.decompose_matrix(tiptoe_mat)[0]

        tmp = cmds.createNode("transform")
        cmds.setAttr(f"{tmp}.translate", *toe_pos)
        cmds.setAttr(f"{tmp}.rotate", *toe_rot)

        cmds.setAttr(f"{self.ctrl_spaces[-1]}.translate", *tiptoe_pos)
        cmds.setAttr(f"{self.ctrl_spaces[-1]}.translateY", toe_pos[1])
        cmds.setAttr(f"{self.ctrl_spaces[-1]}.scale", *s)
        aim = core.connect_aim_constraint(tmp, self.ctrl_spaces[-1], offset=False)
        cmds.delete(aim)
        pc = core.connect_parent_constraint(tmp, self.ctrl_spaces[-1], mo=True)
        cmds.rotate(70, tmp, z=True, os=True, r=True)
        cmds.delete(pc)
        cmds.delete(tmp)

    def lock_attributes(self):
        self._lock_attrs += [
            self.ctrls[-8], ["translate"],
            self.ctrls[-7], ["translate"],
            self.ctrls[-6], ["translate", "rotate"],
            self.ctrls[-1], ["ty", "tz", "rotate"]
            ]
        for ctrl in self.ctrls[-5:-1]:
            self._lock_attrs += [ctrl, ["translate", "rotate"]]


class CtrlColor(ctrl_base.CtrlColorBase):
    def set_color(self, ctrls, side):
        super().set_color(ctrls, side)

        if side == "L":
            core.set_ctrl_shape_color(ctrls[-6], core.LEFT_SARD_COLOR)
            core.set_ctrl_shape_color(ctrls[-7], core.LEFT_SARD_COLOR)
            core.set_ctrl_shape_color(ctrls[-8], core.LEFT_SECOND_COLOR)
            for ctrl in ctrls[-5:]:
                core.set_ctrl_shape_color(ctrl, core.LEFT_SECOND_COLOR)

        elif side == "R":
            core.set_ctrl_shape_color(ctrls[-6], core.RIGHT_SARD_COLOR)
            core.set_ctrl_shape_color(ctrls[-7], core.RIGHT_SARD_COLOR)
            core.set_ctrl_shape_color(ctrls[-8], core.RIGHT_SECOND_COLOR)
            for ctrl in ctrls[-5:]:
                core.set_ctrl_shape_color(ctrl, core.RIGHT_SECOND_COLOR)

        else:
            core.set_ctrl_shape_color(ctrls[-6], core.CENTER_SARD_COLOR)
            core.set_ctrl_shape_color(ctrls[-7], core.CENTER_SARD_COLOR)
            core.set_ctrl_shape_color(ctrls[-8], core.CENTER_SECOND_COLOR)
            for ctrl in ctrls[-5:]:
                core.set_ctrl_shape_color(ctrl, core.CENTER_SECOND_COLOR)