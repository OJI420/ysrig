import importlib
from maya import cmds
from ysrig import core
from ysrig.picker_editor import gui
importlib.reload(gui)

class Data(gui.PickerData):
    def create(self, shape_data, meta_node):
        grp = cmds.getAttr(f"{meta_node}.GroupName")
        SUFFIX = ["Aim", "OpenClose", "ClosePos", "Scale"]
        names = core.get_list_attributes(meta_node, "JointName")
        names = names[:1] + names[2:]
        names += [f"{names[0]}_{s}" for s in SUFFIX]
        names += [name.replace("L_", "R_") for name in names]
        names += [f"{grp}_Aim_All"]

        SHAPES = ["L_Eye", "L_Top", "L_Bottom", "L_Aim", "L_OC", "L_CP", "L_SC", "R_Eye", "R_Top", "R_Bottom", "R_Aim", "R_OC", "R_CP", "R_SC", "Aim"] 
        buttons = []

        for name, shape in zip(names, SHAPES):
            s = shape_data[shape]
            color = core.get_ctrl_color_code(name)
            buttons += [gui.ButtonData(name=name, shape_points=s["cvs"], position=s["pos"], color=color)]

        data = gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=buttons)

        self.datas = [data]