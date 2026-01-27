from maya import cmds
from ysrig import core
from ysrig.modules import root, spine_basic, neck_and_head_basic, shoulder_and_arm_ikfk, leg_and_foot_ikfk, finger_fk, eye_basic, eye_and_simple_eyelid, jaw_basic, biped
from ysrig import picker_editor

class Guide():
    def __init__(self, spine_count, neck_count, arm_tj_count, leg_tj_count ,finger, finger_names, carpal_flags, tiptoe, jaw, eyes, eyelid, connect_type):
        self.spine_count = spine_count
        self.neck_count = neck_count
        self.arm_tj_count = arm_tj_count
        self.leg_tj_count = leg_tj_count
        self.finger_names = finger_names
        self.carpal_flags = carpal_flags
        self.tiptoe = tiptoe
        self.eyelid = eyelid
        self.connect_type = connect_type
        self.use_finger = finger

        self.picker_data = []

        self.root()
        self.spine()
        self.neck()
        self.arm()
        if finger:
            self.finger()

        self.leg()

        if jaw:
            self.jaw()

        if eyes:
            self.eyes()

        self.set_attr()

        if jaw or eyes:
            data = {}
            data["pos"] = {"x":100, "y":-450}
            data["rot"] = 0
            data["scl"] = 1
            self.picker_data += [data]
        self.set_picker()

    def root(self):
        root.guide.main()
        data = {}
        data["pos"] = {"x":0, "y":480}
        data["rot"] = 0
        data["scl"] = 1
        self.picker_data += [data]

    def spine(self):
        guide = spine_basic.guide.Guide("Spine", self.spine_count, "Root", "", ["Hip"])
        guide.apply_settings(root_matrix=[0, 100, 0, 0, 0, 0, 1], guide_positions=[[5, 0, 0], [30, 0, 0]], connect_type=self.connect_type)
        self.spine_gb = guide.joint_names[-1]
        data = {}
        data["pos"] = {"x":0, "y":-90}
        data["rot"] = 0
        data["scl"] = 1
        self.picker_data += [data]

    def neck(self):
        guide = neck_and_head_basic.guide.Guide("Neck", self.neck_count, self.spine_gb, "", ["Head"])
        guide.apply_settings(root_matrix=[0, 150, 0, 0, 0, 0, 1], guide_positions=[[10, 0, 0], [15, 0, 0], [30, 0, 0]], connect_type=self.connect_type)
        data = {}
        data["pos"] = {"x":0, "y":-310}
        data["rot"] = 0
        data["scl"] = 1
        self.picker_data += [data]

    def arm(self):
        guide = shoulder_and_arm_ikfk.guide.Guide("L_Arm", 0, self.spine_gb, "L_", ["L_Shoulder", "L_UpperArm", "L_ForeArm", "L_Hand"],
                                                ":".join(shoulder_and_arm_ikfk.gui.IK_CTRL_SHAPE_TYPE), ":".join(shoulder_and_arm_ikfk.gui.PV_CTRL_SHAPE_TYPE))
        guide.apply_settings(root_matrix=[5, 145, 0, 0, 0, 0, 1], guide_positions=[[10, 0, 0], [50, 0, 0], [75, 0, 0]], connect_type=self.connect_type, twist_joint_count=self.arm_tj_count, goal_bone=not self.use_finger)
        data = {}
        data["pos"] = {"x":80, "y":-300}
        data["rot"] = 60
        data["scl"] = 1
        self.picker_data += [data]

    def finger(self):
        guide = finger_fk.guide.Guide("L_Finger", 0, "L_Hand", "L_", self.finger_names, self.carpal_flags, ":".join(finger_fk.gui.CTRL_SHAPE_TYPE))
        guide.apply_settings(root_matrix=[55, 155, 0, 0, 0, 0, 1], guide_positions=[[10, -10, 0], [10, 0, 0]])
        data = {}
        data["pos"] = {"x":320, "y":0}
        data["rot"] = 0
        data["scl"] = 1
        self.picker_data += [data]

        for i in range(len(self.finger_names)):
            data = {}
            match i:
                case 0:
                    data["pos"] = {"x":-85, "y":340}
                    data["rot"] = -40
                    data["scl"] = 2
                case 1:
                    data["pos"] = {"x":-100, "y":-20}
                    data["rot"] = -4
                    data["scl"] = 1.5
                case 2:
                    data["pos"] = {"x":30, "y":-40}
                    data["rot"] = 0
                    data["scl"] = 1.5
                case 3:
                    data["pos"] = {"x":160, "y":-40}
                    data["rot"] = 2
                    data["scl"] = 1.5
                case 4:
                    data["pos"] = {"x":290, "y":-20}
                    data["rot"] = 4
                    data["scl"] = 1.5
                case _:
                    data["pos"] = {"x":0, "y":0}
                    data["rot"] = 0
                    data["scl"] = 1.5

            self.picker_data += [data]

        if True in self.carpal_flags:
            data = {}
            data["pos"] = {"x":150, "y":250}
            data["rot"] = 0
            data["scl"] = 2
            self.picker_data += [data]

    def leg(self):
        guide = leg_and_foot_ikfk.guide.Guide("L_Leg", 0, "Hip", "L_", ["L_UpperLeg", "L_ForeLeg", "L_Foot", "L_Toe", "L_ToeSub"], self.tiptoe, ":".join(leg_and_foot_ikfk.gui.PV_CTRL_SHAPE_TYPE))
        guide.apply_settings(root_matrix=[15, 100, 0, 0, 0, 0, 1], guide_positions=[[90, 0, 0], [5, 0, 20]], connect_type=self.connect_type, twist_joint_count=self.leg_tj_count, pv_ctrl_shape_type=3)
        data = {}
        data["pos"] = {"x":50, "y":20}
        data["rot"] = 0
        data["scl"] = 1
        self.picker_data += [data]

    def jaw(self):
        guide = jaw_basic.guide.Guide("Jaw", 2, core.FACIALS_ROOT_NAME, "")
        guide.apply_settings(root_matrix=[0, 165, 5, 0, 0, 0, 1], guide_positions=[[0, 165, 10]], goal_bone=False)

    def eyes(self):
        if self.eyelid:
            guide = eye_and_simple_eyelid.guide.Guide("Eyes", 4, core.FACIALS_ROOT_NAME, "", ["L_Eye", "L_Pupil", "L_Eyelid_Top", "L_Eyelid_Bottom"])

        else:
            guide = eye_basic.guide.Guide("Eyes", 2, core.FACIALS_ROOT_NAME, "", ["L_Eye", "L_Eye_GB"])

        guide.apply_settings(root_matrix=[5, 170, 10, 0, 0, 0, 1], guide_positions=[[0, 0, 1], [0, 0, 40]])

    def set_attr(self):
        attrs = [
            [f"{core.YSRIG_GROUP_NAME}.YSRigVersion", core.VERSION],
            [f"{core.YSRIG_GROUP_NAME}.BuildType", "Biped"],
            [f"{core.GUIDE_FACIALS_GROUP_NAME}.FacialRootName", "Head"]
        ]

        for attr in attrs:
            cmds.setAttr(attr[0], l=False)
            cmds.setAttr(*attr, l=True, type="string")

    def set_picker(self):
        mods = picker_editor.gui.get_shape_data()
        data = self.picker_data
        i = 0
        for mod in mods:
            if mod.name == "L_Finger":
                mod.position = data[i]["pos"]
                mod.rotation = data[i]["rot"]
                mod.scale = data[i]["scl"]
                mod.updata_from_data(f"Picker_{mod.name}")
                i += 1
                for m in mod.buttons[0].child_modules:
                    m.position = data[i]["pos"]
                    m.rotation = data[i]["rot"]
                    m.scale = data[i]["scl"]
                    m.updata_from_data(f"Picker_{m.name}")
                    i += 1

            elif mod.name == "R_Finger":
                j = len(mod.buttons[0].child_modules) + 1
                mod.position["x"] = data[i-j]["pos"]["x"]*-1
                mod.position["y"] = data[i-j]["pos"]["y"]
                mod.rotation = data[i-j]["rot"]*-1
                mod.scale = data[i-j]["scl"]
                mod.updata_from_data(f"Picker_{mod.name}")
                j -= 1
                for m in mod.buttons[0].child_modules:
                    m.position["x"] = data[i-j]["pos"]["x"]*-1
                    m.position["y"] = data[i-j]["pos"]["y"]
                    m.rotation = data[i-j]["rot"]*-1
                    m.scale = data[i-j]["scl"]
                    m.updata_from_data(f"Picker_{m.name}")
                    j -= 1

            elif "R_" in mod.name:
                mod.position["x"] = data[i-1]["pos"]["x"]*-1
                mod.position["y"] = data[i-1]["pos"]["y"]
                mod.rotation = data[i-1]["rot"]*-1
                mod.scale = data[i-1]["scl"]
                mod.updata_from_data(f"Picker_{mod.name}")

            else:
                mod.position = data[i]["pos"]
                mod.rotation = data[i]["rot"]
                mod.scale = data[i]["scl"]
                mod.updata_from_data(f"Picker_{mod.name}")
                i += 1