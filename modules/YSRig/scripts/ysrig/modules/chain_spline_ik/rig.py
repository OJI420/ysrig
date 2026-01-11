from importlib import *
from maya import cmds
from ysrig import core, rig_base
reload(core)
reload(rig_base)

All_CTRL_SHAPE = "Triangle"

class Rig(rig_base.RigBace):
    def setup(self):
        self.ctrl_shape_type = core.get_enum_attribute(self.meta_node, "ControllrShapeType")
        self.ctrl_count = cmds.getAttr(f"{self.meta_node}.ControllrCount")

    def create(self):
        self.ik_jt = core.convert_joint_to_controller(self.base_joints, prefix="Ikjt_")
        self.ik_curve = core.build_curve_from_joints(self.ik_jt, name=f"CV_{self.grp_name}")
        cv_space = core.create_space(self.ik_curve, parent=True)
        core.rebuild_curve(self.ik_curve, self.ctrl_count)
        pos_list = core.get_curve_points_pos(self.ik_curve)
        names = core.create_numbered_names(self.grp_name, self.ctrl_count, gb=False)

        self.ik_hd = cmds.ikHandle(sj=self.ik_jt[0], ee=self.ik_jt[-1], c=self.ik_curve, name=f"Ikhandle_{self.grp_name}", sol="ikSplineSolver", ccv=False, pcv=False)[0]
        ik_hd_space = core.create_space(self.ik_hd, parent=True)
        cmds.makeIdentity(self.ik_jt, a=True)

        self.cluster = core.cluster_curve(self.ik_curve)

        self.ctrl_instances = [None] * (self.ctrl_count + 1)
        self.ctrls = [None] * (self.ctrl_count + 1)

        pos, rot = core.decompose_matrix(self.ctrl_space_matrices[-1])[:-1]
        all_ctrl = core.CtrlCurve(f"{self.grp_name}_All", All_CTRL_SHAPE)
        cmds.setAttr(f"{all_ctrl.parent_node}.translate", *pos)
        cmds.setAttr(f"{all_ctrl.parent_node}.rotate", *rot)

        all_ctrl_space = core.create_space(all_ctrl.parent_node, parent=True)
        core.create_hierarchy(
            self.ctrl_grp,
                self.ik_jt[0],
                cv_space,
                all_ctrl_space,
                ik_hd_space
        )

        for i, name in enumerate(names):
            ctrl = core.CtrlCurve(name, self.ctrl_shape_type)
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos_list[i])
            cmds.setAttr(f"{ctrl.parent_node}.rotate", *rot)

            space = core.create_space(ctrl.parent_node, parent=True)
            core.create_hierarchy(
                all_ctrl.parent_node,
                    space
            )

            self.ctrl_instances[i] = ctrl
            self.ctrls[i] = ctrl.parent_node

        self.ctrl_instances[-1] = all_ctrl
        self.ctrls[-1] = all_ctrl.parent_node

        cluster_space = cmds.rename(core.create_space(self.cluster[0]), f"{self.grp_name}_Cluster_Group")
        cmds.matchTransform(cv_space, cluster_space, pos=True)
        cmds.parent(cluster_space, self.ctrl_grp)

        for ct in self.cluster:
            cmds.setAttr(f"{ct}.visibility", False)
            core.create_hierarchy(
                cluster_space,
                    ct
            )

    def add_settings(self):
        cmds.addAttr(self.settings_node, ln="Roll", at="double", k=True)
        cmds.addAttr(self.settings_node, ln="Twist", at="double", k=True)

    def connect(self):
        for proxy, ik_jt in zip(self.proxies, self.ik_jt):
            core.connect_matrix(ik_jt, proxy, tl=True, rt=True, lc=self.connect_type)
        for ctrl, cluster in zip(self.ctrls, self.cluster):
            core.connect_parent_constraint(ctrl, cluster)

        cmds.connectAttr(f"{self.settings_node}.Roll", f"{self.ik_hd}.roll")
        cmds.connectAttr(f"{self.settings_node}.Twist", f"{self.ik_hd}.twist")

    def lock_attributes(self):
        for ctrl in self.ctrls[:-1]:
            self.lock_attrs += [ctrl, ["scale", "rotate", "visibility"]]

        self.lock_attrs += [self.ctrls[-1], ["scale", "visibility"]]
        cmds.setAttr(f"{self.ik_curve}.visibility", False)
        cmds.setAttr(f"{self.ik_hd}.visibility", False)


class RigMirror(Rig):
    def _setup(self, meta_node):
        super()._setup(meta_node)
        self.src_joints = [f"JT_{name}" for name in self.joint_names]
        self.src_side = self.side[:]
        self.build, self.side, self.grp_name, self.joint_names = rig_base.get_mirror_names(self.side, self.grp_name, self.joint_names)

    def create(self):
        self.ik_jt = core.convert_joint_to_controller(self.src_joints, prefix="Ikjt_", sr=[f"{self.src_side}_", f"{self.side}_"])
        self.ik_curve = core.build_curve_from_joints(self.ik_jt, name=f"CV_{self.grp_name}")
        cv_space = core.create_space(self.ik_curve, parent=True)
        core.rebuild_curve(self.ik_curve, self.ctrl_count)
        pos_list = core.get_curve_points_pos(self.ik_curve)
        names = core.create_numbered_names(self.grp_name, self.ctrl_count, gb=False)

        self.ik_hd = cmds.ikHandle(sj=self.ik_jt[0], ee=self.ik_jt[-1], c=self.ik_curve, name=f"Ikhandle_{self.grp_name}", sol="ikSplineSolver", ccv=False, pcv=False)[0]
        ik_hd_space = core.create_space(self.ik_hd, parent=True)
        cmds.makeIdentity(self.ik_jt, a=True)

        self.cluster = core.cluster_curve(self.ik_curve)

        self.ctrl_instances = [None] * (self.ctrl_count + 1)
        self.ctrls = [None] * (self.ctrl_count + 1)

        pos, rot = core.decompose_matrix(self.ctrl_space_matrices[-1])[:-1]
        all_ctrl = core.CtrlCurve(f"{self.grp_name}_All", All_CTRL_SHAPE)
        cmds.setAttr(f"{all_ctrl.parent_node}.translate", *pos)
        cmds.setAttr(f"{all_ctrl.parent_node}.rotate", *rot)

        all_ctrl_space = core.create_space(all_ctrl.parent_node, parent=True)
        core.create_hierarchy(
            self.ctrl_grp,
                self.ik_jt[0],
                cv_space,
                all_ctrl_space,
                ik_hd_space
        )

        for i, name in enumerate(names):
            ctrl = core.CtrlCurve(name, self.ctrl_shape_type)
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos_list[i])
            cmds.setAttr(f"{ctrl.parent_node}.rotate", *rot)

            space = core.create_space(ctrl.parent_node, parent=True)
            core.create_hierarchy(
                all_ctrl.parent_node,
                    space
            )

            self.ctrl_instances[i] = ctrl
            self.ctrls[i] = ctrl.parent_node

        self.ctrl_instances[-1] = all_ctrl
        self.ctrls[-1] = all_ctrl.parent_node

        cluster_space = cmds.rename(core.create_space(self.cluster[0]), f"{self.grp_name}_Cluster_Group")
        cmds.matchTransform(cv_space, cluster_space, pos=True)
        cmds.parent(cluster_space, self.ctrl_grp)

        for ct in self.cluster:
            cmds.setAttr(f"{ct}.visibility", False)
            core.create_hierarchy(
                cluster_space,
                    ct
            )

        core.mirror_space(self.ctrl_grp)
