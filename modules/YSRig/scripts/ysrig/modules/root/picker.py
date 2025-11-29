import importlib
from maya import cmds
from ysrig import core
from ysrig.picker_editor import gui
importlib.reload(gui)


class Data(gui.PickerData):
    def create(self, shape_data, meta_node):
        grp = cmds.getAttr(f"{meta_node}.GroupName")
        names = ["Root", "Root_Offset"]
        buttons = []
        for name, shape in zip(names, shape_data):
            s = shape_data[shape]
            color = core.get_ctrl_color_code(name)
            buttons += [gui.ButtonData(name=name, shape_points=s["cvs"], position=s["pos"], color=color)]

        data = gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=buttons, scripts=core.create_eunmattr_cycler(grp))

        self.datas = [data]