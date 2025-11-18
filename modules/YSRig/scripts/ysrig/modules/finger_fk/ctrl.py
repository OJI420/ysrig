from importlib import *
from maya import cmds
from ysrig import core, ctrl_base
reload(core)
reload(ctrl_base)

class Ctrl(ctrl_base.CtrlBace):
    def setup(self):
        self.ctrl_shape_type = core.get_enum_attribute(self.meta_node, "FKControllrShapeType")
        self.carpal_flags = core.get_list_attributes(self.meta_node, "CarpalFlag")
        self.other_guide_world_matrices = core.get_list_attributes(self.meta_node, "OtherGuidesWorldMatrix")
        self.scale_uniformly = True
        self.all_ctrls = []
        self.all_ctrl_spaces = []

    def create(self):
        for name in self.joint_names:
            if "_GB" in name:
                ctrl = core.EditCurve(name.replace("_GB", "_All"), "Roll")
                space = core.create_space(ctrl.parent_node)

                self.all_ctrls.append(ctrl.parent_node)
                self.all_ctrl_spaces.append(space)

            else:
                ctrl = core.EditCurve(name, self.ctrl_shape_type)
                space = core.create_space(ctrl.parent_node)

                self.scale_uniformly = ctrl.scale_uniformly
                self.ctrls.append(ctrl.parent_node)
                self.ctrl_spaces.append(space)

            core.create_hierarchy(
                self.grp,
                    space, ":",
                        ctrl.parent_node
            )

    def set_color(self):
        klass = CtrlColor()
        klass.set_color(self.ctrls, self.all_ctrls, self.side)

    def set_space_transform(self):
        space_chunk_list = core.get_chunk_list(self.ctrl_spaces, 3)
        matrix_chunk_list = core.get_chunk_list(self.guide_world_matrices, 4)
        metacarpal_children_matrices = []
        all_scale = 0

        for i, spaces in enumerate(space_chunk_list):
            if 3 == len(spaces):
                all_scale += core.auto_scale_chain_ctrls(spaces, matrix_chunk_list[i], 0.3, self.scale_uniformly)
                if self.carpal_flags[i]:
                    metacarpal_children_matrices.append(matrix_chunk_list[i][0])

            else:
                mat = [self.guide_world_matrices[-1], core.get_average_pos_matrix(metacarpal_children_matrices)]
                core.auto_scale_chain_ctrls(spaces, mat, 0.3, self.scale_uniformly)

        all_ctrl_count = len(self.all_ctrls)
        ave_scale = [all_scale / all_ctrl_count * 2] * 3
        for i, space in enumerate(self.all_ctrl_spaces):
            mat = self.other_guide_world_matrices[i + all_ctrl_count]
            pos, rot = core.decompose_matrix(mat)[:-1]
            cmds.setAttr(f"{space}.translate", *pos)
            cmds.setAttr(f"{space}.rotate", *rot)
            cmds.setAttr(f"{space}.scale", *ave_scale)

        self.ctrls = self.ctrls + self.all_ctrls
        self.ctrl_spaces = self.ctrl_spaces + self.all_ctrl_spaces

    def lock_attributes(self):
        for ctrl in self.all_ctrls:
            self._lock_attrs += [ctrl, ["translate"]]


class CtrlColor(ctrl_base.CtrlColorBase):
    def set_color(self, ctrls, all_ctrls, side):
        if side == "L":
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.LEFT_SECOND_COLOR)

            for ctrl in all_ctrls:
                core.set_ctrl_shape_color(ctrl, core.LEFT_SARD_COLOR)

        elif side == "R":
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.RIGHT_SECOND_COLOR)

            for ctrl in all_ctrls:
                core.set_ctrl_shape_color(ctrl, core.RIGHT_SARD_COLOR)

        else:
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.CENTER_SECOND_COLOR)

            for ctrl in all_ctrls:
                core.set_ctrl_shape_color(ctrl, core.CENTER_SARD_COLOR)