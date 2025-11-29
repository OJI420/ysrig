import importlib
from maya import cmds
from ysrig import core
from ysrig.picker_editor import gui
importlib.reload(gui)


class Data(gui.PickerData):
    def create(self, shape_data, meta_node):
        mirror, side_list, grp_list = core.get_mirror_side(meta_node)
        FK_SHAPE = ["UpperLeg", "ForeLeg", "Foot", "Toe1", "Toe2"]
        IK_SHAPE = ["PV", "IK_Foot", "IK_Toe1", "IK_Toe2", "ALL", "Heel", "OUT", "IN", "ToeTip", "Toe"]
        HIDE_SHAPE = ["Foot", "Toe1", "Toe2", "IK_Foot", "IK_Toe1", "IK_Toe2"]
        TOE_SHAPE = ["Toe2", "IK_Toe2"]

        datas = []

        for side, grp in zip(side_list, grp_list):
            names = core.get_list_attributes(meta_node, "JointName")[:-1]
            names = core.get_mirror_names(names, side_list, side)
            names += [f"{grp}_{n}" for n in ["PV", "IK", "REV_FK_Toe", "REV_FK_ToeSub"]]
            revs = [f"{grp}_{n}" for n in ["REV_All", "REV_Heel", "REV_OutSide", "REV_InSide", "REV_ToeTip", "REV_Toe"]]
            shapes = ["UpperLeg", "ForeLeg", "Foot", "Toe1", "Toe2", "PV", "IK_Foot", "IK_Toe1", "IK_Toe2"]
            rev_shapes = ["ALL", "Heel", "OUT", "IN", "ToeTip", "Toe"]

            toe_sub = cmds.getAttr(f"{meta_node}.JointCount") == 6
            if not toe_sub:
                names = names[:-1]
                shapes.pop(3)
                shapes.pop(-2)

            buttons = []

            for name, shape in zip(names, shapes):
                s = shape_data[shape]
                shape_points = s["cvs"]
                pos = s["pos"].copy()
                color = core.get_ctrl_color_code(name)
                hide_attr = None
                hide_type = None

                if shape in FK_SHAPE:
                    hide_attr = {"IKFK":0}
                    if shape in HIDE_SHAPE:
                        hide_type = 0
                    else:
                        hide_type = 1

                if shape in IK_SHAPE:
                    hide_attr = {"IKFK":1}
                    if shape in HIDE_SHAPE:
                        hide_type = 0
                    else:
                        hide_type = 1

                if shape in TOE_SHAPE:
                    if toe_sub:
                        pos["x"] += 20
                        pos["y"] += 20

                buttons += [gui.ButtonData(name=name, shape_points=shape_points, position=pos, color=color, hide_attr=hide_attr, hide_type=hide_type)]

            rev_buttons = []

            for name, shape in zip(revs, rev_shapes):
                s = shape_data[shape]
                shape_points = s["cvs"]
                pos = s["pos"].copy()
                color = core.get_ctrl_color_code(name)
                hide_attr = {"IKFK":1}
                hide_type = 1
                rev_buttons += [gui.ButtonData(name=name, shape_points=shape_points, position=pos, color=color, hide_attr=hide_attr, hide_type=hide_type)]

            rev_data = [gui.PickerModuleData(name=f"{grp}_REV", position={'x': 0, 'y': 0}, buttons=rev_buttons, side=side, mirror=mirror, scripts=core.create_eunmattr_cycler(grp))]
            s = shape_data["Pointer"]
            shape_points = s["cvs"]
            pos = s["pos"].copy()
            color = core.get_ctrl_color_code(names[0])
            buttons += [gui.ButtonData(name=f"{grp}@Pointer", shape_points=shape_points, position=pos, color=color, child_modules=rev_data)]

            datas += [gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=buttons, side=side, mirror=mirror, scripts=core.create_eunmattr_cycler(grp))]
        self.datas = datas