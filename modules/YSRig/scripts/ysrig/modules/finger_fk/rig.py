from importlib import *
from maya import cmds
from ysrig import core, rig_base
reload(core)
reload(rig_base)

# TODO: 指モジュールだけ複雑すぎる 何とかしたい

class Rig(rig_base.RigBace):
    def setup(self):
        self.ctrl_shape_type = core.get_enum_attribute(self.meta_node, "FKControllrShapeType")
        self.carpal_flags = core.get_list_attributes(self.meta_node, "CarpalFlag")

    def create_proxy(self):
        self.base_joints_chunk = core.get_chunk_list(self.base_joints, 4)
        self.joint_names_chunk = core.get_chunk_list(self.joint_names, 4)
        self.proxies_chunk = []

        self.flag = False
        for base_joints, joint_names in zip(self.base_joints_chunk, self.joint_names_chunk):
            if len(base_joints) == 1:
                self.flag = True
                continue

            jts = cmds.duplicate(base_joints[:-1], po=True, rc=True)
            for jt in jts:
                cmds.setAttr(f"{jt}.drawStyle", 2)

            proxies = [cmds.rename(jt, f"Proxy_{name}") for jt, name in zip(jts, joint_names)]
            self.proxies_chunk += [proxies]
            self.proxies += proxies
            cmds.parent(proxies[0], self.grp)

        if not self.flag:
            return

        jt = cmds.duplicate(self.base_joints[-1], po=True, rc=True)
        jt = cmds.rename(jt, f"Proxy_{self.joint_names[-1]}")
        cmds.setAttr(f"{jt}.drawStyle", 2)
        self.proxies_chunk += [[jt]]
        self.proxies += jt
        cmds.parent(jt, self.grp)

        for f, proxies in zip(self.carpal_flags, self.proxies_chunk):
            if f:
                cmds.parent(proxies[0], jt)

    def create(self):
        self.ctrls_chunk = []
        self.ctrl_spaces_chunk = []
        self.all_ctrls = []
        self.all_ctrl_spaces = []
        ctrl_instances= []
        carpal_ctrl_instance = []
        all_ctrl_instance = []
        self.grps = []

        metac_index = len(self.joint_names_chunk) * 3

        if self.flag:
            metac_index = metac_index - 3

        for i, names, base_joints in zip(range(len(self.joint_names_chunk)), self.joint_names_chunk, self.base_joints_chunk):
            if len(base_joints) == 1:
                continue

            grp = cmds.createNode("transform", name=names[-1].replace("_GB", "_Finger_Group"))
            ctrls = core.convert_joint_to_controller(base_joints[:-1])
            cmds.matchTransform(grp, ctrls[0])
            core.create_hierarchy(
                self.grp,
                    grp, ":",
                        ctrls[0]
                )

            ctrl_spaces_chunk = []
            ctrls_chunk = []
            for j, name, ctrl in zip(range(len(names)), names, ctrls + ["tmp"]):
                if "_GB" in name:
                    c = core.CtrlCurve(name.replace("_GB", "_All"), "Roll")
                    if self.flag:
                        pos, rot = core.decompose_matrix(self.ctrl_space_matrices[metac_index + i + 1])[:-1]

                    else:
                        pos, rot = core.decompose_matrix(self.ctrl_space_matrices[metac_index + i])[:-1]

                    cmds.setAttr(f"{c.parent_node}.translate", *pos)
                    cmds.setAttr(f"{c.parent_node}.rotate", *rot)
                    s = core.create_space(c.parent_node, parent=True)
                    all_ctrl_instance += [c]
                    self.all_ctrls += [c.parent_node]
                    self.all_ctrl_spaces += [s]
                    cmds.parent(s, grp)
                    cmds.parent(grp, self.ctrl_grp)

                else:
                    c = core.CtrlCurve(f"{name}1", self.ctrl_shape_type)
                    c.reparent_shape(ctrl)
                    s = core.create_space(c.parent_node, parent=True)
                    ctrl_instances += [c]
                    self.ctrl_spaces += [s]
                    self.ctrls += [c.parent_node]

                ctrl_spaces_chunk += [s]
                ctrls_chunk += [c.parent_node]

            self.grps += [grp]
            self.ctrl_spaces_chunk += [ctrl_spaces_chunk]
            self.ctrls_chunk += [ctrls_chunk]

        if self.flag:
            self.ctrls_chunk += [[]]
            self.ctrl_spaces_chunk += [[]]

            ctrl = core.CtrlCurve(f"{self.grp_name}_Carpal", self.ctrl_shape_type)
            pos, rot = core.decompose_matrix(self.ctrl_space_matrices[metac_index])[:-1]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)
            cmds.setAttr(f"{ctrl.parent_node}.rotate", *rot)
            space = core.create_space(ctrl.parent_node, parent=True)
            cmds.parent(space, self.ctrl_grp)

            self.ctrl_spaces += [space]
            self.ctrl_spaces_chunk[-1] = [space]
            self.ctrls += [ctrl.parent_node]
            self.ctrls_chunk[-1] = [ctrl.parent_node]

            carpal_ctrl_instance = ctrl

            self.ctrl_instances = ctrl_instances + [carpal_ctrl_instance] + all_ctrl_instance

        else:

            self.ctrl_instances = ctrl_instances + all_ctrl_instance

    def set_color(self):
        klass = self.color_class()
        klass.set_color(self.ctrls, self.all_ctrls, self.side)

    def add_settings(self):
        for ctrls in self.ctrls_chunk:
            if len(ctrls) == 1:
                continue

            for ctrl in ctrls[:-1]:
                cmds.addAttr(ctrl, ln="________________", at="enum", en="Settings", k=True)
                cmds.setAttr(f"{ctrl}.________________", l=True)
                cmds.addAttr(ctrl, ln="PositiveWeight", at="double", min=0, max=2, dv=1, k=True)
                cmds.addAttr(ctrl, ln="NegativeWeight", at="double", min=0, max=2, dv=1, k=True)


    def _connect(self):
        for proxies, base_joints in zip(self.proxies_chunk, self.base_joints_chunk):
            if self.parent_joint == rig_base.RigBace.ROOT_JOINT:
                core.connect_parent_constraint(proxies[0], base_joints[0])
                core.connect_scale_constraint(proxies[0], base_joints[0])
                for px, jt in zip(proxies[1:], base_joints[1:]):
                    core.connect_same_attr(px, jt, ["translate", "rotate", "scale"])

            else:
                for px, jt in zip(proxies, base_joints):
                    core.connect_same_attr(px, jt, ["translate", "rotate", "scale"])

    def connect(self):
        for i, proxies, ctrls, spaces, flag, all_ctrl in zip(range(len(self.proxies_chunk)), self.proxies_chunk, self.ctrls_chunk, self.ctrl_spaces_chunk, self.carpal_flags, self.all_ctrls):
            if len(proxies) == 1:
                core.connect_matrix(ctrls[0], proxies[0], tl=self.translate_enabled, rt=True, lc=self.connect_type)
                continue

            if flag:
                core.connect_matrix(self.ctrls_chunk[-1][0], self.grps[i], tl=True, rt=True, lc=self.connect_type)

            for j, proxy, ctrl in zip(range(len(proxies)), proxies, ctrls[:-1]):
                if flag and not j:
                    core.connect_matrix(ctrl, proxy, tl=True, rt=True, lc=self.connect_type)

                else:
                    core.connect_matrix(ctrl, proxy, tl=self.translate_enabled, rt=True, lc=self.connect_type)

            cd= core.connect_condition(
                name=f"Cd_{all_ctrl}_Wt", operation=2, ft=f"{all_ctrl}.rotateZ", st=0,
                tr=f"{ctrls[0]}.PositiveWeight", tg=f"{ctrls[1]}.PositiveWeight", tb=f"{ctrls[2]}.PositiveWeight",
                fr=f"{ctrls[0]}.NegativeWeight", fg=f"{ctrls[1]}.NegativeWeight", fb=f"{ctrls[2]}.NegativeWeight"
                )
            md = core.connect_multiply_divide(
                name=f"Md_{all_ctrl}_Wt", in1x=f"{all_ctrl}.rotateZ", in1y=f"{all_ctrl}.rotateZ", in1z=f"{all_ctrl}.rotateZ", in2=f"{cd}.outColor")

            for space, axis in zip(spaces, "XYZ"):
                core.connect_float_math(f"Fm_{space}", operation=0, fa=f"{space}.rotateZ!", fb=f"{md}.output{axis}", out=[f"{space}.rotateZ"])

    def set_attr(self):
        if not cmds.attributeQuery("PositiveWeights", node=self.meta_node, exists=True):
            return

        positive_weights = core.get_list_attributes(self.meta_node, "PositiveWeights")
        negative_weights = core.get_list_attributes(self.meta_node, "NegativeWeights")
        positive_weights_chunk = core.get_chunk_list(positive_weights, 3)
        negative_weights_chunk = core.get_chunk_list(negative_weights, 3)

        for ctrls, pws, nws in zip(self.ctrls_chunk, positive_weights_chunk, negative_weights_chunk):
            for ctrl, pw, nw in zip(ctrls, pws, nws):
                cmds.setAttr(f"{ctrl}.PositiveWeight", pw, k=False, cb=True)
                cmds.setAttr(f"{ctrl}.NegativeWeight", nw, k=False, cb=True)

    def lock_attributes(self):
        for ctrls in self.ctrls_chunk:
            if len(ctrls) == 1:
                self.lock_attrs += [ctrls[0], ["scale", "visibility"]]
                if not self.translate_enabled:
                    self.lock_attrs += [ctrls[0], ["translate"]]
                continue
            
            for i, ctrl in enumerate(ctrls[:-1]):
                self.lock_attrs += [ctrl, ["scale", "visibility"]]
                if not self.translate_enabled:
                    self.lock_attrs += [ctrl, ["translate"]]
                
                if i:
                    self.lock_attrs += [ctrl, ["rx", "ry"]]

            self.lock_attrs += [ctrls[-1], ["translate", "rx", "ry", "scale", "visibility"]]

    def collect_meta_data(self):
        ctrls = self.ctrls[:-1]
        if len(ctrls) % 3:
            ctrls = ctrls[:-1]

        self.meta_data["PositiveWeights"] = core.compose_attr_paths(ctrls, "PositiveWeight", multi=True)
        self.meta_data["NegativeWeights"] = core.compose_attr_paths(ctrls, "NegativeWeight", multi=True)


