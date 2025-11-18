from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, skeleton_base
reload(core)
reload(skeleton_base)

class Skeleton(skeleton_base.SkeletonBase):
    def create(self):
        sk_grp = core.create_labeled_node("transform", core.SKELETON_GROUP_NAME, name=core.SKELETON_GROUP_NAME)
        cmds.parent(sk_grp, core.YSRIG_GROUP_NAME)
        super().create()