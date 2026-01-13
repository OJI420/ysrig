import importlib
from functools import partial
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

            script = core.create_eunmattr_cycler(grp)
            if cmds.objExists(core.RIG_GROUP_NAME):
                script["IKFK Match"] = partial(ik_fk_matching, meta_node, side, False)
                script["IKFK Switch and Match"] = partial(ik_fk_matching, meta_node, side, True)

            datas += [gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=buttons, side=side, mirror=mirror, scripts=script)]
        self.datas = datas


def ik_fk_matching(meta_node, side, switch):
    grp_name = cmds.getAttr(f"{meta_node}.GroupName")
    joint_names = core.get_list_attributes(meta_node, "JointName")
    base_side = cmds.getAttr(f"{meta_node}.Side")

    search, replace = core.get_mirror_replacement(side, base_side)
    grp_name = grp_name.replace(search, replace)
    joint_names = [name.replace(search, replace) for name in joint_names]

    settings_node = f"Controller_{grp_name}_Group|Controller_{grp_name}_Settings"
    fk_ctrls = [f"Ctrl_{name}" for name in joint_names[:-1]]
    ik_joints = [f"Ikjt_{name}" for name in joint_names[1:-1]]
    ik_ctrl = f"Ctrl_{grp_name}_IK"
    pv_ctrl = f"Ctrl_{grp_name}_PV"

    ikfk_current_value = cmds.getAttr(f"{settings_node}.IKFK")

    cmds.undoInfo(ock=True)

    if ikfk_current_value: # FK -> IK
        arm_length = cmds.getAttr(f"{ik_joints[1]}.translateX")
        tmp_joint = cmds.joint(fk_ctrls[2])
        cmds.setAttr(f"{tmp_joint}.translateY", arm_length*-1.5)
        
        cmds.matchTransform(ik_ctrl, fk_ctrls[-1])
        cmds.matchTransform(pv_ctrl, tmp_joint)

        cmds.setKeyframe(f"{ik_ctrl}.translate")
        cmds.setKeyframe(f"{pv_ctrl}.translate")

        cmds.delete(tmp_joint)

    else: # IK -> FK
        up_arm_rot = cmds.getAttr(f"{ik_joints[0]}.rotate")[0]
        fore_arm_rot = cmds.getAttr(f"{ik_joints[1]}.rotate")[0]

        cmds.setAttr(f"{fk_ctrls[1]}.rotate", *up_arm_rot)
        cmds.setAttr(f"{fk_ctrls[2]}.rotateZ", fore_arm_rot[2])

        cmds.setKeyframe(f"{fk_ctrls[1]}.rotate")
        cmds.setKeyframe(f"{fk_ctrls[2]}.rotateZ")

    if switch:
        cmds.setAttr(f"{settings_node}.IKFK", not ikfk_current_value)
        cmds.setKeyframe(f"{settings_node}.IKFK")

    cmds.undoInfo(cck=True)