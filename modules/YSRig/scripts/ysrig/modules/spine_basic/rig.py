from importlib import *
from maya import cmds
from ysrig import core, rig_base
reload(core)
reload(rig_base)

class Rig(rig_base.RigBace):
    def create(self):
        self.ctrls = [None] * (self.joint_count + 1)
        self.ctrl_instances = [None] * (self.joint_count + 1)

        for i, name in enumerate(self.joint_names):
            if i:
                ctrl = core.CtrlCurve(name, "Spine")
                cmds.matchTransform(ctrl.parent_node, self.base_joints[i])
                rotate = cmds.getAttr(f"{ctrl.parent_node}.rotate")[0]
                rotate = core.get_round_rotate(rotate)
                cmds.setAttr(f"{ctrl.parent_node}.rotate", *rotate)
                cmds.parent(ctrl.parent_node, self.ctrls[i - 1])

            else:
                ctrl = core.CtrlCurve(name, "Hip")
                cmds.matchTransform(ctrl.parent_node, self.base_joints[i])

            self.ctrls[i] = ctrl.parent_node
            self.ctrl_instances[i] = ctrl

        torso = core.CtrlCurve(f"{self.grp_name}_Torso", "Torso")
        cmds.matchTransform(torso.parent_node, self.base_joints[0])
        rotate = cmds.getAttr(f"{torso.parent_node}.rotate")[0]
        rotate = core.get_round_rotate(rotate)
        cmds.setAttr(f"{torso.parent_node}.rotate", *rotate)

        self.ctrls[-1] = torso.parent_node
        self.ctrl_instances[-1] = torso

        core.create_hierarchy(
            self.ctrl_grp,
                self.ctrls[-1], ":",
                    self.ctrls[0],
                    self.ctrls[1]
        )

        for ctrl in self.ctrls:
            core.create_space(ctrl, parent=True)

    def connect(self):
        for ctrl, proxy in zip(self.ctrls[2:-1], self.proxies[2:]):
            core.connect_matrix(ctrl, proxy, tl=self.translate_enabled, rt=True, sc=True, lc=self.connect_type)

        for ctrl, proxy in zip(self.ctrls[:2], self.proxies[:2]):
            core.connect_matrix(ctrl, proxy, True, rt=True, sc=True, lc=self.connect_type)

    def lock_attributes(self):
        for ctrl in self.ctrls[:-1]:
            if self.translate_enabled:
                self.lock_attrs += [ctrl, ["scale", "visibility"]]
            
            else:
                self.lock_attrs += [ctrl, ["translate", "scale", "visibility"]]

        self.lock_attrs += [self.ctrls[-1], ["scale", "visibility"]]


class RigMirror(Rig):
    pass