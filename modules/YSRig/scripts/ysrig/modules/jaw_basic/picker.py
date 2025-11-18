import importlib
from maya import cmds
from ysrig import core
from ysrig.picker_editor import gui
importlib.reload(gui)

class Data(gui.PickerData):
    def create(self, shape_data, meta_node):
        grp = cmds.getAttr(f"{meta_node}.GroupName")
        name = core.get_list_attributes(meta_node, "JointName")[0]
        s = shape_data["Jaw"]
        color = core.get_ctrl_color_code(name)
        buttons = [gui.ButtonData(name=name, shape_points=s["cvs"], position=s["pos"], color=color)]

        data = gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=buttons)

        self.datas = [data]