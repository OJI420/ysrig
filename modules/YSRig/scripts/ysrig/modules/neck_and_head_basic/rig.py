from importlib import *
from maya import cmds
from ysrig import core, rig_base
reload(core)
reload(rig_base)

class Rig(rig_base.RigBace):
    def create(self):
        self.ctrls = core.convert_joint_to_controller(self.base_joints[:-1])
        cmds.parent(self.ctrls[0], self.ctrl_grp)

        self.ctrl_spaces = [None] * (self.joint_count - 1)
        self.ctrl_instances = [None] * (self.joint_count - 1)
        for i, name in enumerate(self.joint_names[:-1]):
            if name == self.joint_names[-2]:
                ctrl = core.CtrlCurve(f"{name}1", "Head")

            else:
                ctrl = core.CtrlCurve(f"{name}1", "Neck")

            self.ctrl_spaces[i] = core.create_space(self.ctrls[i], parent=True)
            ctrl.reparent_shape(self.ctrls[i])
            self.ctrl_instances[i] = ctrl

    def add_settings(self):
        cmds.addAttr(self.settings_node, ln="WL", at="enum", en="World:Local:", k=True)

    def connect(self):
        for ctrl, proxy in zip(self.ctrls, self.proxies):
            core.connect_matrix(ctrl, proxy, tl=self.translate_enabled, rt=True, sc=True, lc=self.connect_type)

        rev = core.create_node("reverse", name=f"Rev_{self.settings_node}_WL")
        cmds.connectAttr(f"{self.settings_node}.WL", f"{rev}.inputX")
        w = 1 / len(self.ctrl_spaces)
        for i, space in enumerate(self.ctrl_spaces):
            weight = w * (i + 1)
            dm = core.connect_matrix(Rig.ROOT_CTRL, space, rt=True, lc=False)[1]
            fm = core.connect_float_math(name=f"Fm_{space}", operation=2, fa=weight, fb=f"{rev}.outputX")
            core.connect_pair_blend(weight=f"{fm}.outFloat", in_rt1=f"{dm}.outputRotate!", in_rt2=f"{dm}.outputRotate", out_rt=f"{space}.rotate:XYZ")

    def set_attr(self):
        cmds.setAttr(f"{self.settings_node}.WL", 1)

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
        self.ctrls = core.convert_joint_to_controller(self.src_joints[:-1], sr=[self.src_side, self.side])
        cmds.parent(self.ctrls[0], self.ctrl_grp)

        self.ctrl_spaces = [None] * (self.joint_count - 1)
        self.ctrl_instances = [None] * (self.joint_count - 1)
        for i, name in enumerate(self.joint_names[:-1]):
            if name == self.joint_names[-2]:
                ctrl = core.CtrlCurve(f"{name}1", "Head")

            else:
                ctrl = core.CtrlCurve(f"{name}1", "Neck")

            self.ctrl_spaces[i] = core.create_space(self.ctrls[i], parent=True)
            ctrl.reparent_shape(self.ctrls[i])
            self.ctrl_instances[i] = ctrl

        core.mirror_space(self.ctrl_grp)