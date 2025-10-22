from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, guide_base
reload(core)
reload(guide_base)

class Guide(guide_base.GuideBase):
    def setup(self, *args):
        self.aim_vector = [0, 0, 1]

    def create(self):
        core.create_hierarchy(
        self.facials_grp,
            self.grp, ":",
                self.root_joint
        )
        joint_names = [self.grp_name, f"{self.grp_name}_GB"]
        guide_joints = [None] * self.joint_count
        guide_joint_spaces = [None] * self.joint_count
        guide_proxies = [None] * self.joint_count
        guide_nodes = [None] * self.joint_count
        guide_node_spaces = [None] * self.joint_count

        for i, name in enumerate(joint_names):
            guide_proxy = core.create_guide_joint("GUideProxy", name)
            guide_node = core.create_guide_node(name)
            guide_node_space = core.create_space(guide_node)
            if i:
                guide_joint = core.create_guide_joint("Guide", name, show_label=False)

            else:
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

        self.joint_names = joint_names
        self.guide_joints = guide_joints
        self.guide_joint_spaces = guide_joint_spaces
        self.guide_proxies = guide_proxies
        self.guide_nodes = guide_nodes
        self.guide_node_spaces = guide_node_spaces

    def connect(self):
        dm = core.create_node("decomposeMatrix", f"Dm_{self.guide_joint_spaces[1]}")
        cmds.connectAttr(f"{self.guide_joints[0]}.worldInverseMatrix[0]", f"{dm}.inputMatrix")
        for axis in "XYZ":
            cmds.connectAttr(f"{dm}.outputTranslate{axis}", f"{self.guide_joint_spaces[1]}.translate{axis}")

    def lock_attributes(self):
        cmds.setAttr(f"{self.settings_node}.GoalBone", True)
        self.lock_attrs = [
        self.root_joint, ["tx", "rotate"],
        self.guide_joints[-1], ["tx"],
        self.settings_node, ["Orient", "Mirror", "TranslateEnabled", "ConnectType"]
        ]

    def apply_settings(self, root_matrix=[0, 0, 0, 0, 0, 0, 1], guide_positions=[[0, 0, 10]], goal_bone=True):
        if self.error:
            return
        
        cmds.setAttr(f"{self.root_joint}.translateY", root_matrix[1])
        cmds.setAttr(f"{self.root_joint}.translateZ", root_matrix[2])
        cmds.setAttr(f"{self.root_joint}.UniformScale", root_matrix[6])

        cmds.setAttr(f"{self.guide_joints[-1]}.translateY", guide_positions[0][1])
        cmds.setAttr(f"{self.guide_joints[-1]}.translateZ", guide_positions[0][2])

        cmds.setAttr(f"{self.settings_node}.GoalBone", goal_bone)

        cmds.undoInfo(cck=True)


def build(data):
    pos, rot, scl = core.decompose_matrix(data["RootMatrix"])

    G = Guide(data["GroupName"], data["JointCount"], data["ParentName"], data["Side"])
    G.apply_settings(root_matrix=[*pos, *rot, scl[0]], goal_bone=data["GoalBone"])

    core.meta_node_apply_settings(G, data)

    pos = core.decompose_matrix(data["GuideJointsMatrix"][1])[0]
    cmds.setAttr(f"{G.guide_joints[1]}.translateY", pos[1])
    cmds.setAttr(f"{G.guide_joints[1]}.translateZ", pos[2])