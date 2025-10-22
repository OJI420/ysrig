from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, skeleton_base
reload(core)
reload(skeleton_base)

class Skeleton(skeleton_base.facialSkeletonBase):
    def post_process(self):
        cmds.delete(self.joints[1])
        cmds.mirrorJoint(self.joints[0], myz=True, mb=True, sr=["L_", "R_"])