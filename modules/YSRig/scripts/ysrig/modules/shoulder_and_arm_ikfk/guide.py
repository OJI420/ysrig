from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, guide_base
from ysrig.modules.shoulder_and_arm_ikfk import gui
reload(core)
reload(guide_base)

class Guide(guide_base.GuideBase):
    def setup(self, *args):
        self.joint_names = args[0]
        self.ik_ctrl_shape_type = args[1]
        self.pv_ctrl_shape_type = args[2]

        self.joint_count = 5
        self.connect_aim_axis = "YZ"

    def add_settings(self):
        cmds.addAttr(self.settings_node, ln="IKControllrShapeType", at="enum", en=self.ik_ctrl_shape_type, k=True)
        cmds.addAttr(self.settings_node, ln="PVControllrShapeType", at="enum", en=self.pv_ctrl_shape_type, k=True)
        cmds.addAttr(self.settings_node, ln="TwistJointCount", at="long", min=0, dv=0, k=True)

    def create(self):
        core.create_hierarchy(
        self.modules_grp,
            self.grp, ":",
                self.root_joint
        )
        joint_names = self.joint_names + [f"{self.joint_names[-1]}_GB"]
        guide_joints = [None] * self.joint_count
        guide_joint_spaces = [None] * self.joint_count
        guide_proxies = [None] * self.joint_count
        guide_nodes = [None] * self.joint_count
        guide_node_spaces = [None] * self.joint_count

        for i, name in enumerate(joint_names):
            guide_proxy = core.create_guide_joint("GUideProxy", name)
            guide_node = core.create_guide_node(name)
            guide_node_space = core.create_space(guide_node)
            guide_joint = core.create_guide_joint("Guide", name)
            guide_joint_space = core.create_space(guide_joint)

            if i:
                parent = guide_proxies[i - 1]

            else:
                parent = self.root_joint

            core.create_hierarchy(
            parent,
                guide_proxy, ":",
                    guide_node_space, ":",
                        guide_node
            )

            core.create_hierarchy(
            self.root_joint,
                guide_joint_space, ":",
                    guide_joint
            )

            guide_joints[i] = guide_joint
            guide_joint_spaces[i] = guide_joint_space
            guide_proxies[i] = guide_proxy
            guide_nodes[i] = guide_node
            guide_node_spaces[i] = guide_node_space

        pv_guide = core.create_guide_joint("Guide", f"{self.grp_name}_PV", color=[0.0, 0.0, 1.0], radius=0.2)
        pv_guide_space = core.create_space(pv_guide)
        core.create_hierarchy(
        guide_joints[2],
            pv_guide_space, ":",
                pv_guide
        )

        self.joint_names = joint_names
        self.guide_joints = guide_joints
        self.guide_joint_spaces = guide_joint_spaces
        self.guide_proxies = guide_proxies
        self.guide_nodes = guide_nodes
        self.guide_node_spaces = guide_node_spaces
        self.other_nodes = [pv_guide]
        self.other_node_spaces = [pv_guide_space]

    def connect(self):
        core.connect_equal_point(self.guide_joints[1:-1])
        core.connect_aim_constraint(self.guide_joints[3], self.guide_joint_spaces[2])
        cmds.connectAttr(f"{self.settings_node}.Orient", f"{self.guide_joint_spaces[2]}.rotateX", f=True)

    def lock_attributes(self):
        cmds.setAttr(f"{self.settings_node}.Orient", 90)
        self.lock_attrs = [
        self.settings_node, ["Orient", "TranslateEnabled"],
        self.guide_joints[2], ["tx", "tz"],
        self.other_nodes[0], ["tx", "tz", "rotate", "scale", "visibility"]
        ]
        cmds.transformLimits(self.guide_joints[2], ty=[0, 0], ety=[0, 1])
        cmds.transformLimits(self.other_nodes[0], ty=[0, 0], ety=[0, 1])

    def collect_meta_data(self):
        self.meta_data["IKControllrShapeType"] = core.compose_attr_paths(self.settings_node, "IKControllrShapeType")
        self.meta_data["PVControllrShapeType"] = core.compose_attr_paths(self.settings_node, "PVControllrShapeType")
        self.meta_data["TwistJointCount"] = core.compose_attr_paths(self.settings_node, "TwistJointCount")

    def apply_settings(self, root_matrix=[0, 0, 0, 0, 0, 0, 1], guide_positions=[[10, 0, 0], [50, 0, 0], [70, 0, 0]], pv_position=-40,
    goal_bone=True, mirror=True ,connect_type=1, ik_ctrl_shape_type=0, pv_ctrl_shape_type=1, twist_joint_count=0):
        if self.error:
            return
        
        cmds.setAttr(f"{self.root_joint}.translate", root_matrix[0], root_matrix[1], root_matrix[2])
        cmds.setAttr(f"{self.root_joint}.rotate", root_matrix[3], root_matrix[4], root_matrix[5])
        cmds.setAttr(f"{self.root_joint}.UniformScale", root_matrix[6])

        cmds.setAttr(f"{self.guide_joints[1]}.translate", guide_positions[0][0], guide_positions[0][1], guide_positions[0][2])
        cmds.setAttr(f"{self.guide_joints[3]}.translate", guide_positions[1][0], guide_positions[1][1], guide_positions[1][2])
        cmds.setAttr(f"{self.guide_joints[4]}.translate", guide_positions[2][0], guide_positions[2][1], guide_positions[2][2])

        cmds.setAttr(f"{self.other_node_spaces[0]}.translateY", -1)
        cmds.setAttr(f"{self.other_nodes[0]}.translateY", pv_position)

        cmds.setAttr(f"{self.settings_node}.GoalBone", goal_bone)
        cmds.setAttr(f"{self.settings_node}.Mirror", mirror)
        cmds.setAttr(f"{self.settings_node}.ConnectType", connect_type)
        cmds.setAttr(f"{self.settings_node}.IKControllrShapeType", ik_ctrl_shape_type)
        cmds.setAttr(f"{self.settings_node}.PVControllrShapeType", pv_ctrl_shape_type)
        cmds.setAttr(f"{self.settings_node}.TwistJointCount", twist_joint_count)

        cmds.undoInfo(cck=True)


def build(data):
    pos, rot, scl = core.decompose_matrix(data["RootMatrix"])

    G = Guide(data["GroupName"], data["JointCount"], data["ParentName"], data["Side"], data["JointName"][:-1], ":".join(gui.IK_CTRL_SHAPE_TYPE), ":".join(gui.PV_CTRL_SHAPE_TYPE))
    G.apply_settings(root_matrix=[*pos, *rot, scl[0]], pv_position=core.decompose_matrix(data["OtherGuidesMatrix"][0])[0][1],
                    goal_bone=data["GoalBone"], mirror=data["Mirror"], connect_type=data["ConnectType"], ik_ctrl_shape_type=data["IKControllrShapeType"], pv_ctrl_shape_type=data["PVControllrShapeType"], twist_joint_count=data["TwistJointCount"])

    core.meta_node_apply_settings(G, data)

    for i, guide, matrix in zip(range(4), G.guide_joints[1:], data["GuideJointsMatrix"][1:]):
        pos = core.decompose_matrix(matrix)[0]
        if i == 1:
            cmds.setAttr(f"{guide}.translateY", pos[1])

        else:
            cmds.setAttr(f"{guide}.translate", *pos)