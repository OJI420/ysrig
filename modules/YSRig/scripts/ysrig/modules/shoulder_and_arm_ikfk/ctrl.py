from importlib import *
from maya import cmds
from ysrig import core, ctrl_base
reload(core)
reload(ctrl_base)

class Ctrl(ctrl_base.CtrlBace):
    def setup(self):
        self.ikctrl_shape_type = core.get_enum_attribute(self.meta_node, "IKControllrShapeType")
        self.pvctrl_shape_type = core.get_enum_attribute(self.meta_node, "PVControllrShapeType")
        self.other_guide_world_matrices = core.get_list_attributes(self.meta_node, "OtherGuidesWorldMatrix")

    def create(self):
        ctrls = [None] * (self.joint_count + 1)
        ctrl_spaces = [None] * (self.joint_count + 1)
        for i in range(self.joint_count + 1):
            if i == 0:
                ctrl = core.EditCurve(self.joint_names[i], "Shoulder")

            elif i == 4:
                ctrl = core.EditCurve(f"{self.grp_name}_IK", self.ikctrl_shape_type)

            elif i == 5:
                ctrl = core.EditCurve(f"{self.grp_name}_PV", self.pvctrl_shape_type)

            else:
                ctrl = core.EditCurve(self.joint_names[i], "BoundingBox")

            ctrls[i] = ctrl.parent_node
            ctrl_spaces[i] = core.create_space(ctrls[i])
            core.create_hierarchy(
                self.grp,
                    ctrl_spaces[i], ":",
                        ctrls[i]
            )

        self.ctrls = ctrls
        self.ctrl_spaces = ctrl_spaces

    def set_space_transform(self):
        scale = core.auto_scale_chain_ctrls(self.ctrl_spaces[:-2], self.guide_world_matrices, 0.2, False)
        s = [scale * 3] * 3
        cmds.setAttr(f"{self.ctrl_spaces[0]}.scale", *s)

        s = [scale * 1.5] * 3
        pos = core.decompose_matrix(self.guide_world_matrices[3])[0]
        cmds.setAttr(f"{self.ctrl_spaces[4]}.translate", *pos)
        cmds.setAttr(f"{self.ctrl_spaces[4]}.scale", *s)

        s = [scale * 0.5] * 3
        pos = core.decompose_matrix(self.other_guide_world_matrices[0])[0]
        cmds.setAttr(f"{self.ctrl_spaces[5]}.translate", *pos)
        cmds.setAttr(f"{self.ctrl_spaces[5]}.scale", *s)

    def add_settings(self):
        cmds.addAttr(self.settings_node, ln="IKFK", at="long", min=0, max=1, dv=0, k=True)

    def connect(self):
        core.connect_switch_attr(
            f"{self.settings_node}.IKFK",
            core.compose_attr_paths(self.ctrls[1:3], "visibility", multi=True),
            core.compose_attr_paths(self.ctrls[4:], "visibility", multi=True)
        )

    def lock_attributes(self):
        self._lock_attrs += [
            self.ctrls[4], ["translate"],
            self.ctrls[5], ["translate"]
            ]


class CtrlColor(ctrl_base.CtrlColorBase):
    def set_color(self, ctrls, side):
        super().set_color(ctrls, side)

        if side == "L":
            core.set_ctrl_shape_color(ctrls[-1], core.LEFT_SECOND_COLOR)
            core.set_ctrl_shape_color(ctrls[-2], core.LEFT_SARD_COLOR)

        elif side == "R":
            core.set_ctrl_shape_color(ctrls[-1], core.RIGHT_SECOND_COLOR)
            core.set_ctrl_shape_color(ctrls[-2], core.RIGHT_SARD_COLOR)

        else:
            core.set_ctrl_shape_color(ctrls[-1], core.CENTER_SECOND_COLOR)
            core.set_ctrl_shape_color(ctrls[-2], core.CENTER_SARD_COLOR)