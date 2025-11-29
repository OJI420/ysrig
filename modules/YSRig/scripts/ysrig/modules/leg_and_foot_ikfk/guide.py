from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, guide_base
from ysrig.modules.leg_and_foot_ikfk import gui
reload(core)
reload(guide_base)
reload(gui)

class Guide(guide_base.GuideBase):
    def setup(self, *args):
        self.joint_names = args[0]
        if not args[1]:
            self.joint_names = self.joint_names[:-1]

        self.pv_ctrl_shape_type = args[2]

        self.joint_count = len(self.joint_names) + 1
        self.connect_aim_axis = "YZ"

    def add_settings(self):
        cmds.addAttr(self.settings_node, ln="PVControllrShapeType", at="enum", en=self.pv_ctrl_shape_type, k=True)
        cmds.addAttr(self.settings_node, ln="TwistJointCount", at="long", min=0, dv=0, k=True)

    def create(self):
        core.create_hierarchy(
            self.modules_grp,
                self.grp, ":",
                    self.root_joint
        )
        joint_names = self.joint_names + [f"{self.joint_names[3]}_GB"]
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
                proxies_parent = guide_proxies[i - 1]

            else:
                proxies_parent = self.root_joint

            core.create_hierarchy(
                proxies_parent,
                    guide_proxy, ":",
                        guide_node_space, ":",
                            guide_node
            )

            if i > 2:
                guide_parent = guide_joints[2]

            else:
                guide_parent = self.root_joint

            core.create_hierarchy(
                guide_parent,
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
            guide_joints[1],
                pv_guide_space, ":",
                    pv_guide
        )

        rev_guides = [None] * 6
        rev_guide_space = [None] * 6
        for i, name in enumerate(["Center", "Heel", "OutSide", "InSide", "ToeTip", "All"]):
            rev_guides[i] = core.create_guide_joint("Guide", f"{self.grp_name}_REV_{name}", color=[0.0, 0.0, 1.0], label=name ,radius=0.1)
            rev_guide_space[i] = core.create_space(rev_guides[i])
            if i == 2 or i == 3:
                parent = rev_guides[0]
            
            else:
                parent = guide_joints[2]

            core.create_hierarchy(
                parent,
                    rev_guide_space[i], ":",
                        rev_guides[i]
            )

        self.joint_names = joint_names
        self.guide_joints = guide_joints
        self.guide_joint_spaces = guide_joint_spaces
        self.guide_proxies = guide_proxies
        self.guide_nodes = guide_nodes
        self.guide_node_spaces = guide_node_spaces
        self.other_nodes = [pv_guide] + rev_guides
        self.other_node_spaces = [pv_guide_space] + rev_guide_space

    def connect(self):
        core.connect_equal_point(self.guide_joints[0:3])
        core.connect_aim_constraint(self.guide_joints[2], self.guide_joint_spaces[1])
        cmds.connectAttr(f"{self.settings_node}.Orient", f"{self.guide_joint_spaces[1]}.rotateX", f=True)

        core.connect_equal_point([self.guide_joints[2], self.guide_joints[3], self.guide_joints[-1]], offset=False)
        if self.joint_count == 6:
            core.connect_equal_point(self.guide_joints[3:])

        cmds.delete(self.aim_nodes[2])
        cmds.setAttr(f"{self.guide_node_spaces[2]}.rotate", 0, 0, 0)
        self.aim_nodes[2] = core.connect_aim_constraint(self.guide_nodes[3], self.guide_nodes[2])
        core.connect_orient_constraint(self.guide_joints[2], self.guide_proxies[2])

        dm = core._create_node("decomposeMatrix", f"Dm_{self.other_nodes[1]}")
        cmds.connectAttr(f"{self.guide_joints[2]}.worldInverseMatrix[0]", f"{dm}.inputMatrix")
        cmds.connectAttr(f"{dm}.outputTranslateX", f"{self.other_node_spaces[1]}.translateX")
        cmds.connectAttr(f"{dm}.outputTranslateX", f"{self.other_node_spaces[2]}.translateX")
        cmds.connectAttr(f"{dm}.outputTranslateX", f"{self.other_node_spaces[5]}.translateX")
        cmds.connectAttr(f"{dm}.outputTranslateX", f"{self.other_node_spaces[6]}.translateX")

    def _lock_attributes(self):
        cmds.setAttr(f"{self.root_joint}.rotateZ", -90)
        cmds.setAttr(f"{self.settings_node}.Orient", 90)

        self._lock_attrs = [
        self.grp, ["scale"],
        self.root_joint, ["ry", "rz", "scale", "visibility"],
        self.guide_joints[0], ["translate", "rotate", "scale", "visibility"],
        self.settings_node, ["Orient", "TranslateEnabled"],
        self.guide_joints[1], ["tx", "tz", "rotate", "scale", "visibility"],
        self.guide_joints[2], ["ry", "rz", "scale", "visibility"],
        self.other_nodes[0], ["tx", "tz", "rotate", "scale", "visibility"],
        self.other_nodes[1], ["tx", "ty", "rotate", "scale", "visibility"],
        self.other_nodes[2], ["tx", "ty", "rotate", "scale", "visibility"],
        self.other_nodes[3], ["tx", "tz", "rotate", "scale", "visibility"],
        self.other_nodes[4], ["tx", "tz", "rotate", "scale", "visibility"],
        self.other_nodes[5], ["tx", "ty", "rotate", "scale", "visibility"],
        self.other_nodes[6], ["tx", "ty", "rotate", "scale", "visibility"]
        ]

        for gj in self.guide_joints[3:]:
            self._lock_attrs += [
            gj, ["ty", "rotate", "scale", "visibility"]
            ]
        
        cmds.transformLimits(self.guide_joints[1], ty=[0, 0], ety=[1, 0])
        cmds.transformLimits(self.other_nodes[0], ty=[0, 0], ety=[1, 0])

    def collect_meta_data(self):
        self.meta_data["PVControllrShapeType"] = core.compose_attr_paths(self.settings_node, "PVControllrShapeType")
        self.meta_data["TwistJointCount"] = core.compose_attr_paths(self.settings_node, "TwistJointCount")

    def apply_settings(self, root_matrix=[0, 0, 0, 0, 0, 0, 1], guide_positions=[[80, 0, 0], [10, 0, 20]], pv_position=50, rev_positions=[10, -10, 10, -10, 20, 40],
    goal_bone=True, mirror=True, connect_type=1, pv_ctrl_shape_type=0, twist_joint_count=0):
        if self.error:
            return
        
        cmds.setAttr(f"{self.root_joint}.translate", root_matrix[0], root_matrix[1], root_matrix[2])
        cmds.setAttr(f"{self.root_joint}.rotateX", root_matrix[3])
        cmds.setAttr(f"{self.root_joint}.UniformScale", root_matrix[6])

        cmds.setAttr(f"{self.guide_joints[2]}.translate", guide_positions[0][0], guide_positions[0][1], guide_positions[0][2])
        cmds.setAttr(f"{self.guide_joints[-1]}.translateX", guide_positions[1][0])
        cmds.setAttr(f"{self.guide_joints[-1]}.translateZ", guide_positions[1][2])

        cmds.setAttr(f"{self.other_node_spaces[0]}.translateY", 1)
        cmds.setAttr(f"{self.other_node_spaces[2]}.translateZ", -1)
        cmds.setAttr(f"{self.other_node_spaces[3]}.translateY", 1)
        cmds.setAttr(f"{self.other_node_spaces[4]}.translateY", -1)
        cmds.setAttr(f"{self.other_node_spaces[5]}.translateZ", 1)
        cmds.setAttr(f"{self.other_nodes[0]}.translateY", pv_position)
        cmds.setAttr(f"{self.other_nodes[1]}.translateZ", rev_positions[0])
        cmds.setAttr(f"{self.other_nodes[2]}.translateZ", rev_positions[1])
        cmds.setAttr(f"{self.other_nodes[3]}.translateY", rev_positions[2])
        cmds.setAttr(f"{self.other_nodes[4]}.translateY", rev_positions[3])
        cmds.setAttr(f"{self.other_nodes[5]}.translateZ", rev_positions[4])
        cmds.setAttr(f"{self.other_nodes[6]}.translateZ", rev_positions[5])

        cmds.setAttr(f"{self.settings_node}.GoalBone", goal_bone)
        cmds.setAttr(f"{self.settings_node}.Mirror", mirror)
        cmds.setAttr(f"{self.settings_node}.ConnectType", connect_type)
        cmds.setAttr(f"{self.settings_node}.PVControllrShapeType", pv_ctrl_shape_type)
        cmds.setAttr(f"{self.settings_node}.TwistJointCount", twist_joint_count)

        cmds.undoInfo(cck=True)


