import importlib
from maya import cmds
from ysrig import core
from ysrig.picker_editor import gui
importlib.reload(gui)


class Data(gui.PickerData):
    def create(self, shape_data, meta_node):
        mirror, side_list, grp_list = core.get_mirror_side(meta_node)
        datas = []

        for side, grp in zip(side_list, grp_list):
            names = core.get_list_attributes(meta_node, "JointName")[:-1]
            names = core.get_mirror_names(names, side_list, side)
            neck_count = cmds.getAttr(f"{meta_node}.JointCount") - 3
            
            buttons = []

            neck_scale_y = 1.0
            neck_scale_y = 1.0 / float(neck_count)

            NECK_UNIT_HEIGHT = -72
            scaled_neck_offset = NECK_UNIT_HEIGHT * neck_scale_y
            current_neck_y_offset = 0.0

            for i, name in enumerate(names):
                
                shape_points = []
                pos = {}
                s = None

                if i == 0:
                    s = shape_data["Neck_Base"]
                    shape_points = s["cvs"]
                    pos = s["pos"].copy() 

                elif name == names[-1]:
                    s = shape_data["Head"]
                    shape_points = s["cvs"]
                    pos = s["pos"].copy()

                else:
                    s = shape_data["Neck"]

                    shape_points = [[p[0], p[1] * neck_scale_y] for p in s["cvs"]]
                    pos = s["pos"].copy() 
                    pos['y'] += current_neck_y_offset
                    current_neck_y_offset += scaled_neck_offset

                
                color = core.get_ctrl_color_code(name)
                
                buttons += [gui.ButtonData(name=name, shape_points=shape_points, position=pos, color=color)]

            datas += [gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=buttons, side=side, mirror=mirror)]
        self.datas = datas