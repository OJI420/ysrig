from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, skeleton_base
reload(core)
reload(skeleton_base)

class Skeleton(skeleton_base.facialSkeletonBase):
    def parent(self):
        core.create_hierarchy(
        self.skeleton_grp,
            self.joints[0], ":",
                self.joints[1], "..",
            self.joints[2],
            self.joints[3]
        )

    def post_process(self):
        cmds.mirrorJoint(self.joints[0], myz=True, mb=True, sr=["L_", "R_"])
        cmds.mirrorJoint(self.joints[2], myz=True, mb=True, sr=["L_", "R_"])
        cmds.mirrorJoint(self.joints[3], myz=True, mb=True, sr=["L_", "R_"])