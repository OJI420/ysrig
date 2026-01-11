from importlib import *
from maya import cmds
from ysrig import core, rig_base
reload(core)
reload(rig_base)

class Rig(rig_base.RigBace):
    def setup(self):
        self.pv_ctrl_shape_type = core.get_enum_attribute(self.meta_node, "PVControllrShapeType")
        self.root_matrix = cmds.getAttr(f"{self.meta_node}.RootMatrix")
        self.guide_joint_matrices = core.get_list_attributes(self.meta_node, "GuideJointsMatrix")

    def create(self):
        fk_ctrls = core.convert_joint_to_controller(self.base_joints[:-1])
        self.ctrls = [None] * (len(fk_ctrls) + 8)
        self.ctrl_instances = [None] * (len(fk_ctrls) + 8)

        total_count = 0
        for i, ctrl, name in zip(range(len(fk_ctrls)), fk_ctrls, self.joint_names):
            if i == 2:
                c = core.CtrlCurve(f"{name}1", "Cube")

            else:
                c = core.CtrlCurve(f"{name}1", "BoundingBox")

            c.reparent_shape(ctrl)
            self.ctrl_instances[i] = c
            self.ctrls[i] = c.parent_node

            total_count += 1

        cmds.parent(self.ctrls[2], w=True)
        cmds.parent(self.ctrls[3], w=True)
        rot = core.decompose_matrix(self.root_matrix)[1]
        rot = [r1 + r2 for r1, r2 in zip(rot, core.decompose_matrix(self.guide_joint_matrices[2])[1])]
        cmds.setAttr(f"{self.ctrls[2]}.jointOrient", 0, 0, 0)
        cmds.setAttr(f"{self.ctrls[2]}.rotate", *rot)
        core.create_hierarchy(
            self.ctrls[1],
                self.ctrls[2], ":",
                    self.ctrls[3],
        )
        cmds.makeIdentity(self.ctrls[2], a=True)

        ik_ctrl = core.CtrlCurve(f"{self.grp_name}_IK", "Foot_IK")
        pv_ctrl = core.CtrlCurve(f"{self.grp_name}_PV", self.pv_ctrl_shape_type)
        rev_all_ctrl = core.CtrlCurve(f"{self.grp_name}_REV_All", "Pin")

        for c in [pv_ctrl, ik_ctrl, rev_all_ctrl]:
            pos, rot = core.decompose_matrix(self.ctrl_space_matrices[total_count])[:-1]
            cmds.setAttr(f"{c.parent_node}.translate", *pos)
            cmds.setAttr(f"{c.parent_node}.rotate", *rot)

            self.ctrl_instances[total_count] = c
            self.ctrls[total_count] = c.parent_node
            total_count += 1

        pos = core.decompose_matrix(self.ctrl_space_matrices[2])[0]
        cmds.setAttr(f"{self.ctrls[-7]}.translate", *pos)
        cmds.setAttr(f"{self.ctrls[-7]}.rotate", 0, 0, 0)

        self.rev_toe_ctrls = [None] * len(self.base_joints[3:-1])
        self.rev_toe_ctrl_instances = [None] * len(self.base_joints[3:-1])

        toe_ctrls = core.convert_joint_to_controller(self.base_joints[3:-1], prefix="Ctrl_REV_FK_")
        toe_ctrls = [cmds.rename(n, f"Ctrl_{self.grp_name}_REV_FK_{s}") for n, s in zip(toe_ctrls, ["Toe", "ToeSub"])]
        for i, ctrl, name in zip(range(len(toe_ctrls)), toe_ctrls, self.joint_names[3:-1]):
            c = core.CtrlCurve(f"{name}1", "BoundingBox")

            c.reparent_shape(ctrl)
            self.rev_toe_ctrl_instances[i] = c
            self.rev_toe_ctrls[i] = c.parent_node

        for suffix, mat in zip(["Heel", "OutSide", "InSide", "ToeTip", "Toe"], self.ctrl_space_matrices[-5:]):
            ctrl = core.CtrlCurve(f"{self.grp_name}_REV_{suffix}", "Rev")
            pos, rot = core.decompose_matrix(mat)[:-1]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)
            cmds.setAttr(f"{ctrl.parent_node}.rotate", *rot)
            self.ctrl_instances[total_count] = ctrl
            self.ctrls[total_count] = ctrl.parent_node
            total_count += 1

        pos = core.decompose_matrix(self.ctrl_space_matrices[3])[0]
        cmds.setAttr(f"{self.ctrls[-1]}.translate", *pos)

        self.hds = [None] * 3

        self.ik_joints = core.convert_joint_to_controller(self.base_joints, prefix="Ikjt_")
        self.hds[0], ef = cmds.ikHandle(sj=self.ik_joints[0], ee=self.ik_joints[2], name=f"Ikhandle_{self.grp_name}")
        self.hds[1], ef = cmds.ikHandle(sj=self.ik_joints[3], ee=self.ik_joints[4], sol="ikSCsolver", name=f"Ikhandle_{self.grp_name}_Toe")
        self.hds[2], ef = cmds.ikHandle(sj=self.ik_joints[2], ee=self.ik_joints[3], sol="ikSCsolver", name=f"Ikhandle_{self.grp_name}_Foot")
        for hd in self.hds:
            cmds.setAttr(f"{hd}.visibility", False)

        core.create_hierarchy(
            self.ctrl_grp,
                fk_ctrls[0],
                self.ik_joints[0],
                ik_ctrl.parent_node, ":",
                    self.ctrls[-5], ":",
                        self.ctrls[-4], ":",
                            self.ctrls[-3], ":",
                                self.ctrls[-2], ":",
                                    self.ctrls[-1], ":",
                                        self.hds[0], "..",
                                    toe_ctrls[0], ":", 
                                        self.hds[1],
                                        self.hds[2], "..", "..", "..", "..", "..",
                rev_all_ctrl.parent_node, "..",
                pv_ctrl.parent_node,
            )
        
        ctrls = self.ctrls[:1] + self.ctrls[-8:] + self.rev_toe_ctrls[:1]
        self.ctrl_spaces = [None] * len(ctrls)
        for i, ctrl in enumerate(ctrls):
            self.ctrl_spaces[i] = core.create_space(ctrl, parent=True)

        self.knee_line = core.connect_curve_point(f"CV_{self.grp_name}_Knee", [self.ik_joints[1], self.ctrls[-8]], parent=self.ctrl_grp, lc=self.connect_type)

        target_ik = cmds.createNode("transform", name=f"Target_{self.grp_name}_IK")
        cmds.parent(target_ik, self.ik_joints[2])
        cmds.matchTransform(target_ik, self.ctrls[2])

        target_fk = cmds.createNode("transform", name=f"Target_{self.grp_name}_FK")
        cmds.parent(target_fk, self.ctrls[2])
        cmds.matchTransform(target_fk, self.ctrls[-7])

        """
        self.ctrls
        [0] [-13] -> Ctrl_L_UpperLeg
        [1] [-12] -> Ctrl_L_ForeLeg
        [2] [-11] -> Ctrl_L_Foot
        [3] [-10] -> Ctrl_L_Toe
        [4] [-9] -> Ctrl_L_ToeSub
        [5] [-8] -> Ctrl_L_Leg_PV
        [6] [-7] -> Ctrl_L_Leg_IK
        [7] [-6] -> Ctrl_L_Leg_REV_All
        [8] [-5] -> Ctrl_L_Leg_REV_Heel
        [9] [-4] -> Ctrl_L_Leg_REV_OutSide
        [10] [-3] -> Ctrl_L_Leg_REV_InSide
        [11] [-2] -> Ctrl_L_Leg_REV_ToeTip
        [12] [-1] -> Ctrl_L_Leg_REV_Toe
        """

        """
        # self.ctrl_spaces
        [0], [-10] -> Ctrl_L_UpperLeg_Space
        [1], [-9] -> Ctrl_L_Leg_PV_Space
        [2], [-8] -> Ctrl_L_Leg_IK_Space
        [3], [-7] -> Ctrl_L_Leg_REV_All_Space
        [4], [-6] -> Ctrl_L_Leg_REV_Heel_Space
        [5], [-5] -> Ctrl_L_Leg_REV_OutSide_Space
        [6], [-4] -> Ctrl_L_Leg_REV_InSide_Space
        [7], [-3] -> Ctrl_L_Leg_REV_TipToe_Space
        [8], [-2] -> Ctrl_L_Leg_REV_Toe_Space
        [9], [-1] -> Ctrl_REV_FK_L_Toe_Space
        """

    def set_color(self):
        super().set_color()
        if self.side == "L":
            for ctrl in self.rev_toe_ctrls:
                core.set_ctrl_shape_color(ctrl, core.LEFT_MAIN_COLOR)

        elif self.side == "R":
            for ctrl in self.rev_toe_ctrls:
                core.set_ctrl_shape_color(ctrl, core.RIGHT_MAIN_COLOR)

        else:
            for ctrl in self.rev_toe_ctrls:
                core.set_ctrl_shape_color(ctrl, core.CENTER_MAIN_COLOR)

    def set_shape_transform(self):
        super().set_shape_transform()
        for ctrl, ctrl_mat, spase_mat in zip(self.rev_toe_ctrl_instances, self.ctrl_matrices[3:], self.ctrl_space_matrices[3:]):
            offset_scale = core.decompose_matrix(spase_mat)[2]
            ctrl.set_matrix(ctrl_mat, offset_scale=offset_scale)
            ctrl.set_width(self.ctrl_line_width)

        foot_pos = core.decompose_matrix(self.ctrl_space_matrices[3])[0]
        toe_rev_pos = core.decompose_matrix(self.ctrl_space_matrices[-1])[0]
        dis = core.get_distance(foot_pos, toe_rev_pos)
        self.ctrl_instances[-1].set_translate([dis * -1, 0, 0])

        for ctrl in self.ctrls[3:] + self.rev_toe_ctrls:
            core.clamp_curve_y_zero(ctrl)

        pos1 = core.decompose_matrix(self.ctrl_space_matrices[2])[0]
        pos2, rot = core.decompose_matrix(self.ctrl_space_matrices[-7])[:-1]
        pos = [p2 - p1 for p1, p2 in zip(pos1, pos2)]
        self.ctrl_instances[-7].set_rotate(rot)
        self.ctrl_instances[-7].set_translate(pos)

    def add_settings(self):
        cmds.addAttr(self.settings_node, ln="IKFK", at="enum", en="IK:FK:", k=True)
        cmds.addAttr(self.settings_node, ln="FK_WL", at="enum", en="World:Local:", k=True)
        cmds.addAttr(self.settings_node, ln="IK_WL", at="enum", en="World:Local:", k=True)
        cmds.addAttr(self.settings_node, ln="PV_WL", at="enum", en="World:Local:", k=True)

        cmds.addAttr(self.ctrls[-6], ln="________________", at="enum", en="Settings", k=True)
        cmds.setAttr(f"{self.ctrls[-6]}.________________", l=True)
        cmds.addAttr(self.ctrls[-6], ln="ToeLiftThreshold", at="double", min=0, dv=20, k=True)
        cmds.addAttr(self.ctrls[-6], ln="ToeContactAngle", at="double", min=0, dv=0, k=True)

    def connect(self):
        if len(self.rev_toe_ctrls) == 2:
            core.connect_same_attr(self.rev_toe_ctrls[-1], self.ik_joints[-2], ["rotate"])

        pv_dv = core.connect_matrix(self.ctrls[-7], self.ctrl_spaces[1], lc=self.connect_type, suffix="_Local")[1]
        cmds.poleVectorConstraint(self.ctrls[-8], self.hds[0])

        # IKFK
        core.connect_switch_attr(
            f"{self.settings_node}.IKFK",
            core.compose_attr_paths(self.ctrls[0:-8], "visibility", multi=True),
            core.compose_attr_paths(self.ctrls[-8:] + self.rev_toe_ctrls + [self.knee_line], "visibility", multi=True)
        )
        for px, ik, fk in zip(self.proxies, self.ik_joints[:-1], self.ctrls[0:-8]):
            dv = core.connect_matrix(fk, px, rt=True, lc=self.connect_type)[1]
            core.connect_pair_blend(weight=f"{self.settings_node}.IKFK", in_rt1=f"{ik}.rotate", in_rt2=f"{dv}.outputRotate", out_rt=f"{px}.rotate:XYZ")

        # FK WL
        dv = core.connect_matrix(self.ROOT_OFFSET_CTRL, self.ctrl_spaces[0], rt=True, lc=False)[1]
        core.connect_pair_blend(weight=f"{self.settings_node}.FK_WL", in_rt1=f"{dv}.outputRotate", in_rt2=f"{dv}.outputRotate!", out_rt=f"{self.ctrl_spaces[0]}.rotate:XYZ")

        # IK WL
        dv = core.connect_matrix(self.ROOT_OFFSET_CTRL, self.ctrl_spaces[2], tl=True, rt=True, lc=False)[1]
        core.connect_pair_blend(weight=f"{self.settings_node}.IK_WL", in_tl1=f"{dv}.outputTranslate", in_tl2=f"{dv}.outputTranslate!", in_rt1=f"{dv}.outputRotate", in_rt2=f"{dv}.outputRotate!",
                                out_tl=f"{self.ctrl_spaces[2]}.translate:XYZ", out_rt=f"{self.ctrl_spaces[2]}.rotate:XYZ")

        # PV WL
        dv = core.connect_matrix(self.ROOT_OFFSET_CTRL, self.ctrl_spaces[1], tl=True, rt=True ,lc=False, suffix="_World")[1]
        core.connect_pair_blend(weight=f"{self.settings_node}.PV_WL", in_tl1=f"{dv}.outputTranslate", in_tl2=f"{pv_dv}.outputTranslate", in_rt1=f"{dv}.outputRotate", in_rt2=f"{pv_dv}.outputRotate",
                                out_tl=f"{self.ctrl_spaces[1]}.translate:XYZ", out_rt=f"{self.ctrl_spaces[1]}.rotate:XYZ")

        # ↓ リバースフットギミック

        # Heel
        cd = core.connect_condition(name=f"Cd_{self.ctrls[-5]}", operation=3, ft=f"{self.ctrls[-6]}.rotateX", fr=f"{self.ctrls[-6]}.rotateX")
        fm = core.connect_float_math(name=f"Fm_{self.ctrls[-5]}", operation=2, fa=f"{cd}.outColorR", fb=-1)
        core.connect_compose_matrix(name=f"Cm_{self.ctrls[-5]}", rz=f"{fm}.outFloat", out=[f"{self.ctrls[-5]}.offsetParentMatrix"])

        # Out
        cd = core.connect_condition(name=f"Cd_{self.ctrls[-4]}", operation=3, ft=f"{self.ctrls[-6]}.rotateZ", fr=f"{self.ctrls[-6]}.rotateZ")
        fm = core.connect_float_math(name=f"Fm_{self.ctrls[-4]}", operation=2, fa=f"{cd}.outColorR", fb=-1)
        core.connect_compose_matrix(name=f"Cm_{self.ctrls[-4]}", rz=f"{fm}.outFloat", out=[f"{self.ctrls[-4]}.offsetParentMatrix"])

        # In
        cd = core.connect_condition(name=f"Cd_{self.ctrls[-3]}", operation=4, ft=f"{self.ctrls[-6]}.rotateZ", fr=f"{self.ctrls[-6]}.rotateZ")
        core.connect_compose_matrix(name=f"Cm_{self.ctrls[-3]}", rz=f"{cd}.outColorR", out=[f"{self.ctrls[-3]}.offsetParentMatrix"])

        # Toe
        fm1 = core.connect_float_math(name=f"Fm_{self.ctrls[-2]}", operation=1, fa=f"{self.ctrls[-6]}.rotateX", fb=f"{self.ctrls[-6]}.ToeLiftThreshold")
        fm2 = core.connect_float_math(name=f"Fm_{self.ctrls[-1]}", operation=1, fa=f"{self.ctrls[-6]}.ToeLiftThreshold", fb=f"{fm1}.outFloat")

        cd = core.connect_condition(name=f"Cd_{self.ctrls[-2]}", operation=3, ft=f"{fm1}.outFloat", fr=0, tr=f"{fm1}.outFloat")
        core.connect_compose_matrix(name=f"Cm_{self.ctrls[-2]}", rz=f"{cd}.outColorR", out=[f"{self.ctrls[-2]}.offsetParentMatrix"])

        cd1 = core.connect_condition(name=f"Cd_{self.ctrls[-1]}_01", operation=3, ft=f"{self.ctrls[-6]}.rotateX", fr=0, tr=f"{self.ctrls[-6]}.rotateX")
        cd2 = core.connect_condition(name=f"Cd_{self.ctrls[-1]}_02", operation=4, ft=f"{self.ctrls[-6]}.rotateX", st=f"{self.ctrls[-6]}.ToeLiftThreshold", fr=f"{fm2}.outFloat", tr=f"{cd1}.outColorR")
        cd3 = core.connect_condition(name=f"Cd_{self.ctrls[-1]}_03", operation=3, ft=f"{cd2}.outColorR", fr=0, tr=f"{cd2}.outColorR")
        core.connect_compose_matrix(name=f"Cm_{self.ctrls[-1]}", rz=f"{cd3}.outColorR", out=[f"{self.ctrls[-1]}.offsetParentMatrix"])

        cd1 = core.connect_condition(name=f"Cd_{self.rev_toe_ctrls[-1]}_01", operation=3, ft=f"{self.ctrls[-6]}.rotateX", fr=0, tr=f"{self.ctrls[-6]}.rotateX")
        cd2 = core.connect_condition(name=f"Cd_{self.rev_toe_ctrls[-1]}_02", operation=3, ft=f"{self.ctrls[-6]}.rotateX", st=f"{self.ctrls[-6]}.ToeContactAngle", fr=f"{cd1}.outColorR", tr=f"{self.ctrls[-6]}.ToeContactAngle")
        fm = core.connect_float_math(name=f"Fm_{self.rev_toe_ctrls[-1]}", operation=2, fa=f"{cd2}.outColorR", fb=-1)
        core.connect_compose_matrix(name=f"Cm_{self.rev_toe_ctrls[-1]}", rz=f"{fm}.outFloat", out=[f"{self.rev_toe_ctrls[-1]}.offsetParentMatrix"])

        # IKの伸び切りチェッカー
        core.connect_ik_stretch_warning([self.ik_joints[0], self.hds[0]], cmds.getAttr(f"{self.ik_joints[1]}.tx") * 2, ctrls=[self.ctrls[-8], self.ctrls[-7]])

    def set_attr(self):
        cmds.setAttr(f"{self.settings_node}.IKFK", 0)
        cmds.setAttr(f"{self.settings_node}.FK_WL", 1)
        cmds.setAttr(f"{self.settings_node}.IK_WL", 0)
        cmds.setAttr(f"{self.settings_node}.PV_WL", 1)

        if not cmds.attributeQuery("ToeLiftThreshold", node=self.meta_node, exists=True):
            return

        value = cmds.getAttr(f"{self.meta_node}.ToeLiftThreshold")
        cmds.setAttr(f"{self.ctrls[-6]}.ToeLiftThreshold", value, k=False, cb=True)

        value = cmds.getAttr(f"{self.meta_node}.ToeContactAngle")
        cmds.setAttr(f"{self.ctrls[-6]}.ToeContactAngle", value, k=False, cb=True)

    def lock_attributes(self):
        for ctrl in self.ctrls:
            self.lock_attrs += [ctrl, ["scale", "visibility"]]

        for ctrl in self.ctrls[0:-8] + self.rev_toe_ctrls: # FK
            self.lock_attrs += [ctrl, ["translate", "scale", "visibility"]]

        self.lock_attrs += [
            self.ctrls[1], ["rx", "ry"],
            self.rev_toe_ctrls[0], ["rx", "ry"],
            self.ctrls[3], ["rx", "ry"],
            self.ctrls[-8], ["rotate"],
            self.ctrls[-6], ["translate", "ry"],
            self.ctrls[-5], ["translate", "rx"],
            self.ctrls[-4], ["translate", "rx", "ry"],
            self.ctrls[-3], ["translate", "rx", "ry"],
            self.ctrls[-2], ["translate", "rx"],
            self.ctrls[-1], ["translate", "rx", "ry"]
            ]

        knee_orient = cmds.getAttr(f"{self.ctrls[1]}.jointOrientZ")
        knee_orient *= -1
        cmds.transformLimits(self.ctrls[1], rz=[0, knee_orient], erz=[0, 1])

    def _distribute_shape_instances(self):
        super()._distribute_shape_instances()
        for node in self.rev_toe_ctrls:
            tmp = cmds.instance(self.settings_node)[0]
            shape = f"{tmp}|{self.settings_node}"
            cmds.parent(shape, node, r=True, s=True)
            cmds.delete(tmp)

    def collect_meta_data(self):
        self.meta_data["ToeLiftThreshold"] = core.compose_attr_paths(self.ctrls[-6], "ToeLiftThreshold")
        self.meta_data["ToeContactAngle"] = core.compose_attr_paths(self.ctrls[-6], "ToeContactAngle")


