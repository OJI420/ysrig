import importlib
from maya import cmds
from ysrig import core
from ysrig.picker_editor import gui
importlib.reload(gui)


def main(shape_data, meta_node) -> gui.PickerModuleData:
    mirror, side_list, grp_list = core.get_mirror_side(meta_node)

    data = []
    HEIGHT = 20

    for side, grp in zip(side_list, grp_list):
        names = core.get_list_attributes(meta_node, "JointName")[:-1]
        names = core.get_mirror_names(names, side_list, side)

        buttons = []
        current_offset = 0.0

        for name in names:
            s = shape_data["Chain"]
            shape_points = s["cvs"]
            pos = s["pos"].copy()
            pos['y'] += current_offset
            color = core.get_ctrl_color_code(name)

            buttons += [gui.ButtonData(name=name, shape_points=shape_points, position=pos, color=color)]
            current_offset += HEIGHT

        data += [gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=buttons, side=side, mirror=mirror)]
    return data