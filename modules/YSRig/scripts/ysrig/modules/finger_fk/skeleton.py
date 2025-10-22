from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, skeleton_base
reload(core)
reload(skeleton_base)

class Skeleton(skeleton_base.SkeletonBase):
    def setup(self):
        self.carpal_flags = core.get_list_attributes(self.meta_node, "CarpalFlag")
        self.carpal = False
        for flag in self.carpal_flags:
            if flag:
                self.carpal = True

    def parent(self):
        joint_chunks = core.get_chunk_list(self.joints, 4)
        for joints in joint_chunks:
            for i, jt in enumerate(joints):
                if i:
                    cmds.parent(jt, joints[i - 1])

                else:
                    cmds.parent(jt, self.skeleton_grp)

        if self.carpal:
            for i, joints in enumerate(joint_chunks[:-1]):
                if self.carpal_flags[i]:
                    cmds.parent(joints[0], self.joints[-1])

    def parent_external(self):
        parent = cmds.getAttr(f"{self.meta_node}.ParentName")
        if parent:
            parent = f"JT_{parent}"

        else:
            parent = f"JT_Root"

        joint_chunks = core.get_chunk_list(self.joints, 4)
        for joints, flag in zip(joint_chunks, self.carpal_flags):
            if not flag:
                cmds.parent(joints[0], parent)

        if self.carpal:
            cmds.parent(self.joints[-1], parent)

    def mirror(self):
        self.get_prefixes()

        if self.parent_name:
            parent = self.parent_name.replace(self.prefixes[0], self.prefixes[1])

        joint_chunks = core.get_chunk_list(self.joints, 4)
        for joints, flag in zip(joint_chunks, self.carpal_flags):
            if not flag:
                cmds.mirrorJoint(joints[0], myz=True, mb=True, sr=self.prefixes)
                if self.parent_name:
                    fst_joint = joints[0].replace(self.prefixes[0], self.prefixes[1])
                    if cmds.objExists(parent):
                        cmds.parent(fst_joint, parent)

                    else:
                        cmds.parent(fst_joint, "JT_Root")

        if self.carpal:
            cmds.mirrorJoint(self.joints[-1], myz=True, mb=True, sr=self.prefixes)
            if self.parent_name:
                fst_joint = self.joints[-1].replace(self.prefixes[0], self.prefixes[1])
                if cmds.objExists(parent):
                    cmds.parent(fst_joint, parent)

                else:
                    cmds.parent(fst_joint, "JT_Root")