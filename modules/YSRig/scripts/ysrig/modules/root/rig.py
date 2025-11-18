from importlib import *
from maya import cmds
from ysrig import core, rig_base
reload(core)
reload(rig_base)

class Rig(rig_base.RigBace):
    def _create_grp(self):
        rig_grp = core.create_labeled_node("transform", core.RIG_GROUP_NAME, name=core.RIG_GROUP_NAME)
        cmds.parent(rig_grp, core.YSRIG_GROUP_NAME)
        super()._create_grp()

    def parent_grp(self):
        cmds.parent(self.grp, core.RIG_GROUP_NAME)

    def create_ctrl_grp(self):
        pass

    def create(self):
        root_ctrl = core.CtrlCurve(self.joint_names[0], "Root")
        root_ctrl.set_shape_color(core.ROOT_MAIN_COLOR)
        root_ctrl.set_scale(50)
        offset_ctrl = core.CtrlCurve("Root_Offset", "Root_Offset")
        offset_ctrl.set_shape_color(core.ROOT_SECOND_COLOR)
        offset_ctrl.set_scale(50)

        core.create_hierarchy(
            self.grp,
                root_ctrl.parent_node, ":",
                    offset_ctrl.parent_node
        )

        self.ctrls = [root_ctrl.parent_node, offset_ctrl.parent_node]
        self.ctrl_instances = [root_ctrl, offset_ctrl]

    def set_color(self):
        pass

    def set_shape_transform(self):
        super().set_shape_transform()
        offset_scale = core.decompose_matrix(self.ctrl_space_matrices[0])[2]
        self.ctrl_instances[1].set_matrix(self.ctrl_matrices[0], offset_scale=offset_scale)
        self.ctrl_instances[1].set_width(self.ctrl_line_width)

    def _connect(self):
        pass

    def connect(self):
        core.connect_same_attr(self.ctrls[0], self.base_joints[0], ["translate", "rotate", "scale"])
        cmds.addAttr(self.ctrls[0], ln="UniformScale", at="double", min=0.01, dv=1.0, k=True)
        [cmds.connectAttr(f"{self.ctrls[0]}.UniformScale", f"{self.ctrls[0]}.scale{a}") for a in "XYZ"]

    def lock_attributes(self):
        for ctrl in self.ctrls:
            self.lock_attrs += [ctrl, ["scale", "visibility"]]

    def post_process(self):
        cmds.delete(self.proxies[0])

    def connect_visibility(self):
        pass

class RigMirror(Rig):
    pass