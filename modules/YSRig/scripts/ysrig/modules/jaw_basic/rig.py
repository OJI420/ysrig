from importlib import *
from maya import cmds
from ysrig import core, rig_base
reload(core)
reload(rig_base)

class Rig(rig_base.RigBace):
    def create(self):
        self.ctrls = core.convert_joint_to_controller(self.base_joints[:-1])
        cmds.parent(self.ctrls[0], self.ctrl_grp)

        self.ctrl_instances = [None] * (self.joint_count - 1)
        ctrl = core.CtrlCurve("tmp", "Jaw")
        ctrl.reparent_shape(self.ctrls[0])
        self.ctrl_instances[0] = ctrl
        core.create_space(self.ctrls[0], parent=True)

    def connect(self):
        core.connect_matrix(self.ctrls[0], self.proxies[0], tl=True, rt=True, sc=True, lc=True)

    def lock_attributes(self):
        self.lock_attrs += [self.ctrls[0], ["scale", "visibility"]]

    def connect_visibility(self):
        if not cmds.attributeQuery("Facial", node="Controller_Root_Settings", exists=True):
            cmds.addAttr("Controller_Root_Settings", ln="Facial", at="enum", en="Hide:Show", k=True, dv=1)

        cmds.connectAttr(f"Controller_Root_Settings.Facial", f"{self.grp}.visibility")


class RigMirror(Rig):
    pass