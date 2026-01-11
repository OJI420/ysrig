import importlib
from functools import partial
from maya import cmds
from ysrig import core
from ysrig.picker_editor import gui
importlib.reload(gui)


class Data(gui.PickerData):
    def create(self, shape_data, meta_node):
        mirror, side_list, grp_list = core.get_mirror_side(meta_node)
        FK_SHAPE = ["UpperLeg", "ForeLeg", "Foot", "Toe1", "Toe2"]
        IK_SHAPE = ["PV", "IK_Foot", "IK_Toe1", "IK_Toe2", "ALL", "Heel", "OUT", "IN", "ToeTip", "Toe"]
        HIDE_SHAPE = ["Foot", "Toe1", "Toe2", "IK_Foot", "IK_Toe1", "IK_Toe2"]
        TOE_SHAPE = ["Toe2", "IK_Toe2"]

        datas = []

        for side, grp in zip(side_list, grp_list):
            names = core.get_list_attributes(meta_node, "JointName")[:-1]
            names = core.get_mirror_names(names, side_list, side)
            names += [f"{grp}_{n}" for n in ["PV", "IK", "REV_FK_Toe", "REV_FK_ToeSub"]]
            revs = [f"{grp}_{n}" for n in ["REV_All", "REV_Heel", "REV_OutSide", "REV_InSide", "REV_ToeTip", "REV_Toe"]]
            shapes = ["UpperLeg", "ForeLeg", "Foot", "Toe1", "Toe2", "PV", "IK_Foot", "IK_Toe1", "IK_Toe2"]
            rev_shapes = ["ALL", "Heel", "OUT", "IN", "ToeTip", "Toe"]

            toe_sub = cmds.getAttr(f"{meta_node}.JointCount") == 6
            if not toe_sub:
                names = names[:-1]
                shapes.pop(3)
                shapes.pop(-2)

            buttons = []

            for name, shape in zip(names, shapes):
                s = shape_data[shape]
                shape_points = s["cvs"]
                pos = s["pos"].copy()
                color = core.get_ctrl_color_code(name)
                hide_attr = None
                hide_type = None

                if shape in FK_SHAPE:
                    hide_attr = {"IKFK":0}
                    if shape in HIDE_SHAPE:
                        hide_type = 0
                    else:
                        hide_type = 1

                if shape in IK_SHAPE:
                    hide_attr = {"IKFK":1}
                    if shape in HIDE_SHAPE:
                        hide_type = 0
                    else:
                        hide_type = 1

                if shape in TOE_SHAPE:
                    if toe_sub:
                        pos["x"] += 20
                        pos["y"] += 20

                buttons += [gui.ButtonData(name=name, shape_points=shape_points, position=pos, color=color, hide_attr=hide_attr, hide_type=hide_type)]

            rev_buttons = []

            for name, shape in zip(revs, rev_shapes):
                s = shape_data[shape]
                shape_points = s["cvs"]
                pos = s["pos"].copy()
                color = core.get_ctrl_color_code(name)
                hide_attr = {"IKFK":1}
                hide_type = 1
                rev_buttons += [gui.ButtonData(name=name, shape_points=shape_points, position=pos, color=color, hide_attr=hide_attr, hide_type=hide_type)]

            script = core.create_eunmattr_cycler(grp)
            if cmds.objExists(core.RIG_GROUP_NAME):
                script["IKFK Matching"] = partial(ik_fk_matching, meta_node, side)

            rev_data = [gui.PickerModuleData(name=f"{grp}_REV", position={'x': 0, 'y': 0}, buttons=rev_buttons, side=side, mirror=mirror, scripts=script)]
            s = shape_data["Pointer"]
            shape_points = s["cvs"]
            pos = s["pos"].copy()
            color = core.get_ctrl_color_code(names[0])
            buttons += [gui.ButtonData(name=f"{grp}@Pointer", shape_points=shape_points, position=pos, color=color, child_modules=rev_data)]

            datas += [gui.PickerModuleData(name=grp, position={'x': 0, 'y': 0}, buttons=buttons, side=side, mirror=mirror, scripts=script)]
        self.datas = datas


def ik_fk_matching(meta_node, side):
    grp_name = cmds.getAttr(f"{meta_node}.GroupName")
    joint_names = core.get_list_attributes(meta_node, "JointName")
    base_side = cmds.getAttr(f"{meta_node}.Side")

    search, replace = core.get_mirror_replacement(side, base_side)
    grp_name = grp_name.replace(search, replace)
    joint_names = [name.replace(search, replace) for name in joint_names]

    settings_node = f"Controller_{grp_name}_Group|Controller_{grp_name}_Settings"
    fk_ctrls = [f"Ctrl_{name}" for name in joint_names[:-1]]
    ik_joints = [f"Ikjt_{name}" for name in joint_names[:-1]]
    ik_ctrl = f"Ctrl_{grp_name}_IK"
    pv_ctrl = f"Ctrl_{grp_name}_PV"
    rev_fk_ctrl = [f"Ctrl_REV_FK_{name}" for name in joint_names[3:-1]]
    rev_fk_ctrl = [f"Ctrl_{grp_name}_REV_FK_{s}" for n, s in zip(rev_fk_ctrl, ["Toe", "ToeSub"])]
    target_ik = f"Target_{grp_name}_IK"
    target_fk = f"Target_{grp_name}_FK"

    ikfk_current_value = cmds.getAttr(f"{settings_node}.IKFK")

    cmds.undoInfo(ock=True)

    if ikfk_current_value:
        leg_length = cmds.getAttr(f"{ik_joints[1]}.translateX")
        tmp_joint = cmds.joint(fk_ctrls[1])
        cmds.setAttr(f"{tmp_joint}.translateY", leg_length*1.5)
        
        cmds.matchTransform(ik_ctrl, target_fk)
        cmds.matchTransform(pv_ctrl, tmp_joint)

        cmds.delete(tmp_joint)

        # Toe
        cmds.setAttr(f"{rev_fk_ctrl[0]}.rotateZ", cmds.getAttr(f"{fk_ctrls[3]}.rotateZ"))

        if len(ik_joints) == 5:
            cmds.setAttr(f"{rev_fk_ctrl[1]}.rotate", *cmds.getAttr(f"{fk_ctrls[4]}.rotate")[0])


    else: # IK -> FK
        cmds.setAttr(f"{fk_ctrls[0]}.rotate", *cmds.getAttr(f"{ik_joints[0]}.rotate")[0])
        cmds.setAttr(f"{fk_ctrls[1]}.rotateZ", cmds.getAttr(f"{ik_joints[1]}.rotateZ"))

        # Foot
        cmds.matchTransform(fk_ctrls[2], target_ik)

        # Toe
        cmds.setAttr(f"{fk_ctrls[3]}.rotateZ", cmds.getAttr(f"{ik_joints[3]}.rotateZ"))

        if len(ik_joints) == 5:
            cmds.setAttr(f"{fk_ctrls[4]}.rotate", *cmds.getAttr(f"{ik_joints[4]}.rotate")[0])

    cmds.setAttr(f"{settings_node}.IKFK", not ikfk_current_value)

    cmds.undoInfo(cck=True)