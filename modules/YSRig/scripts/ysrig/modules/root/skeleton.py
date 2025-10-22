from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, skeleton_base
reload(core)
reload(skeleton_base)

class Skeleton(skeleton_base.SkeletonBase):
    def create(self):
        sk_grp = core.create_labeled_node("transform", core.get_skeleton_group(), name=core.get_skeleton_group())
        cmds.parent(sk_grp, core.get_root_group())
        super().create()