from importlib import *
from maya import cmds
from ysrig import core, rig_base
reload(core)
reload(rig_base)

class Rig(rig_base.RigBace):
    def setup(self):
        self.ik_ctrl_shape_type = core.get_enum_attribute(self.meta_node, "IKControllrShapeType")
        self.pv_ctrl_shape_type = core.get_enum_attribute(self.meta_node, "PVControllrShapeType")

    def create(self):
        self.ctrls = [None] * 6
        self.ctrl_instances = [None] * 6
        self.ctrl_spaces = [None] * 6

        fk_ctrls = core.convert_joint_to_controller(self.base_joints[:-1])
        for i, ctrl, name in zip(range(4), fk_ctrls, self.joint_names):
            if i:
                c = core.CtrlCurve(f"{name}1", "BoundingBox")

            else:
                c = core.CtrlCurve(f"{name}1", "Shoulder")

            c.reparent_shape(ctrl)
            self.ctrl_instances[i] = c
            self.ctrls[i] = c.parent_node

        ik_ctrl = core.CtrlCurve(f"{self.grp_name}_IK", self.ik_ctrl_shape_type)
        pv_ctrl = core.CtrlCurve(f"{self.grp_name}_PV", self.pv_ctrl_shape_type)
        self.ctrl_instances[4:] = [ik_ctrl, pv_ctrl]
        self.ctrls[4:] = [ik_ctrl.parent_node, pv_ctrl.parent_node]

        pos = core.decompose_matrix(self.ctrl_space_matrices[4])[0]
        cmds.setAttr(f"{self.ctrls[4]}.translate", *pos)
        pos = core.decompose_matrix(self.ctrl_space_matrices[5])[0]
        cmds.setAttr(f"{self.ctrls[5]}.translate", *pos)

        self.ik_joints = core.convert_joint_to_controller(self.base_joints[1:4], prefix="Ikjt_")
        self.hd, ef = cmds.ikHandle(sj=self.ik_joints[0], ee=self.ik_joints[2], name=f"Ikhandle_{self.grp_name}")
        cmds.setAttr(f"{self.hd}.visibility", False)

        cmds.parent(self.ctrls[1], w=True)
        cmds.parent(self.ctrls[3], self.proxies[2])
        core.create_hierarchy(
            self.ctrl_grp,
                self.ctrls[0], ":",
                    self.ctrls[1],
                    self.ik_joints[0],
                    self.ctrls[4],
                    self.ctrls[5],
                    self.hd
            )

        for i, ctrl in enumerate(self.ctrls[:2] + self.ctrls[3:] + [self.hd]):
            self.ctrl_spaces[i] = core.create_space(ctrl, parent=True)

        self.elbow_line = core.connect_curve_point(f"CV_{self.grp_name}_Elbow", [self.ik_joints[1], self.ctrls[5]], parent=self.ctrl_grp, lc=self.connect_type)

        """
        self.ctrls
            0 : 肩
            1 : 上腕
            2 : 前腕
            3 : 手首
            4 : IK
            5 : PV
        
        self.ctrl_spaces
            0 : 肩
            1 : FK
            2 : 手首
            3 : IK
            4 : PV
            5 : IKハンドル
        """

    def add_settings(self):
        cmds.addAttr(self.settings_node, ln="IKFK", at="enum", en="IK:FK:", k=True)
        cmds.addAttr(self.settings_node, ln="FK_WL", at="enum", en="World:Local:", k=True)
        cmds.addAttr(self.settings_node, ln="IK_WL", at="enum", en="World:Local:", k=True)
        cmds.addAttr(self.settings_node, ln="PV_WL", at="enum", en="World:Local:", k=True)
        cmds.addAttr(self.settings_node, ln="Hand_WL", at="enum", en="World:Local:", k=True)

    def connect(self):
        core.connect_matrix(self.ctrls[0], self.proxies[0], tl=True, rt=True, lc=self.connect_type)
        core.connect_matrix(self.ctrls[3], self.proxies[3], rt=True, lc=self.connect_type)
        core.connect_matrix(self.ctrls[4], self.ctrl_spaces[5], tl=True, lc=self.connect_type)
        pv_dv = core.connect_matrix(self.ctrls[4], self.ctrl_spaces[4], rt=True, lc=self.connect_type, suffix="_Local")[1]
        cmds.poleVectorConstraint(self.ctrls[5], self.hd)

        # IKFK
        core.connect_switch_attr(
            f"{self.settings_node}.IKFK",
            core.compose_attr_paths(self.ctrls[1:3], "visibility", multi=True),
            core.compose_attr_paths(self.ctrls[4:] + [self.elbow_line], "visibility", multi=True)
        )
        for px, ik, fk in zip(self.proxies[1:3], self.ik_joints[:-1], self.ctrls[1:3]):
            dv = core.connect_matrix(fk, px, rt=True, lc=self.connect_type)[1]
            core.connect_pair_blend(weight=f"{self.settings_node}.IKFK", in_rt1=f"{ik}.rotate", in_rt2=f"{dv}.outputRotate", out_rt=f"{px}.rotate:XYZ")

        # FK WL
        dv = core.connect_matrix(self.ROOT_OFFSET_CTRL, self.ctrl_spaces[1], rt=True, lc=False)[1]
        core.connect_pair_blend(weight=f"{self.settings_node}.FK_WL", in_rt1=f"{dv}.outputRotate", in_rt2=f"{dv}.outputRotate!", out_rt=f"{self.ctrl_spaces[1]}.rotate:XYZ")

        # IK WL
        dv = core.connect_matrix(self.ROOT_OFFSET_CTRL, self.ctrl_spaces[3], tl=True, rt=True, lc=False)[1]
        core.connect_pair_blend(weight=f"{self.settings_node}.IK_WL", in_tl1=f"{dv}.outputTranslate", in_tl2=f"{dv}.outputTranslate!", in_rt1=f"{dv}.outputRotate", in_rt2=f"{dv}.outputRotate!",
                                out_tl=f"{self.ctrl_spaces[3]}.translate:XYZ", out_rt=f"{self.ctrl_spaces[3]}.rotate:XYZ")

        # PV WL
        dv = core.connect_matrix(self.ROOT_OFFSET_CTRL, self.ctrl_spaces[4], tl=True, lc=False, suffix="_World")[1]
        core.connect_pair_blend(weight=f"{self.settings_node}.PV_WL", in_tl1=f"{dv}.outputTranslate", in_tl2=f"{pv_dv}.outputTranslate", out_tl=f"{self.ctrl_spaces[4]}.translate:XYZ")

        # Hand WL
        dv = core.connect_matrix(self.ROOT_OFFSET_CTRL, self.ctrl_spaces[2], rt=True, lc=False)[1]
        core.connect_pair_blend(weight=f"{self.settings_node}.Hand_WL", in_rt1=f"{dv}.outputRotate", in_rt2=f"{dv}.outputRotate!", out_rt=f"{self.ctrl_spaces[2]}.rotate:XYZ")

        # IKの伸び切りチェッカー
        core.connect_ik_stretch_warning([self.ik_joints[0], self.hd], cmds.getAttr(f"{self.ik_joints[1]}.tx") * 2, shapes=[self.ctrl_instances[4].shape_node, self.ctrl_instances[5].shape_node])


    def set_attr(self):
        cmds.setAttr(f"{self.settings_node}.IKFK", 1)
        cmds.setAttr(f"{self.settings_node}.FK_WL", 1)
        cmds.setAttr(f"{self.settings_node}.IK_WL", 1)
        cmds.setAttr(f"{self.settings_node}.PV_WL", 1)
        cmds.setAttr(f"{self.settings_node}.Hand_WL", 1)

    def lock_attributes(self):
        for ctrl in self.ctrls:
            self.lock_attrs += [ctrl, ["scale", "visibility"]]

        self.lock_attrs += [
            self.ctrls[1], ["translate"],
            self.ctrls[2], ["translate", "rx", "ry"],
            self.ctrls[3], ["translate"],
            self.ctrls[4], ["rotate"],
            self.ctrls[5], ["rotate"]
            ]

        elbow_orient = cmds.getAttr(f"{self.ctrls[2]}.jointOrientZ")
        elbow_orient *= -1
        cmds.transformLimits(self.ctrls[2], rz=[elbow_orient, 0], erz=[1, 0])


