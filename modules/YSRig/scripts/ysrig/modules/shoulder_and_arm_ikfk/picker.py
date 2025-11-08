import importlib
from maya import cmds
from ysrig import core
from ysrig.picker_editor import gui
importlib.reload(gui)


def main(shape_data, meta_node) -> gui.PickerModuleData:
    mirror, side_list, grp_list = core.get_mirror_side(meta_node)

    data = []

    for side, grp in zip(side_list, grp_list):
        names = core.get_list_attributes(meta_node, "JointName")[:-1]
        names = core.get_mirror_names(names, side_list, side)
        names += [f"{grp}_IK", f"{grp}_PV"]

        buttons = []

        for name, shape in zip(names, shape_data):
            
            s = shape_data[shape]
            shape_points = s["cvs"]
            pos = s["pos"].copy()
            color = core.get_ctrl_color_code(name)
            hide_attr = None
            hide_type = None

            if shape == "UpperArm" or shape == "ForeArm":
                hide_attr = {"IKFK":0}
                hide_type = 1

            if shape == "IK" or shape == "PV":
                hide_attr = {"IKFK":1}
                hide_type = 1

            buttons += [gui.ButtonData(name=name, shape_points=shape_points, position=pos, color=color, hide_attr=hide_attr, hide_type=hide_type)]

        data += [gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=buttons, side=side, mirror=mirror)]
    return data