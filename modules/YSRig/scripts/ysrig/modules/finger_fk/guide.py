from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, guide_base
from ysrig.modules.finger_fk import gui
reload(core)
reload(guide_base)

class Guide(guide_base.GuideBase):
    def setup(self, *args):
        self.finger_names = args[0]
        self.carpal_flags = args[1]
        self.carpal = False
        self.fk_ctrl_shape_type = args[2]
        self.finger_count = len(args[0])
        self.joint_count = len(args[0]) * 4
        self.finger_roots = [None] * len(args[0])
        self.metacarpal_children_count = 0

        for flag in self.carpal_flags:
            if flag:
                self.carpal = True
                self.metacarpal_children_count += 1

        if self.carpal:
            self.joint_count += 1

    def add_settings(self):
        cmds.addAttr(self.settings_node, ln="FKControllrShapeType", at="enum", en=self.fk_ctrl_shape_type, k=True)

    def create(self):
        core.create_hierarchy(
        self.modules_grp,
            self.grp, ":",
                self.root_joint
        )

        joint_names = []
        guide_joints = []
        guide_joint_spaces = []
        guide_proxies = []
        guide_nodes = []
        guide_node_spaces = []
        finger_roots = []
        finger_alls = []
        finger_all_spaces = []
        name_carpal = []
        guide_Carpal = []
        guide_node_Carpal = []
        self.metacarpal_guide_proxies = []
        self.metacarpal_target = core.create_guide_node(f"{self.grp_name}_Carpal_Target")

        if self.carpal:
            name_carpal = [f"{self.grp_name}_Carpal"]
            guide_Carpal = [core.create_guide_joint("Guide", name_carpal[0], color=[0.6, 0.0, 0.0], radius=0.2)]
            guide_node_Carpal = [core.create_guide_node(f"{self.grp_name}_Carpal")]
            self.metacarpal_guide_proxies = [core.create_guide_joint("GUideProxy", f"{self.grp_name}_Carpal", radius=0.1)]
            core.create_hierarchy(
            guide_Carpal,
                self.metacarpal_guide_proxies[0]
            )

        for i, finger_name in enumerate(self.finger_names):
            names = core.create_numbered_names(finger_name, 4)
            joints = [None] * 4
            joint_spaces = [None] * 4
            proxies = [None] * 4
            nodes = [None] * 4
            node_spaces = [None] * 4
            finger_root  = core.create_guide_joint("Guide", f"{finger_name}_Global", radius=0.2)
            finger_all  = core.create_guide_joint("Guide", f"{finger_name}_ALL",  color=[0.0, 0.0, 1.0], radius=0.1)
            finger_all_space = core.create_space(finger_all)

            if self.carpal_flags[i]:
                self.metacarpal_guide_proxies += [core.create_guide_joint("GUideProxy", f"{self.grp_name}_Carpal_{finger_name}", radius=0.1)]
                core.create_hierarchy(
                self.metacarpal_guide_proxies[0],
                    self.metacarpal_guide_proxies[-1]
                )

            for j, name in enumerate(names):
                proxy = core.create_guide_joint("GUideProxy", name, radius=0.1)
                node = core.create_guide_node(name)
                node_space = core.create_space(node)
                joint = core.create_guide_joint("Guide", name, radius=0.2, show_label=False)
                joint_space = core.create_space(joint)

                if j:
                    proxies_parent = proxies[j - 1]

                else:
                    proxies_parent = finger_root

                core.create_hierarchy(
                proxies_parent,
                    proxy, ":",
                        node_space, ":",
                            node
                )

                core.create_hierarchy(
                finger_root,
                    joint_space, ":",
                        joint
                )

                joints[j] = joint
                joint_spaces[j] = joint_space
                proxies[j] = proxy
                nodes[j] = node
                node_spaces[j] = node_space

            core.create_hierarchy(
                self.root_joint,
                    finger_root, ":",
                        finger_all_space, ":",
                            finger_all
            )

            joint_names += names
            guide_joints += joints
            guide_joint_spaces += joint_spaces
            guide_proxies += proxies
            guide_nodes += nodes
            guide_node_spaces += node_spaces
            finger_roots += [finger_root]
            finger_alls += [finger_all]
            finger_all_spaces += [finger_all_space]

        if self.carpal:
            core.create_hierarchy(
                self.root_joint,
                    self.metacarpal_target,
                    guide_Carpal[0], ":",
                        guide_node_Carpal[0]
            )

        self.joint_names = joint_names + name_carpal
        self.guide_joints = guide_joints + guide_Carpal
        self.guide_joint_spaces = guide_joint_spaces
        self.guide_proxies = guide_proxies
        self.guide_nodes = guide_nodes + guide_node_Carpal
        self.guide_node_spaces = guide_node_spaces
        self.other_nodes = finger_roots + finger_alls
        self.other_node_spaces = finger_all_spaces

    def _connect(self):
        cmds.addAttr(self.root_joint, ln="UniformScale", at="double", min=0.1, dv=1.0, k=True)
        cmds.setAttr(f"{self.root_joint}.radius", k=True)
        cmds.connectAttr(f"{self.root_joint}.UniformScale", f"{self.root_joint}.radius")
        for axis in "XYZ":
            cmds.connectAttr(f"{self.root_joint}.UniformScale", f"{self.root_joint}.scale{axis}")

        if self.carpal:
            wam = core._create_node("wtAddMatrix", name=f"Wam_{self.metacarpal_target}")
            dm = core._create_node("decomposeMatrix", name=f"Dm{self.metacarpal_target}")
            cmds.connectAttr(f"{wam}.matrixSum", f"{dm}.inputMatrix")
            cmds.connectAttr(f"{dm}.outputTranslate", f"{self.metacarpal_target}.translate")
            wt = 1 / self.metacarpal_children_count
            core.connect_aim_constraint(self.metacarpal_target, self.guide_nodes[-1])

        aim_nodes = []
        start = 0
        end = 4
        m = 1
        for c in range(self.finger_count):
            joints = self.guide_joints[start:end]
            proxies = self.guide_proxies[start:end]
            node_spaces = self.guide_node_spaces[start:end]
            start += 4
            end += 4

            for i, jt, proxy, guide in zip(range(4), joints, proxies, node_spaces):
                if i == 3:
                    core.connect_point_constraint(jt, proxy)
                    core.connect_same_attr(node_spaces[i - 1], guide, ["rotate"])

                else:
                    core.connect_point_constraint(jt, proxy)
                    aim_nodes += [core.connect_bend_constraint(proxy, proxies[i + 1], guide, axis=self.connect_aim_axis)]

            core.connect_equal_point([joints[0], joints[1], joints[3]])
            core.connect_equal_point([joints[1], joints[2], joints[3]])

            if self.carpal_flags[c]:
                core.connect_point_constraint(joints[0], self.metacarpal_guide_proxies[m])
                cmds.connectAttr(f"{self.other_nodes[c]}.matrix", f"{wam}.wtMatrix[{m}].matrixIn")
                cmds.setAttr(f"{wam}.wtMatrix[{m}].weightIn", wt)
                m += 1

    def _lock_attributes(self):
        self._lock_attrs = [
        self.grp, ["scale"],
        self.root_joint, ["scale", "visibility"],
        self.settings_node, ["Orient"]
        ]
        if self.carpal:
            self._lock_attrs += [
            self.guide_joints[-1], ["rotate", "scale", "visibility"]
            ]

        i = 0
        for c in range(self.finger_count):
            self._lock_attrs += [
            self.guide_joints[i], ["translate", "rotate", "scale", "visibility"],
            self.guide_joints[i + 1], ["tz", "rotate", "scale", "visibility"],
            self.guide_joints[i + 2], ["tz", "rotate", "scale", "visibility"],
            self.guide_joints[i + 3], ["tz", "rotate", "scale", "visibility"],
            self.other_nodes[c], ["scale", "visibility"],
            self.other_nodes[c + self.finger_count], ["tz", "rotate", "scale", "visibility"]
            ]
            i += 4

    def collect_meta_data(self):
        self.meta_data["FKControllrShapeType"] = core.compose_attr_paths(self.settings_node, "FKControllrShapeType")
        self.meta_data["CarpalFlag"] = self.carpal_flags

    def _post_process(self):
        cmds.setAttr(f"{self.root_joint}.drawLabel", True)
        if self.carpal:
            cmds.setAttr(f"{self.guide_nodes[-1]}.displayLocalAxis", True)

        i = 0
        for c in range(self.finger_count):
            cmds.setAttr(f"{self.other_nodes[c]}.otherType", self.joint_names[i], type="string")
            cmds.setAttr(f"{self.guide_joints[i]}.drawStyle", 2)
            cmds.setAttr(f"{self.guide_joints[i]}.drawLabel", False)
            cmds.setAttr(f"{self.guide_joints[i]}.displayHandle", False)
            cmds.setAttr(f"{self.guide_joints[i]}.displayLocalAxis", False)

            cmds.setAttr(f"{self.guide_nodes[i]}.displayLocalAxis", True)
            i += 4

    def apply_settings(self, root_matrix=[0, 0, 0, 0, 0, 0, 1], guide_positions=[[10, -10, 0], [10, 0, 0]], metacarpal_position=[2, -10, -2], thumb_position=[2, -10, 0], all_ctrl_pos=[0, 5], finger_distance=2,
    goal_bone=True, mirror=True, connect_type=1, translate_enabled=True, fk_ctrl_shape_type=2):
        if self.error:
            return
        
        cmds.setAttr(f"{self.root_joint}.translate", root_matrix[0], root_matrix[1], root_matrix[2])
        cmds.setAttr(f"{self.root_joint}.rotate", root_matrix[3], root_matrix[4], root_matrix[5])
        cmds.setAttr(f"{self.root_joint}.UniformScale", root_matrix[6])

        all_finger_distance = finger_distance * self.finger_count
        start_end = [[0, 0, all_finger_distance / 2], [0, 0, all_finger_distance / -2]]
        finger_positions = core.get_divide_positions(start_end, self.finger_count)

        i = 0
        for c in range(self.finger_count):
            if c:
                cmds.setAttr(f"{self.other_nodes[c]}.translate", guide_positions[0][0], guide_positions[0][1], guide_positions[0][2] + finger_positions[c][2])

            else:
                cmds.setAttr(f"{self.other_nodes[c]}.translate", thumb_position[0], thumb_position[1], thumb_position[2] + finger_positions[c][2])

            cmds.setAttr(f"{self.guide_joints[i + 3]}.translateX", guide_positions[1][0])
            cmds.setAttr(f"{self.guide_joints[i + 3]}.translateY", guide_positions[1][1])
            i += 4

        if self.carpal:
            cmds.setAttr(f"{self.guide_joints[-1]}.translate", metacarpal_position[0], metacarpal_position[1], metacarpal_position[2])

        for i in range(self.finger_count):
            cmds.setAttr(f"{self.other_nodes[i + self.finger_count]}.translateX", all_ctrl_pos[0])
            cmds.setAttr(f"{self.other_nodes[i + self.finger_count]}.translateY", all_ctrl_pos[1])

        cmds.setAttr(f"{self.settings_node}.GoalBone", goal_bone)
        cmds.setAttr(f"{self.settings_node}.Mirror", mirror)
        cmds.setAttr(f"{self.settings_node}.TranslateEnabled", translate_enabled)
        cmds.setAttr(f"{self.settings_node}.ConnectType", connect_type)
        cmds.setAttr(f"{self.settings_node}.FKControllrShapeType", fk_ctrl_shape_type)

        cmds.undoInfo(cck=True)


