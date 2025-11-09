from importlib import *
from maya import cmds
from ysrig import core, rig_base
reload(core)
reload(rig_base)

class Rig(rig_base.RigBace):
    def setup(self):
        self.ctrl_shape_type = core.get_enum_attribute(self.meta_node, "ControllrShapeType")

    def create(self):
        self.ctrls = core.convert_joint_to_controller(self.base_joints[:-1])
        cmds.parent(self.ctrls[0], self.ctrl_grp)

        self.ctrl_instances = [None] * (self.joint_count - 1)
        for i, name in enumerate(self.joint_names[:-1]):
            ctrl = core.CtrlCurve(f"{name}1", self.ctrl_shape_type)
            ctrl.reparent_shape(self.ctrls[i])
            self.ctrl_instances[i] = ctrl
            if self.translate_enabled:
                core.create_space(self.ctrls[i], parent=True)

    def connect(self):
        for ctrl, proxy in zip(self.ctrls, self.proxies):
            core.connect_matrix(ctrl, proxy, tl=self.translate_enabled, rt=True, sc=True, lc=self.connect_type)

    def lock_attributes(self):
        for ctrl in self.ctrls:
            if self.translate_enabled:
                self.lock_attrs += [ctrl, ["scale", "visibility"]]
            
            else:
                self.lock_attrs += [ctrl, ["translate", "scale", "visibility"]]


class RigMirror(Rig):
    def _setup(self, meta_node):
        super()._setup(meta_node)
        self.src_joints = [f"JT_{name}" for name in self.joint_names]
        self.src_side = self.side[:]
        self.build, self.side, self.grp_name, self.joint_names = rig_base.get_mirror_names(self.side, self.grp_name, self.joint_names)

    def create(self):
        self.ctrls = core.convert_joint_to_controller(self.src_joints[:-1], sr=[f"{self.src_side}_", f"{self.side}_"])
        cmds.parent(self.ctrls[0], self.ctrl_grp)

        self.ctrl_instances = [None] * (self.joint_count - 1)
        for i, name in enumerate(self.joint_names[:-1]):
            ctrl = core.CtrlCurve(f"{name}1", self.ctrl_shape_type)
            ctrl.reparent_shape(self.ctrls[i])
            self.ctrl_instances[i] = ctrl
            if self.translate_enabled:
                core.create_space(self.ctrls[i], parent=True)

        core.mirror_space(self.ctrl_grp)
