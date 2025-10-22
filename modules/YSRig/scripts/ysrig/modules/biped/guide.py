from maya import cmds
from ysrig import core
from ysrig.modules import root, spine_basic, neck_and_head_basic, shoulder_and_arm_ikfk, leg_and_foot_ikfk, finger_fk, eye_basic, eye_and_simple_eyelid, jaw_basic, biped

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

    def root(self):
        root.guide.main()

    def spine(self):
        guide = spine_basic.guide.Guide("Spine", self.spine_count, "Root", "", ["Hip"])
        guide.apply_settings(root_matrix=[0, 100, 0, 0, 0, 0, 1], guide_positions=[[5, 0, 0], [30, 0, 0]], connect_type=self.connect_type)
        self.spine_gb = guide.joint_names[-1]

    def neck(self):
        guide = neck_and_head_basic.guide.Guide("Neck", self.neck_count, self.spine_gb, "", ["Head"])
        guide.apply_settings(root_matrix=[0, 150, 0, 0, 0, 0, 1], guide_positions=[[10, 0, 0], [15, 0, 0], [30, 0, 0]], connect_type=self.connect_type)

    def arm(self):
        guide = shoulder_and_arm_ikfk.guide.Guide("L_Arm", 0, self.spine_gb, "L_", ["L_Shoulder", "L_UpperArm", "L_ForeArm", "L_Hand"],
                                                ":".join(shoulder_and_arm_ikfk.gui.IK_CTRL_SHAPE_TYPE), ":".join(shoulder_and_arm_ikfk.gui.PV_CTRL_SHAPE_TYPE))
        guide.apply_settings(root_matrix=[5, 145, 0, 0, 0, 0, 1], guide_positions=[[10, 0, 0], [50, 0, 0], [75, 0, 0]], connect_type=self.connect_type, twist_joint_count=self.arm_tj_count, goal_bone=not self.use_finger)

    def finger(self):
        guide = finger_fk.guide.Guide("L_Finger", 0, "L_Hand", "L_", self.finger_names, self.carpal_flags, ":".join(finger_fk.gui.CTRL_SHAPE_TYPE))
        guide.apply_settings(root_matrix=[55, 155, 0, 0, 0, 0, 1], guide_positions=[[10, -10, 0], [10, 0, 0]])

    def leg(self):
        guide = leg_and_foot_ikfk.guide.Guide("L_Leg", 0, "Hip", "L_", ["L_UpperLeg", "L_ForeLeg", "L_Foot", "L_Toe", "L_ToeSub"], self.tiptoe, ":".join(leg_and_foot_ikfk.gui.PV_CTRL_SHAPE_TYPE))
        guide.apply_settings(root_matrix=[15, 100, 0, 0, 0, 0, 1], guide_positions=[[90, 0, 0], [5, 0, 20]], connect_type=self.connect_type, twist_joint_count=self.leg_tj_count, pv_ctrl_shape_type=3)

    def jaw(self):
        guide = jaw_basic.guide.Guide("Jaw", 2, core.get_facials_root(), "")
        guide.apply_settings(root_matrix=[0, 165, 5, 0, 0, 0, 1], guide_positions=[[0, 165, 10]], goal_bone=False)

    def eyes(self):
        if self.eyelid:
            guide = eye_and_simple_eyelid.guide.Guide("Eyes", 4, core.get_facials_root(), "", ["L_Eye", "L_Pupil", "L_Eyelid_Top", "L_Eyelid_Bottom"])

        else:
            guide = eye_basic.guide.Guide("Eyes", 2, core.get_facials_root(), "", ["L_Eye", "L_Eye_GB"])

        guide.apply_settings(root_matrix=[5, 170, 10, 0, 0, 0, 1], guide_positions=[[0, 0, 1], [0, 0, 40]])

    def set_attr(self):
        attrs = [
            [f"{core.get_root_group()}.YSRigVersion", core.VERSION],
            [f"{core.get_root_group()}.BuildType", "Biped"],
            [f"{core.get_guide_facials_group()}.FacialRootName", "Head"]
        ]

        for attr in attrs:
            cmds.setAttr(attr[0], l=False)
            cmds.setAttr(*attr, l=True, type="string")