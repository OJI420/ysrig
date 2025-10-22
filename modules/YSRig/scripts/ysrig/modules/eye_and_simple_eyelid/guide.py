from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core
from ysrig.modules.eye_basic import guide
reload(core)
reload(guide)

class Guide(guide.Guide):
    def create(self):
        super().create()

        self.guide_nodes += [core.create_guide_node(self.joint_names[2])]
        self.guide_nodes += [core.create_guide_node(self.joint_names[3])]
        self.guide_node_spaces += [core.create_space(self.guide_nodes[2])]
        self.guide_node_spaces += [core.create_space(self.guide_nodes[3])]
        core.create_hierarchy(
        self.guide_nodes[0],
            self.guide_node_spaces[2], ":",
                self.guide_nodes[2], "..",
            self.guide_node_spaces[3], ":",
                self.guide_nodes[3]
        )


def build(data):
    pos, rot, scl = core.decompose_matrix(data["RootMatrix"])

    G = Guide(data["GroupName"], data["JointCount"], data["ParentName"], data["Side"], data["JointName"])
    G.apply_settings(root_matrix=[*pos, *rot, scl[0]], guide_positions=[core.decompose_matrix(data["GuideJointsMatrix"][1])[0], core.decompose_matrix(data["OtherGuidesMatrix"][0])[0]])

    core.meta_node_apply_settings(G, data)

    if not "EyelidPitchFollowWeight" in data:
        return

    meta_data = {}
    meta_data["EyelidPitchFollowWeight"] = data["EyelidPitchFollowWeight"]
    meta_data["EyelidYawFollowWeight"] = data["EyelidYawFollowWeight"]
    meta_data["EyelidCloseAngle"] = data["EyelidCloseAngle"]
    meta_data["PupilDepthWeight"] = data["PupilDepthWeight"]
    core.dict_to_attr(G.meta_node, meta_data)