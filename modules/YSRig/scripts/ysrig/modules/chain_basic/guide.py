from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, guide_base
from ysrig.modules.chain_basic import gui
reload(core)
reload(guide_base)

class Guide(guide_base.GuideBase):
    def setup(self, *args):
        self.ctrl_shape_type = args[0]
        self.joint_count += 1

    def add_settings(self):
        cmds.addAttr(self.settings_node, ln="ControllrShapeType", at="enum", en=self.ctrl_shape_type, k=True)

    def create(self):
        core.create_hierarchy(
        self.modules_grp,
            self.grp, ":",
                self.root_joint
        )
        joint_names = core.create_numbered_names(self.grp_name, self.joint_count)
        guide_joints = [None] * self.joint_count
        guide_joint_spaces = [None] * self.joint_count
        guide_proxies = [None] * self.joint_count
        guide_nodes = [None] * self.joint_count
        guide_node_spaces = [None] * self.joint_count

        if self.joint_count == 2:
            joint_names[0] = self.grp_name[:]

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

        self.joint_names = joint_names
        self.guide_joints = guide_joints
        self.guide_joint_spaces = guide_joint_spaces
        self.guide_proxies = guide_proxies
        self.guide_nodes = guide_nodes
        self.guide_node_spaces = guide_node_spaces

    def connect(self):
        if self.joint_count > 2:
            core.connect_equal_point(self.guide_joints)

    def collect_meta_data(self):
        self.meta_data["ControllrShapeType"] = core.compose_attr_paths(self.settings_node, "ControllrShapeType")
        self.meta_data["Orient"] = core.compose_attr_paths(self.settings_node, "Orient")

    def apply_settings(self, root_matrix=[0, 0, 0, 0, 0, 0, 1], guide_positions=[[10, 0, 0]],
    orient=0, goal_bone=True, mirror=True, connect_type=1, translate_enabled=True, ctrl_shape_type=0):
        if self.error:
            return

        cmds.setAttr(f"{self.root_joint}.translate", root_matrix[0], root_matrix[1], root_matrix[2])
        cmds.setAttr(f"{self.root_joint}.rotate", root_matrix[3], root_matrix[4], root_matrix[5])
        cmds.setAttr(f"{self.root_joint}.UniformScale", root_matrix[6])

        cmds.setAttr(f"{self.guide_joints[-1]}.translate", guide_positions[0][0], guide_positions[0][1], guide_positions[0][2])

        cmds.setAttr(f"{self.settings_node}.Orient", orient)
        cmds.setAttr(f"{self.settings_node}.GoalBone", goal_bone)
        cmds.setAttr(f"{self.settings_node}.Mirror", mirror)
        cmds.setAttr(f"{self.settings_node}.TranslateEnabled", translate_enabled)
        cmds.setAttr(f"{self.settings_node}.ConnectType", connect_type)
        cmds.setAttr(f"{self.settings_node}.ControllrShapeType", ctrl_shape_type)

        cmds.undoInfo(cck=True)

def build(data):
    pos, rot, scl = core.decompose_matrix(data["RootMatrix"])

    G = Guide(data["GroupName"], data["JointCount"] - 1, data["ParentName"], data["Side"], ":".join(gui.CTRL_SHAPE_TYPE))
    G.apply_settings(root_matrix=[*pos, *rot, scl[0]], 
                    orient=data["Orient"], goal_bone=data["GoalBone"], mirror=data["Mirror"], connect_type=data["ConnectType"], translate_enabled=data["TranslateEnabled"], ctrl_shape_type=data["ControllrShapeType"])

    core.meta_node_apply_settings(G, data)

    for guide, matrix in zip(G.guide_joints[1:], data["GuideJointsMatrix"][1:]):
        pos = core.decompose_matrix(matrix)[0]
        cmds.setAttr(f"{guide}.translate", *pos)