def build(data):
    pos, rot, scl = core.decompose_matrix(data["RootMatrix"])

    G = Guide(data["GroupName"], data["JointCount"] - 1, data["ParentName"], data["Side"], data["JointName"][:-1], data["JointCount"] == 6, ":".join(gui.PV_CTRL_SHAPE_TYPE))
    G.apply_settings(root_matrix=[*pos, *rot, scl[0]], pv_position=core.decompose_matrix(data["OtherGuidesMatrix"][0])[0][1],
                    goal_bone=data["GoalBone"], mirror=data["Mirror"], connect_type=data["ConnectType"], pv_ctrl_shape_type=data["PVControllrShapeType"], twist_joint_count=data["TwistJointCount"])

    core.meta_node_apply_settings(G, data)

    for i, guide, matrix in zip(range(G.joint_count), G.guide_joints[1:], data["GuideJointsMatrix"][1:]):
        pos, rot = core.decompose_matrix(matrix)[:-1]
        if i == 0:
            cmds.setAttr(f"{guide}.translateY", pos[1])

        elif i == 1:
            cmds.setAttr(f"{guide}.translate", *pos)
            cmds.setAttr(f"{guide}.rotateX", rot[0])

        else:
            cmds.setAttr(f"{guide}.translateX", pos[0])
            cmds.setAttr(f"{guide}.translateZ", pos[2])

    for i, guide, matrix in zip(range(6), G.other_nodes[1:], data["OtherGuidesMatrix"][1:]):
        pos = core.decompose_matrix(matrix)[0]
        if i == 2 or i == 3:
            cmds.setAttr(f"{guide}.translateY", pos[1])

        else:
            cmds.setAttr(f"{guide}.translateZ", pos[2])

    if not "ToeLiftThreshold" in data:
        return

    meta_data = {}
    meta_data["ToeLiftThreshold"] = data["ToeLiftThreshold"]
    meta_data["ToeContactAngle"] = data["ToeContactAngle"]
    core.dict_to_attr(G.meta_node, meta_data)