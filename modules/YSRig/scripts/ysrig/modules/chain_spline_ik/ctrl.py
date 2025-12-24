from importlib import *
from maya import cmds
from ysrig import core, ctrl_base
reload(core)
reload(ctrl_base)

All_CTRL_SHAPE = "Triangle"

class Ctrl(ctrl_base.CtrlBace):
    def setup(self):
        self.ctrl_shape_type = core.get_enum_attribute(self.meta_node, "ControllrShapeType")
        self.ctrl_count = cmds.getAttr(f"{self.meta_node}.ControllrCount")
        self.scale_uniformly = True

    def create(self):
        ctrls = [None] * (self.ctrl_count + 1)
        ctrl_spaces = [None] * (self.ctrl_count + 1)
        names = core.create_numbered_names(self.grp_name, self.ctrl_count, gb=False)

        curve = cmds.curve(d=1, p=[core.decompose_matrix(trs)[0] for trs in self.guide_world_matrices])
        core.rebuild_curve(curve, self.ctrl_count)
        self.pos_list = core.get_curve_points_pos(curve)
        cmds.delete(curve)

        for i, name in enumerate(names):
            ctrl = core.EditCurve(name, self.ctrl_shape_type)
            ctrls[i] = ctrl.parent_node
            ctrl_spaces[i] = core.create_space(ctrls[i])
            core.create_hierarchy(
                self.grp,
                    ctrl_spaces[i], ":",
                        ctrls[i]
            )

        ctrl = core.EditCurve(f"{self.grp_name}_All", All_CTRL_SHAPE)
        ctrls[-1] = ctrl.parent_node
        ctrl_spaces[-1] = core.create_space(ctrls[-1])
        core.create_hierarchy(
            self.grp,
                ctrl_spaces[-1], ":",
                    ctrls[-1]
        )

        self.ctrls = ctrls
        self.ctrl_spaces = ctrl_spaces

    def set_space_transform(self):
        pos, rot = core.decompose_matrix(self.guide_world_matrices[0])[:-1]
        scl = sum([core.get_distance(self.guide_world_matrices[i], self.guide_world_matrices[i+1]) for i in range(self.ctrl_count-1)]) / self.ctrl_count
        for i, space in enumerate(self.ctrl_spaces):
            cmds.setAttr(f"{space}.rotate", *rot)
            cmds.setAttr(f"{space}.scale", scl, scl, scl)

            if space == self.ctrl_spaces[-1]:
                cmds.setAttr(f"{space}.translate", *pos)

            else:
                p = self.pos_list[i]
                cmds.setAttr(f"{space}.translate", *p)


class CtrlColor(ctrl_base.CtrlColorBase):
    def set_color(self, ctrls, side):
        if side == "L":
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.LEFT_SECOND_COLOR)

        elif side == "R":
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.RIGHT_SECOND_COLOR)

        else:
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.CENTER_SECOND_COLOR)