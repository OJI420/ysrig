from importlib import *
from maya import cmds
from ysrig import core, rig_base
reload(core)
reload(rig_base)

class Rig(rig_base.RigBace):
    def create_proxy(self):
        super().create_proxy()
        core.create_hierarchy(
            self.grp,
                self.proxies[2],
                self.proxies[3],
        )
        self.proxies += cmds.mirrorJoint(self.proxies[0], myz=True, mb=True, sr=["L_", "R_"])
        self.proxies += cmds.mirrorJoint(self.proxies[2], myz=True, mb=True, sr=["L_", "R_"])
        self.proxies += cmds.mirrorJoint(self.proxies[3], myz=True, mb=True, sr=["L_", "R_"])
        self.base_joints += [jt.replace("L_", "R_") for jt in self.base_joints]

    def create(self):
        self.ctrls = []
        self.ctrl_instances = []
        self.ctrl_spaces = []
        names = [jt.replace("L_", "") for jt in self.joint_names]

        for side in "LR":
            ctrl = core.CtrlCurve(f"{side}_{names[0]}", "Eye")
            self.ctrls += [ctrl.parent_node]
            self.ctrl_instances += [ctrl]
            pos = core.decompose_matrix(self.ctrl_space_matrices[0])[0]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)

            ctrl = core.CtrlCurve(f"{side}_{names[2]}", "Eyelid")
            ctrl.set_rotate([-20, 0, 0])
            self.ctrls += [ctrl.parent_node]
            self.ctrl_instances += [ctrl]
            pos, rot = core.decompose_matrix(self.ctrl_space_matrices[1])[:-1]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)
            cmds.setAttr(f"{ctrl.parent_node}.rotate", *rot)

            ctrl = core.CtrlCurve(f"{side}_{names[3]}", "Eyelid")
            ctrl.set_rotate([-20, 0, 0])
            ctrl.set_rotate([0, 0, 180])
            self.ctrls += [ctrl.parent_node]
            self.ctrl_instances += [ctrl]
            pos, rot = core.decompose_matrix(self.ctrl_space_matrices[2])[:-1]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)
            cmds.setAttr(f"{ctrl.parent_node}.rotate", *rot)

            ctrl = core.CtrlCurve(f"{side}_{names[0]}_UI", "Face_UI")
            ctrl.set_display_type(1)
            ctrl.set_scale(3, 1, 1)
            self.ctrls += [ctrl.parent_node]
            self.ctrl_instances += [ctrl]
            pos = core.decompose_matrix(self.ctrl_space_matrices[3])[0]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)

            # 目のUI
            for i in range(3):
                s = core.CtrlCurve("tmp", "Scale")
                s.set_display_type(2)
                s.set_translate([i - 1, 0, 0])
                s.reparent_shape(ctrl.parent_node)

            for i, name in enumerate(["OpenClose", "ClosePos", "Scale"]):
                s = core.CtrlCurve(f"{side}_{names[0]}_{name}", f"Pointer_{i + 1}")
                self.ctrls += [s.parent_node]
                self.ctrl_instances += [s]
                pos = core.decompose_matrix(self.ctrl_space_matrices[i + 4])[0]
                cmds.setAttr(f"{s.parent_node}.translate", *pos)
                cmds.parent(s.parent_node, ctrl.parent_node)

            ctrl = core.CtrlCurve(f"{side}_{names[0]}_Aim", "Aim")
            ctrl.show_pivot()
            self.ctrls += [ctrl.parent_node]
            self.ctrl_instances += [ctrl]
            pos = core.decompose_matrix(self.ctrl_space_matrices[7])[0]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)

        ctrl = core.CtrlCurve(f"{self.grp_name}_Aim_All", "Aim_All")
        self.ctrls += [ctrl.parent_node]
        self.ctrl_instances += [ctrl]
        pos = core.decompose_matrix(self.ctrl_space_matrices[16])[0]
        cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)

        core.create_hierarchy(
            self.ctrl_grp,
                self.ctrls[0],
                self.ctrls[1],
                self.ctrls[2],
                self.ctrls[3],
                self.ctrls[8],
                self.ctrls[9],
                self.ctrls[10],
                self.ctrls[11],
                self.ctrls[16], ":",
                    self.ctrls[7],
                    self.ctrls[15],
        )

        self.ctrl_spaces = [core.create_space(ctrl, parent=True) for ctrl in self.ctrls]
        self.eye_connect_spaces = [core.create_space(ctrl, parent=True, suffix="Connect") for ctrl in [self.ctrls[0], self.ctrls[8]]]
        self.connect_spaces1 = [core.create_space(ctrl, parent=True, suffix="Connect_01") for ctrl in self.ctrls[1:3] + self.ctrls[9:11]]
        self.connect_spaces2 = [core.create_space(ctrl, parent=True, suffix="Connect_02") for ctrl in self.ctrls[1:3] + self.ctrls[9:11]]

        for space in self.ctrl_spaces[8:12]:
            core.mirror_space(space)

        pos = core.decompose_matrix(self.ctrl_space_matrices[7])[0]
        pos[0] *= -1
        cmds.setAttr(f"{self.ctrl_spaces[15]}.translateX", pos[0])

        """
        self.ctrls
        [0] [-17] -> Ctrl_L_Eye
        [1] [-16] -> Ctrl_L_Eyelid_Top
        [2] [-15] -> Ctrl_L_Eyelid_Bottom
        [3] [-14] -> Ctrl_L_Eye_UI
        [4] [-13] -> Ctrl_L_Eye_OpenClose
        [5] [-12] -> Ctrl_L_Eye_ClosePos
        [6] [-11] -> Ctrl_L_Eye_Scale
        [7] [-10] -> Ctrl_L_Eye_Aim
        [8] [-9] -> Ctrl_R_Eye
        [9] [-8] -> Ctrl_R_Eyelid_Top
        [10] [-7] -> Ctrl_R_Eyelid_Bottom
        [11] [-6] -> Ctrl_R_Eye_UI
        [12] [-5] -> Ctrl_R_Eye_OpenClose
        [13] [-4] -> Ctrl_R_Eye_ClosePos
        [14] [-3] -> Ctrl_R_Eye_Scale
        [15] [-2] -> Ctrl_R_Eye_Aim
        [16] [-1] -> Ctrl_Eyes_Aim_All
        """

    def set_shape_transform(self):
        ctrl_instances = self.ctrl_instances[:3] + self.ctrl_instances[7:11] + self.ctrl_instances[15:]
        ctrl_matrices = self.ctrl_matrices[:3] + self.ctrl_matrices[7:11] + self.ctrl_matrices[15:]
        ctrl_space_matrices = self.ctrl_space_matrices[:3] + self.ctrl_space_matrices[7:11] + self.ctrl_space_matrices[15:]

        for ctrl, ctrl_mat, spase_mat in zip(ctrl_instances, ctrl_matrices, ctrl_space_matrices):
            offset_scale = core.decompose_matrix(spase_mat)[2]
            ctrl.set_matrix(ctrl_mat, offset_scale=offset_scale)
            ctrl.set_width(self.ctrl_line_width)

        ctrl_instances = [self.ctrl_instances[3], self.ctrl_instances[11]]
        ctrl_matrices = [self.ctrl_matrices[3], self.ctrl_matrices[11]]
        ctrl_space_matrices = [self.ctrl_space_matrices[3], self.ctrl_space_matrices[11]]

        for ctrl, ctrl_mat, spase_mat in zip(ctrl_instances, ctrl_matrices, ctrl_space_matrices):
            scale = core.decompose_matrix(spase_mat)[2]
            core.set_shape_matrix(ctrl.parent_node, [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0], offset_scale=scale)
            core.set_curve_width(ctrl.parent_node, self.ctrl_line_width)
            sscl = core.decompose_matrix(spase_mat)[-1]
            cpos, crot, cscl = core.decompose_matrix(ctrl_mat)
            pos = [s * p for s, p in zip(sscl, cpos)]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)
            cmds.setAttr(f"{ctrl.parent_node}.rotate", *crot)
            cmds.setAttr(f"{ctrl.parent_node}.scale", *cscl)

        ctrl_instances = self.ctrl_instances[4:7] + self.ctrl_instances[12:15]
        ctrl_matrices = self.ctrl_matrices[4:7] + self.ctrl_matrices[12:15]
        ctrl_space_matrices = self.ctrl_space_matrices[4:7] + self.ctrl_space_matrices[12:15]
        for ctrl, ctrl_mat, spase_mat in zip(ctrl_instances, ctrl_matrices, ctrl_space_matrices):
            space = cmds.listRelatives(ctrl.parent_node, p=True)[0]
            scl = core.decompose_matrix(spase_mat)[-1]
            cmds.setAttr(f"{space}.scale", *scl)

    def add_settings(self):
        for ctrl in [self.ctrls[7], self.ctrls[15]]:
            cmds.addAttr(ctrl, ln="________________", at="enum", en="Settings", k=True)
            cmds.setAttr(f"{ctrl}.________________", l=True)
            cmds.addAttr(ctrl, ln="EyelidPitchFollowWeight", at="double", min=0, max=1, dv=0.5, k=True)
            cmds.addAttr(ctrl, ln="EyelidYawFollowWeight", at="double", min=0, max=1, dv=0.25, k=True)

        for ctrl in [self.ctrls[4], self.ctrls[12]]:
            cmds.addAttr(ctrl, ln="________________", at="enum", en="Settings", k=True)
            cmds.setAttr(f"{ctrl}.________________", l=True)
            cmds.addAttr(ctrl, ln="EyelidCloseAngle", at="double", min=0, max=360, dv=40, k=True)

        for ctrl in [self.ctrls[6], self.ctrls[14]]:
            cmds.addAttr(ctrl, ln="________________", at="enum", en="Settings", k=True)
            cmds.setAttr(f"{ctrl}.________________", l=True)
            cmds.addAttr(ctrl, ln="PupilDepthWeight", at="double", dv=1, k=True)

    def connect(self):
        for i, side in enumerate("LR"):
            core.connect_matrix(self.ctrls[8 * i], self.proxies[4 * i], rt=True, lc=True)
            core.connect_matrix(self.ctrls[8 * i + 1], self.proxies[4 * i + 2], rt=True, lc=True)
            core.connect_matrix(self.ctrls[8 * i + 2], self.proxies[4 * i + 3], rt=True, lc=True)
            core.connect_aim_constraint(self.ctrls[8 * i + 7], self.eye_connect_spaces[i], [0, 0, 1], offset=False, sk="z")
            # 瞼の眼球への追従
            core.connect_float_math(name=f"Fm_{side}_{self.grp_name}_EyelidPitchFollow", operation=2,
                                    fa=f"{self.eye_connect_spaces[i]}.rotateX", fb=f"{self.ctrls[8 * i + 7]}.EyelidPitchFollowWeight",
                                    out=[f"{self.connect_spaces1[2 * i]}.rotateX", f"{self.connect_spaces1[2 * i + 1]}.rotateX"])

            core.connect_float_math(name=f"Fm_{side}_{self.grp_name}_EyelidYawFollow", operation=2,
                                    fa=f"{self.eye_connect_spaces[i]}.rotateY", fb=f"{self.ctrls[8 * i + 7]}.EyelidYawFollowWeight",
                                    out=[f"{self.connect_spaces1[2 * i]}.rotateY", f"{self.connect_spaces1[2 * i + 1]}.rotateY"])

            # 目閉じ
            fm1 = core.connect_float_math(name=f"Fm_{side}_{self.grp_name}_Eyelid_OC_01", operation=0, fa=f"{self.ctrls[8 * i + 4]}.translateY", fb=-1)
            fm2 = core.connect_float_math(name=f"Fm_{side}_{self.grp_name}_Eyelid_OC_02", operation=2, fa=f"{fm1}.outFloat", fb=-1)
            fm3 = core.connect_float_math(name=f"Fm_{side}_{self.grp_name}_Eyelid_OC_03", operation=3, fa=f"{self.ctrls[8 * i + 4]}.EyelidCloseAngle", fb=4)
            fm4 = core.connect_float_math(name=f"Fm_{side}_{self.grp_name}_Eyelid_OC_04", operation=2, fa=f"{fm2}.outFloat", fb=f"{fm3}.outFloat")

            # 目閉じポイント
            fm5 = core.connect_float_math(name=f"Fm_{side}_{self.grp_name}_Eyelid_CP_01", operation=0, fa=f"{self.ctrls[8 * i + 5]}.translateY", fb=-1)
            fm6 = core.connect_float_math(name=f"Fm_{side}_{self.grp_name}_Eyelid_CP_02", operation=2, fa=f"{fm5}.outFloat", fb=-1)
            fm7 = core.connect_float_math(name=f"Fm_{side}_{self.grp_name}_Eyelid_CP_03", operation=2, fa=f"{self.ctrls[8 * i + 5]}.translateY", fb=-1)
            fm8 = core.connect_float_math(name=f"Fm_{side}_{self.grp_name}_Eyelid_CP_04", operation=0, fa=f"{fm7}.outFloat", fb=-1)

            core.connect_float_math(name=f"Fm_{self.connect_spaces2[2 * i]}", operation=2, fa=f"{fm4}.outFloat", fb=f"{fm6}.outFloat", out=[f"{self.connect_spaces2[2 * i]}.rotateX"])
            core.connect_float_math(name=f"Fm_{self.connect_spaces2[2 * i + 1]}", operation=2, fa=f"{fm4}.outFloat", fb=f"{fm8}.outFloat", out=[f"{self.connect_spaces2[2 * i + 1]}.rotateX"])

            # 瞳の大きさ
            fm1 = core.connect_float_math(name=f"Fm_{self.proxies[4 * i + 1]}_01", operation=0, fa=f"{self.ctrls[8 * i + 6]}.translateY", fb=1, out=[f"{self.proxies[4 * i + 1]}.scale:XYZ"])
            fm2 = core.connect_float_math(name=f"Fm_{self.proxies[4 * i + 1]}_02", operation=2, fa=f"{self.ctrls[8 * i + 6]}.translateY", fb=f"{self.ctrls[8 * i + 6]}.PupilDepthWeight")
            fm3 = core.connect_float_math(name=f"Fm_{self.proxies[4 * i + 1]}_03", operation=0, fa=f"{fm2}.outFloat", fb=1, out=[f"{self.proxies[4 * i + 1]}.scaleZ"])

    def set_attr(self):
        cmds.setAttr(f"{self.ctrls[4]}.translateY", 1)
        cmds.setAttr(f"{self.ctrls[12]}.translateY", 1)
        cmds.setAttr(f"{self.ctrls[5]}.translateY", -0.5)
        cmds.setAttr(f"{self.ctrls[13]}.translateY", -0.5)

        if not cmds.attributeQuery("EyelidPitchFollowWeight", node=self.meta_node, exists=True):
            return

        for i in range(2):
            attrs = ["EyelidPitchFollowWeight", "EyelidYawFollowWeight", "EyelidCloseAngle", "PupilDepthWeight"]
            ctrls = [self.ctrls[8 * i + 7], self.ctrls[8 * i + 7], self.ctrls[8 * i + 4], self.ctrls[8 * i + 6]]
            for attr, ctrl in zip(attrs, ctrls):
                value = cmds.getAttr(f"{self.meta_node}.{attr}[{i}]")
                cmds.setAttr(f"{ctrl}.{attr}", value, k=False, cb=True)

    def lock_attributes(self):
        for i in range(2):
            for ctrl in self.ctrls[8*i:8*i+3]:
                self.lock_attrs += [ctrl, ["translate", "scale"]]

            for ctrl in self.ctrls[8*i+4:8*i+7]:
                self.lock_attrs += [ctrl, ["tx", "tz", "rotate", "scale"]]
                cmds.transformLimits(ctrl, ty=[-1, 1], ety=[1, 1])

            self.lock_attrs += [self.ctrls[8*i+7], ["rotate", "scale"]]

    def collect_meta_data(self):
        self.meta_data["EyelidPitchFollowWeight"] = core.compose_attr_paths(nodes=[self.ctrls[7], self.ctrls[15]], attr="EyelidPitchFollowWeight", multi=True)
        self.meta_data["EyelidYawFollowWeight"] = core.compose_attr_paths(nodes=[self.ctrls[7], self.ctrls[15]], attr="EyelidYawFollowWeight", multi=True)
        self.meta_data["EyelidCloseAngle"] = core.compose_attr_paths(nodes=[self.ctrls[4], self.ctrls[12]], attr="EyelidCloseAngle", multi=True)
        self.meta_data["PupilDepthWeight"] = core.compose_attr_paths(nodes=[self.ctrls[6], self.ctrls[14]], attr="PupilDepthWeight", multi=True)

    def connect_visibility(self):
        if not cmds.attributeQuery("Facial", node="Controller_Root_Settings", exists=True):
            cmds.addAttr("Controller_Root_Settings", ln="Facial", at="enum", en="Hide:Show", k=True, dv=1)

        cmds.connectAttr(f"Controller_Root_Settings.Facial", f"{self.grp}.visibility")


class RigMirror(Rig):
    pass