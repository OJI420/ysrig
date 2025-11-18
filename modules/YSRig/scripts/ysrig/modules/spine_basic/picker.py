import importlib
from maya import cmds
from ysrig import core
from ysrig.picker_editor import gui
importlib.reload(gui)


class Data(gui.PickerData):
    def create(self, shape_data, meta_node):
        grp = cmds.getAttr(f"{meta_node}.GroupName")
        names = core.get_list_attributes(meta_node, "JointName")
        names = names + [f"{grp}_Torso"]
        spine_count = cmds.getAttr(f"{meta_node}.JointCount") - 1
        
        buttons = []

        spine_scale_y = 1.0
        spine_scale_y = 1.0 / float(spine_count)

        SPINE_UNIT_HEIGHT = -172
        scaled_spine_offset = SPINE_UNIT_HEIGHT * spine_scale_y
        current_spine_y_offset = 0.0

        for i, name in enumerate(names):
            
            shape_points = []
            pos = {}
            s = None

            if i == 0:
                s = shape_data["Hip"]
                shape_points = s["cvs"]
                pos = s["pos"].copy() 

            elif name == names[-1]:
                s = shape_data["Torso"]
                shape_points = s["cvs"]
                pos = s["pos"].copy()

            else:
                if name == names[-2]:
                    s = shape_data["Spine_End"]
                else:
                    s = shape_data["Spine"]

                shape_points = [[p[0], p[1] * spine_scale_y] for p in s["cvs"]]
                pos = s["pos"].copy() 
                pos['y'] += current_spine_y_offset
                current_spine_y_offset += scaled_spine_offset

            
            color = core.get_ctrl_color_code(name)
            
            buttons += [gui.ButtonData(name=name, shape_points=shape_points, position=pos, color=color)]

        data = gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=buttons)
        self.datas = [data]