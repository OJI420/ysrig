from importlib import *
from maya import cmds
from ysrig import core, rig_base
reload(core)
reload(rig_base)

class Rig(rig_base.RigBace):
    def create_proxy(self):
        super().create_proxy()
        self.proxies += [cmds.mirrorJoint(self.proxies[0], myz=True, mb=True, sr=["L_", "R_"])[0]]
        self.base_joints = [self.base_joints[0], self.base_joints[0].replace("L_", "R_")]

    def create(self):
        self.ctrls = []
        self.ctrl_instances = []
        names = [jt.replace("L_", "") for jt in self.joint_names]

        for side in "LR":
            ctrl = core.CtrlCurve(f"{side}_{names[0]}", "Eye")
            self.ctrls += [ctrl.parent_node]
            self.ctrl_instances += [ctrl]
            pos = core.decompose_matrix(self.ctrl_space_matrices[0])[0]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)

            ctrl = core.CtrlCurve(f"{side}_{names[0]}_Aim", "Aim")
            ctrl.show_pivot()
            self.ctrls += [ctrl.parent_node]
            self.ctrl_instances += [ctrl]
            pos = core.decompose_matrix(self.ctrl_space_matrices[1])[0]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)

        ctrl = core.CtrlCurve(f"{self.grp_name}_Aim", "Aim_All")
        self.ctrls += [ctrl.parent_node]
        self.ctrl_instances += [ctrl]
        pos = core.decompose_matrix(self.ctrl_space_matrices[-1])[0]
        cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)

        core.create_hierarchy(
            self.ctrl_grp,
                self.ctrls[0],
                self.ctrls[2],
                self.ctrls[-1], ":",
                    self.ctrls[1],
                    self.ctrls[3],
        )

        self.ctrl_spaces = [core.create_space(ctrl, parent=True) for ctrl in self.ctrls]
        self.connect_space = [core.create_space(ctrl, parent=True, suffix="Connect") for ctrl in [self.ctrls[0], self.ctrls[2]]]

        core.mirror_space(self.ctrl_spaces[2])

        pos = core.decompose_matrix(self.ctrl_space_matrices[1])[0]
        pos[0] *= -1
        cmds.setAttr(f"{self.ctrl_spaces[3]}.translateX", pos[0])

    def connect(self):
        core.connect_matrix(self.ctrls[0], self.proxies[0], rt=True, lc=True)
        core.connect_matrix(self.ctrls[2], self.proxies[1], rt=True, lc=True)
        core.connect_aim_constraint(self.ctrls[1], self.connect_space[0], [0, 0, 1], offset=False, sk="z")
        core.connect_aim_constraint(self.ctrls[3], self.connect_space[1], [0, 0, 1], offset=False, sk="z")

    def lock_attributes(self):
        self.lock_attrs += [self.ctrls[0], ["translate", "scale"]]
        self.lock_attrs += [self.ctrls[1], ["rotate", "scale"]]
        self.lock_attrs += [self.ctrls[2], ["translate", "scale"]]
        self.lock_attrs += [self.ctrls[3], ["rotate", "scale"]]

    def connect_visibility(self):
        if not cmds.attributeQuery("Facial", node="Controller_Root_Settings", exists=True):
            cmds.addAttr("Controller_Root_Settings", ln="Facial", at="enum", en="Hide:Show", k=True, dv=1)

        cmds.connectAttr(f"Controller_Root_Settings.Facial", f"{self.grp}.visibility")


class RigMirror(Rig):
    pass