def build(data):
    pos, rot, scl = core.decompose_matrix(data["RootMatrix"])
    finger_names = [name.replace("_GB", "") for i, name in enumerate(data["JointName"]) if i % 4 == 3]

    G = Guide(data["GroupName"], data["JointCount"], data["ParentName"], data["Side"], finger_names, data["CarpalFlag"], ":".join(gui.CTRL_SHAPE_TYPE))
    G.apply_settings(root_matrix=[*pos, *rot, scl[0]], 
                    goal_bone=data["GoalBone"], mirror=data["Mirror"], connect_type=data["ConnectType"], translate_enabled=data["TranslateEnabled"], fk_ctrl_shape_type=data["FKControllrShapeType"])

    core.meta_node_apply_settings(G, data)

    for i, guide, matrix in zip(range(G.joint_count), G.guide_joints, data["GuideJointsMatrix"]):
        pos, rot = core.decompose_matrix(matrix)[:-1]
        
        if not i % 4 == 0:
            cmds.setAttr(f"{guide}.translateX", pos[0])
            cmds.setAttr(f"{guide}.translateY", pos[1])

    if G.carpal:
        pos = core.decompose_matrix(data["GuideJointsMatrix"][-1])[0]
        cmds.setAttr(f"{G.guide_joints[-1]}.translate", *pos)

    for i, guide, matrix in zip(range(len(G.other_nodes)), G.other_nodes, data["OtherGuidesMatrix"]):
        pos, rot = core.decompose_matrix(matrix)[:-1]

        if i < G.finger_count:
            cmds.setAttr(f"{guide}.translate", *pos)
            cmds.setAttr(f"{guide}.rotate", *rot)

        else:
            cmds.setAttr(f"{guide}.translateX", pos[0])
            cmds.setAttr(f"{guide}.translateY", pos[1])

    if not "PositiveWeights" in data:
        return

    meta_data = {}
    meta_data["PositiveWeights"] = data["PositiveWeights"]
    meta_data["NegativeWeights"] = data["NegativeWeights"]
    core.dict_to_attr(G.meta_node, meta_data)