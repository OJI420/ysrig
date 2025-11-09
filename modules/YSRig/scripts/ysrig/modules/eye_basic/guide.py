from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, guide_base
reload(core)
reload(guide_base)

class Guide(guide_base.GuideBase):
    def setup(self, *args):
        self.joint_names = args[0]
        self.aim_vector = [0, 0, 1]

    def create(self):
        core.create_hierarchy(
        self.facials_grp,
            self.grp, ":",
                self.root_joint
        )
        joint_names = self.joint_names
        guide_joints = [None] * 2
        guide_joint_spaces = [None] * 2
        guide_proxies = [None] * 2
        guide_nodes = [None] * 2
        guide_node_spaces = [None] * 2
        other_nodes = [None]
        other_node_spaces = [None]

        guide_proxies[0] = core.create_guide_joint("GUideProxy", joint_names[0], radius=0)
        guide_proxies[1] = core.create_guide_joint("GUideProxy", joint_names[1], radius=0)
        guide_nodes[0] = core.create_guide_node(joint_names[0])
        guide_nodes[1] = core.create_guide_node(joint_names[1])
        guide_node_spaces[0] = core.create_space(guide_nodes[0])
        guide_node_spaces[1] = core.create_space(guide_nodes[1])
        guide_joints[0] = core.create_guide_joint("Guide", joint_names[0], radius=1, show_label=False)
        guide_joints[1] = core.create_guide_joint("Guide", joint_names[1], color=[0.6, 0.3, 0.0], radius=0.5, show_label=False)
        guide_joint_spaces[0] = core.create_space(guide_joints[0])
        guide_joint_spaces[1] = core.create_space(guide_joints[1])
        other_nodes[0] = core.create_guide_joint("Guide", f"{joint_names[0]}_Aim", color=[0.0, 0.0, 1.0], radius=0.1)
        other_node_spaces[0] = core.create_space(other_nodes[0])

        core.create_hierarchy(
        self.root_joint,
            guide_proxies[0], ":",
                guide_node_spaces[0], ":",
                    guide_nodes[0], "..",
                guide_proxies[1], ":",
                    guide_node_spaces[1], ":",
                        guide_nodes[1], "..", "..", "..",
            guide_joint_spaces[0], ":",
                guide_joints[0], ":",
                    guide_joint_spaces[1], ":",
                        guide_joints[1], "..",
                    other_node_spaces[0], ":",
                        other_nodes[0]
            )

        self.joint_names = joint_names
        self.guide_joints = guide_joints
        self.guide_joint_spaces = guide_joint_spaces
        self.guide_proxies = guide_proxies
        self.guide_nodes = guide_nodes
        self.guide_node_spaces = guide_node_spaces
        self.other_nodes = other_nodes
        self.other_node_spaces = other_node_spaces

    def lock_attributes(self):
        self.lock_attrs = [
        self.other_nodes[0], ["tx", "ty", "rotate", "scale", "visibility"],
        self.settings_node, ["Orient", "GoalBone", "TranslateEnabled", "ConnectType", "Mirror"]
        ]

        cmds.transformLimits(self.guide_joints[1], tz=[0, 0], etz=[1, 0])
        cmds.transformLimits(self.other_nodes[0], tz=[0, 0], etz=[1, 0])

    def post_process(self):
        cmds.setAttr(f"{self.guide_nodes[0]}.displayLocalAxis", False)

    def apply_settings(self, root_matrix=[0, 0, 0, 0, 0, 0, 1], guide_positions=[[0, 0, 1], [0, 0, 40]]):
        if self.error:
            return
        
        cmds.setAttr(f"{self.root_joint}.UniformScale", root_matrix[6])

        cmds.setAttr(f"{self.guide_joint_spaces[1]}.translateZ", 0.1)

        cmds.setAttr(f"{self.root_joint}.translate", root_matrix[0], root_matrix[1], root_matrix[2])
        cmds.setAttr(f"{self.guide_joints[1]}.translate", guide_positions[0][0], guide_positions[0][1], guide_positions[0][2])
        cmds.setAttr(f"{self.other_nodes[0]}.translateZ", guide_positions[1][2])

        cmds.undoInfo(cck=True)

def build(data):
    pos, rot, scl = core.decompose_matrix(data["RootMatrix"])

    G = Guide(data["GroupName"], data["JointCount"], data["ParentName"], data["Side"], data["JointName"])
    G.apply_settings(root_matrix=[*pos, *rot, scl[0]], guide_positions=[core.decompose_matrix(data["GuideJointsMatrix"][1])[0], core.decompose_matrix(data["OtherGuidesMatrix"][0])[0]])

    core.meta_node_apply_settings(G, data)