class RigMirror(Rig):
    def _setup(self, meta_node):
        super()._setup(meta_node)
        self.src_joints = [f"JT_{name}" for name in self.joint_names]
        self.src_side = self.side[:]
        self.build, self.side, self.grp_name, self.joint_names = rig_base.get_mirror_names(self.side, self.grp_name, self.joint_names)

    def create(self):
        self.ctrls_chunk = []
        self.ctrl_spaces_chunk = []
        self.all_ctrls = []
        self.all_ctrl_spaces = []
        ctrl_instances= []
        carpal_ctrl_instance = []
        all_ctrl_instance = []
        self.grps = []

        self.src_joints_chunk = core.get_chunk_list(self.src_joints, 4)
        metac_index = len(self.joint_names_chunk) * 3

        if self.flag:
            metac_index = metac_index - 3

        for i, names, base_joints, src_joints in zip(range(len(self.joint_names_chunk)), self.joint_names_chunk, self.base_joints_chunk, self.src_joints_chunk):
            if len(base_joints) == 1:
                continue

            grp = cmds.createNode("transform", name=names[-1].replace("_GB", "_Finger_Group"))
            ctrls = core.convert_joint_to_controller(src_joints[:-1], sr=[self.src_side, self.side])
            cmds.matchTransform(grp, ctrls[0])
            core.create_hierarchy(
                self.grp,
                    grp, ":",
                        ctrls[0]
                )

            ctrl_spaces_chunk = []
            ctrls_chunk = []
            for j, name, ctrl in zip(range(len(names)), names, ctrls + ["tmp"]):
                if "_GB" in name:
                    c = core.CtrlCurve(name.replace("_GB", "_All"), "Roll")
                    if self.flag:
                        pos, rot = core.decompose_matrix(self.ctrl_space_matrices[metac_index + i + 1])[:-1]

                    else:
                        pos, rot = core.decompose_matrix(self.ctrl_space_matrices[metac_index + i])[:-1]

                    cmds.setAttr(f"{c.parent_node}.translate", *pos)
                    cmds.setAttr(f"{c.parent_node}.rotate", *rot)
                    s = core.create_space(c.parent_node, parent=True)
                    all_ctrl_instance += [c]
                    self.all_ctrls += [c.parent_node]
                    self.all_ctrl_spaces += [s]
                    cmds.parent(s, grp)
                    cmds.parent(grp, self.ctrl_grp)

                else:
                    c = core.CtrlCurve(f"{name}1", self.ctrl_shape_type)
                    c.reparent_shape(ctrl)
                    s = core.create_space(c.parent_node, parent=True)
                    ctrl_instances += [c]
                    self.ctrl_spaces += [s]
                    self.ctrls += [c.parent_node]

                ctrl_spaces_chunk += [s]
                ctrls_chunk += [c.parent_node]

            self.grps += [grp]
            self.ctrl_spaces_chunk += [ctrl_spaces_chunk]
            self.ctrls_chunk += [ctrls_chunk]

        if self.flag:
            self.ctrls_chunk += [[]]
            self.ctrl_spaces_chunk += [[]]

            ctrl = core.CtrlCurve(f"{self.grp_name}_Carpal", self.ctrl_shape_type)
            pos, rot = core.decompose_matrix(self.ctrl_space_matrices[metac_index])[0:2]
            cmds.setAttr(f"{ctrl.parent_node}.translate", *pos)
            cmds.setAttr(f"{ctrl.parent_node}.rotate", *rot)
            space = core.create_space(ctrl.parent_node, parent=True)
            cmds.parent(space, self.ctrl_grp)

            self.ctrl_spaces += [space]
            self.ctrl_spaces_chunk[-1] = [space]
            self.ctrls += [ctrl.parent_node]
            self.ctrls_chunk[-1] = [ctrl.parent_node]

            carpal_ctrl_instance = ctrl

            self.ctrl_instances = ctrl_instances + [carpal_ctrl_instance] + all_ctrl_instance

        else:

            self.ctrl_instances = ctrl_instances + all_ctrl_instance

        core.mirror_space(self.ctrl_grp)

    def set_attr(self):
        for ctrls in self.ctrls_chunk:
            for ctrl in ctrls[:-1]:
                core.connect_same_attr(ctrl.replace(f"{self.side}_", f"{self.src_side}_"), ctrl, ["PositiveWeight", "NegativeWeight"])
                cmds.setAttr(f"{ctrl}.PositiveWeight", l=True, cb=True)
                cmds.setAttr(f"{ctrl}.NegativeWeight", l=True, cb=True)

    def collect_meta_data(self):
        pass