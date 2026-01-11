import importlib
from maya import cmds
from ysrig import core
from ysrig.picker_editor import gui
importlib.reload(gui)


class Data(gui.PickerData):
    def create(self, shape_data, meta_node):
        mirror, side_list, grp_list = core.get_mirror_side(meta_node)

        datas = []
        HEIGHT = 20

        for side, grp in zip(side_list, grp_list):
            ctrl_count = cmds.getAttr(f"{meta_node}.ControllrCount")
            names = core.create_numbered_names(grp, ctrl_count, gb=False)
            names = core.get_mirror_names(names, side_list, side)

            buttons = []
            current_offset = 0.0

            for name in names:
                s = shape_data["Handle"]
                shape_points = s["cvs"]
                pos = s["pos"].copy()
                pos['y'] += current_offset
                color = core.get_ctrl_color_code(name)

                buttons += [gui.ButtonData(name=name, shape_points=shape_points, position=pos, color=color)]
                current_offset += HEIGHT

            name = f"{grp}_All"
            shape = shape_data["All"]
            shape_points = shape["cvs"]
            color = core.get_ctrl_color_code(name)

            buttons += [gui.ButtonData(name=name, shape_points=shape_points, position=shape["pos"], color=color)]

            datas += [gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=buttons, side=side, mirror=mirror)]
        self.datas = datas