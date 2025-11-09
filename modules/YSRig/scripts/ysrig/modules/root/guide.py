from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, guide_base
reload(core)
reload(guide_base)

class Guide(guide_base.GuideBase):
    def _handle_error(self):
        if cmds.objExists(core.get_root_group()):
            MGlobal.displayError(f"'{core.get_root_group()}' はすでに存在しています")
            self.error = True
            return

        if cmds.objExists(core.get_guide_group()):
            MGlobal.displayError(f"'{core.get_guide_group()}' はすでに存在しています")
            self.error = True
            return

        if cmds.objExists(f"Guide_{self.grp_name}_Group"):
            MGlobal.displayError(f"'{self.grp_name}' はすでに存在しています")
            self.error = True
            return

    def create(self):
        self.rig_group = core.create_rig_grp()
        self.guide_group = core.create_labeled_node("transform", core.get_guide_group(), name=core.get_guide_group())
        self.guide_modules_group = core.create_labeled_node("transform", core.get_guide_modules_group(), name=core.get_guide_modules_group())
        self.guide_facials_group = core.create_labeled_node("transform", core.get_guide_facials_group(), name=core.get_guide_facials_group())
        cmds.addAttr(self.guide_facials_group, ln="FacialRootName", dt="string")
        cmds.setAttr(f"{self.guide_facials_group}.FacialRootName", l=True)
        name = "Root"

        self.joint_names = [name]
        self.guide_joints = [core.create_guide_joint("Guide", name)]
        self.guide_joint_spaces = [core.create_space(self.guide_joints[0])]
        self.guide_proxies = [core.create_guide_joint("GUideProxy", name)]
        self.guide_nodes = [core.create_guide_node(name)]
        self.guide_node_spaces = [core.create_space(self.guide_nodes[0])]

        core.create_hierarchy(
        self.rig_group,
            self.guide_group, ":",
                self.grp, ":",
                    self.root_joint, ":",
                        self.guide_proxies[0], ":",
                            self.guide_node_spaces[0], ":",
                                self.guide_nodes[0], "..", "..", "..",
                    self.guide_joint_spaces[0], ":",
                        self.guide_joints[0], "..", "..",
                self.guide_modules_group, ":",
                    self.guide_facials_group
        )

        root_curev = core.Curve("tmp", "Root")
        root_curev.set_scale(50)
        root_curev.set_width(2)
        root_curev.set_shape_color([1, 0, 0])
        root_curev.reparent_shape(self.root_joint)

    def _connect(self):
        cmds.addAttr(self.root_joint, ln="UniformScale", at="double", min=0.1, dv=1.0, k=True)
        for axis in "XYZ":
            cmds.connectAttr(f"{self.root_joint}.UniformScale", f"{self.root_joint}.scale{axis}")
            cmds.connectAttr(f"{self.root_joint}.UniformScale", f"{self.guide_modules_group}.scale{axis}")

    def lock_attributes(self):
        self.lock_attrs = [
        self.grp, ["translate", "rotate", "scale"],
        self.root_joint, ["translate", "rotate", "radius"],
        self.settings_node, ["Orient", "GoalBone", "Mirror", "TranslateEnabled", "ConnectType"]
        ]

    def collect_meta_data(self):
        self.meta_data["FacialRootName"] = core.compose_attr_paths(self.guide_facials_group, "FacialRootName")

    def _post_process(self):
        cmds.setAttr(f"{self.root_joint}.otherType", self.joint_names[0], type="string")
        cmds.setAttr(f"{self.root_joint}.displayHandle", False)
        cmds.setAttr(f"{self.root_joint}.drawStyle", 2)

        cmds.setAttr(f"{self.guide_joints[0]}.drawStyle", 2)
        cmds.setAttr(f"{self.guide_joints[0]}.drawLabel", False)
        cmds.setAttr(f"{self.guide_joints[0]}.displayHandle", False)
        cmds.setAttr(f"{self.guide_joints[0]}.displayLocalAxis", False)

        cmds.setAttr(f"{self.guide_nodes[0]}.displayLocalAxis", True)

    def apply_settings(self, root_matrix=[0, 0, 0, 0, 0, 0, 1]):
        if self.error:
            return
        
        cmds.setAttr(f"{self.root_joint}.UniformScale", root_matrix[6])


def main():
    G = Guide("Root", 1, "", "")
    G.apply_settings()


def build(data):
    root_scale = core.decompose_matrix(data["RootMatrix"])

    G = Guide("Root", 1, "", "")
    G.apply_settings(root_matrix=[0, 0, 0, 0, 0, 0, root_scale[2][0]])

    if "LineWidth" in data:
        meta_data = {}
        meta_data["CtrlsMatrix"] = core.list_to_tuple(data["CtrlsMatrix"])
        meta_data["LineWidth"] = data["LineWidth"]
        core.dict_to_attr(G.meta_node, meta_data)