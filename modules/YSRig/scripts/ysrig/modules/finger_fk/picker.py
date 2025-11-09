import importlib
from maya import cmds
from ysrig import core
from ysrig.picker_editor import gui
importlib.reload(gui)


def main(shape_data, meta_node) -> gui.PickerModuleData:
    mirror, side_list, grp_list = core.get_mirror_side(meta_node)
    FINGER_BTN_NAMES = ["MP", "PIP", "DIP", "Roll"]
    CARPAL_NAEM = "Carpal"

    data = []

    for side, grp in zip(side_list, grp_list):
        all_names = core.get_list_attributes(meta_node, "JointName")
        all_names = core.get_mirror_names(all_names, side_list, side)
        names_chunk = core.get_chunk_list(all_names, 4)

        fingers_datas = []

        for names in names_chunk:
            if len(names) == 1:
                finger_name = names[0]
                s = shape_data[CARPAL_NAEM]
                shape_points = s["cvs"]
                pos = s["pos"].copy()
                color = core.get_ctrl_color_code(finger_name)
                buttons = [gui.ButtonData(name=finger_name, shape_points=shape_points, position=pos, color=color)]

            else:
                buttons = []
                finger_name = names[-1].replace("_GB", "_All")
                for fng_name, bt_name in zip(names, FINGER_BTN_NAMES):
                    if bt_name == "Roll":
                        fng_name = finger_name
                    s = shape_data[bt_name]
                    shape_points = s["cvs"]
                    pos = s["pos"].copy()
                    color = core.get_ctrl_color_code(fng_name)
                    buttons += [gui.ButtonData(name=fng_name, shape_points=shape_points, position=pos, color=color)]

            fingers_datas += [gui.PickerModuleData(name=finger_name, position={'x': 0, 'y': 0}, buttons=buttons, side=side, mirror=mirror)]

        s = shape_data["Pointer"]
        shape_points = s["cvs"]
        pos = s["pos"].copy()
        color = core.get_ctrl_color_code(names_chunk[0][0])

        button = [gui.ButtonData(name=f"{grp}@Pointer", shape_points=shape_points, position=pos, color=color, child_modules=fingers_datas)]

        data += [gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=button, side=side, mirror=mirror)]
    return data