class RigMirror(Rig):
    def _setup(self, meta_node):
        super()._setup(meta_node)
        self.src_joints = [f"JT_{name}" for name in self.joint_names]
        self.src_side = self.side[:]
        self.build, self.side, self.grp_name, self.joint_names = rig_base.get_mirror_names(self.side, self.grp_name, self.joint_names)

    def create(self):
        self.ctrls = [None] * 6
        self.ctrl_instances = [None] * 6
        self.ctrl_spaces = [None] * 6

        fk_ctrls = core.convert_joint_to_controller(self.src_joints[:-1], sr=[f"{self.src_side}_", f"{self.side}_"])
        for i, ctrl, name in zip(range(4), fk_ctrls, self.joint_names):
            if i:
                c = core.CtrlCurve(f"{name}1", "BoundingBox")

            else:
                c = core.CtrlCurve(f"{name}1", "Shoulder")

            c.reparent_shape(ctrl)
            self.ctrl_instances[i] = c
            self.ctrls[i] = c.parent_node

        ik_ctrl = core.CtrlCurve(f"{self.grp_name}_IK", self.ik_ctrl_shape_type)
        pv_ctrl = core.CtrlCurve(f"{self.grp_name}_PV", self.pv_ctrl_shape_type)
        self.ctrl_instances[4:] = [ik_ctrl, pv_ctrl]
        self.ctrls[4:] = [ik_ctrl.parent_node, pv_ctrl.parent_node]

        pos = core.decompose_matrix(self.ctrl_space_matrices[4])[0]
        cmds.setAttr(f"{self.ctrls[4]}.translate", *pos)
        pos = core.decompose_matrix(self.ctrl_space_matrices[5])[0]
        cmds.setAttr(f"{self.ctrls[5]}.translate", *pos)

        self.ik_joints = core.convert_joint_to_controller(self.src_joints[1:4], prefix="Ikjt_", sr=[f"{self.src_side}_", f"{self.side}_"])
        self.hd, ef = cmds.ikHandle(sj=self.ik_joints[0], ee=self.ik_joints[2], name=f"Ikhandle_{self.grp_name}")
        cmds.setAttr(f"{self.hd}.visibility", False)

        cmds.parent(self.ctrls[1], w=True)
        cmds.parent(self.ctrls[3], self.proxies[2])
        core.create_hierarchy(
            self.ctrl_grp,
                self.ctrls[0], ":",
                    self.ctrls[1],
                    self.ik_joints[0],
                    self.ctrls[4],
                    self.ctrls[5],
                    self.hd
            )

        for i, ctrl in enumerate(self.ctrls[:2] + self.ctrls[3:] + [self.hd]):
            self.ctrl_spaces[i] = core.create_space(ctrl, parent=True)

        self.elbow_line = core.connect_curve_point(f"CV_{self.grp_name}_Elbow", [self.ik_joints[1], self.ctrls[5]], parent=self.ctrl_grp, lc=self.connect_type)

        core.mirror_space(self.ctrl_grp)
        core.mirror_space(self.ctrl_spaces[2])