class RigMirror(Rig):
    def _setup(self, meta_node):
        super()._setup(meta_node)
        self.src_joints = [f"JT_{name}" for name in self.joint_names]
        self.src_side = self.side[:]
        self.build, self.side, self.grp_name, self.joint_names = rig_base.get_mirror_names(self.side, self.grp_name, self.joint_names)

    def create(self):
        fk_ctrls = core.convert_joint_to_controller(self.src_joints[:-1], sr=[f"{self.src_side}_", f"{self.side}_"])
        self.ctrls = [None] * (len(fk_ctrls) + 8)
        self.ctrl_instances = [None] * (len(fk_ctrls) + 8)

        total_count = 0
        for i, ctrl, name in zip(range(len(fk_ctrls)), fk_ctrls, self.joint_names):
            if i == 2:
                c = core.CtrlCurve(f"{name}1", "Cube")

            else:
                c = core.CtrlCurve(f"{name}1", "BoundingBox")

            c.reparent_shape(ctrl)
            self.ctrl_instances[i] = c
            self.ctrls[i] = c.parent_node

            total_count += 1

        cmds.parent(self.ctrls[2], w=True)
        cmds.parent(self.ctrls[3], w=True)
        rot = core.decompose_matrix(self.root_matrix)[1]
        rot = [r1 + r2 for r1, r2 in zip(rot, core.decompose_matrix(self.guide_joint_matrices[2])[1])]
        cmds.setAttr(f"{self.ctrls[2]}.jointOrient", 0, 0, 0)
        cmds.setAttr(f"{self.ctrls[2]}.rotate", *rot)
        core.create_hierarchy(
            self.ctrls[1],
                self.ctrls[2], ":",
                    self.ctrls[3],
        )
        cmds.makeIdentity(self.ctrls[2], a=True)

        ik_ctrl = core.CtrlCurve(f"{self.grp_name}_IK", "Foot_IK")
        pv_ctrl = core.CtrlCurve(f"{self.grp_name}_PV", self.pv_ctrl_shape_type)
        rev_all_ctrl = core.CtrlCurve(f"{self.grp_name}_REV_All", "Pin")

        for c in [pv_ctrl, ik_ctrl, rev_all_ctrl]:
            pos, rot = core.decompose_matrix(self.ctrl_space_matrices[total_count])[:-1]
            cmds.setAttr(f"{c.parent_node}.translate", *pos)
            cmds.setAttr(f"{c.parent_node}.rotate", *rot)

            self.ctrl_instances[total_count] = c
            self.ctrls[total_count] = c.parent_node
            total_count += 1

        pos = core.decompose_matrix(self.ctrl_space_matrices[2])[0]
        cmds.setAttr(f"{self.ctrls[-7]}.translate", *pos)
        cmds.setAttr(f"{self.ctrls[-7]}.rotate", 0, 0, 0)

        self.rev_toe_ctrls = [None] * len(self.base_joints[3:-1])
        self.rev_toe_ctrl_instances = [None] * len(self.base_joints[3:-1])

        toe_ctrls = core.convert_joint_to_controller(self.src_joints[3:-1], prefix="Ctrl_REV_FK_", sr=[f"{self.src_side}_", f"{self.side}_"])
        toe_ctrls = [cmds.rename(n, f"Ctrl_{self.grp_name}_REV_FK_{s}") for n, s in zip(toe_ctrls, ["Toe", "ToeSub"])]
        for i, ctrl, name in zip(range(len(toe_ctrls)), toe_ctrls, self.joint_names[3:-1]):
            c = core.CtrlCurve(f"{name}1", "BoundingBox")

            c.reparent_shape(ctrl)
            self.rev_toe_ctrl_instances[i] = c
            self.rev_toe_ctrls[i] = c.parent_node

        for suffix, mat in zip(["Heel", "OutSide", "InSide", "ToeTip", "Toe"], self.ctrl_space_matrices[-5:]):
            ctrl = core.CtrlCurve(f"{self.grp_name}_REV_{suffix}", "Rev")
            pos, rot = core.decompose_matrix(mat)[:-1]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)
            cmds.setAttr(f"{ctrl.parent_node}.rotate", *rot)
            self.ctrl_instances[total_count] = ctrl
            self.ctrls[total_count] = ctrl.parent_node
            total_count += 1

        pos = core.decompose_matrix(self.ctrl_space_matrices[3])[0]
        cmds.setAttr(f"{self.ctrls[-1]}.translate", *pos)

        self.hds = [None] * 3

        self.ik_joints = core.convert_joint_to_controller(self.src_joints, prefix="Ikjt_", sr=[f"{self.src_side}_", f"{self.side}_"])
        self.hds[0], ef = cmds.ikHandle(sj=self.ik_joints[0], ee=self.ik_joints[2], name=f"Ikhandle_{self.grp_name}")
        self.hds[1], ef = cmds.ikHandle(sj=self.ik_joints[3], ee=self.ik_joints[4], sol="ikSCsolver", name=f"Ikhandle_{self.grp_name}_Toe")
        self.hds[2], ef = cmds.ikHandle(sj=self.ik_joints[2], ee=self.ik_joints[3], sol="ikSCsolver", name=f"Ikhandle_{self.grp_name}_Foot")
        for hd in self.hds:
            cmds.setAttr(f"{hd}.visibility", False)

        core.create_hierarchy(
            self.ctrl_grp,
                fk_ctrls[0],
                self.ik_joints[0],
                ik_ctrl.parent_node, ":",
                    self.ctrls[-5], ":",
                        self.ctrls[-4], ":",
                            self.ctrls[-3], ":",
                                self.ctrls[-2], ":",
                                    self.ctrls[-1], ":",
                                        self.hds[0], "..",
                                    toe_ctrls[0], ":", 
                                        self.hds[1],
                                        self.hds[2], "..", "..", "..", "..", "..",
                rev_all_ctrl.parent_node, "..",
                pv_ctrl.parent_node,
            )
        
        ctrls = self.ctrls[:1] + self.ctrls[-8:] + self.rev_toe_ctrls[:1]
        self.ctrl_spaces = [None] * len(ctrls)
        for i, ctrl in enumerate(ctrls):
            self.ctrl_spaces[i] = core.create_space(ctrl, parent=True)

        self.knee_line = core.connect_curve_point(f"CV_{self.grp_name}_Knee", [self.ik_joints[1], self.ctrls[-8]], parent=self.ctrl_grp, lc=self.connect_type)

        target_ik = cmds.createNode("transform", name=f"Target_{self.grp_name}_IK")
        cmds.parent(target_ik, self.ik_joints[2])
        cmds.matchTransform(target_ik, self.ctrls[2])

        target_fk = cmds.createNode("transform", name=f"Target_{self.grp_name}_FK")
        cmds.parent(target_fk, self.ctrls[2])
        cmds.matchTransform(target_fk, self.ctrls[-7])

        core.mirror_space(self.ctrl_grp)

    def set_attr(self):
        cmds.setAttr(f"{self.settings_node}.IKFK", 0)
        cmds.setAttr(f"{self.settings_node}.FK_WL", 1)
        cmds.setAttr(f"{self.settings_node}.IK_WL", 0)
        cmds.setAttr(f"{self.settings_node}.PV_WL", 1)

        core.connect_same_attr(self.ctrls[-6].replace(f"{self.side}_", f"{self.src_side}_"), self.ctrls[-6], ["ToeLiftThreshold", "ToeContactAngle"])
        cmds.setAttr(f"{self.ctrls[-6]}.ToeLiftThreshold", l=True, cb=True)
        cmds.setAttr(f"{self.ctrls[-6]}.ToeContactAngle", l=True, cb=True)

    def collect_meta_data(self):
        pass