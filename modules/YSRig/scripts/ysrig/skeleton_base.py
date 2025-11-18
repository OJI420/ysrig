from traceback import *
import importlib
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core, reload
importlib.reload(core)


class SkeletonBase:
    """
    ガイド作成の基底クラス
    """
    def __init__(self, meta_node):
        self._setup(meta_node)                 # 変数宣言
        self.setup()
        self.check_build()                     # ビルド条件を満たすかチェック

        if not self.build:
            return

        self.pre_process()                 # 前処理
        self.create()                      # ノード作成
        self.parent()                      # ジョイントを階層化
        self.connect()                     # ノード接続
        self.post_process()                # 後処理

    def _setup(self, meta_node):
        self.error = False
        self.build = True

        self.meta_node = meta_node

        self.group_name = cmds.getAttr(f"{self.meta_node}.GroupName")
        self.parent_name = f'JT_{cmds.getAttr(f"{self.meta_node}.ParentName")}'
        self.side = cmds.getAttr(f"{self.meta_node}.Side")
        self.prefixes = []
        self.joint_names = core.get_list_attributes(self.meta_node, "JointName")
        self.joint_count = cmds.getAttr(f"{self.meta_node}.JointCount")
        self.joints = [None] * self.joint_count
        self.guides_world_matrix = core.get_list_attributes(self.meta_node, "GuidesWorldMatrix")
        self.create_goal_bone = cmds.getAttr(f"{self.meta_node}.GoalBone")

        self.skeleton_grp = core.SKELETON_GROUP_NAME

    def setup(self):
        pass

    def check_build(self):
        for name in self.joint_names:
            if  cmds.objExists(f"JT_{name}"):
                self.build = False

    def pre_process(self):
        pass

    def create(self):
        for i, name in enumerate(self.joint_names):
            jt = cmds.createNode("joint", name=f"JT_{name}")
            cmds.setAttr(f"{jt}.segmentScaleCompensate", False)

            trs = core.decompose_matrix(self.guides_world_matrix[i])
            pos = trs[0]
            orient = trs[1]

            cmds.setAttr(f"{jt}.translate", *pos)
            cmds.setAttr(f"{jt}.jointOrient", *orient)

            self.joints[i] = jt

    def parent(self):
        cmds.parent(self.joints[0], self.skeleton_grp)
        for i, jt in enumerate(self.joints):
            if i:
                cmds.parent(jt, self.joints[i - 1])

    def connect(self):
        pass

    def post_process(self):
        suffix = self.joint_names[-1][-2:]
        if not self.create_goal_bone and "GB" == suffix:
            cmds.delete(self.joints[-1])

    def parent_external_call(self):
        if not self.build:
            return

        self.parent_external()

    def parent_external(self):
        parent = cmds.getAttr(f"{self.meta_node}.ParentName")
        if not parent:
            if not self.group_name == "Root":
                parent = "Root"

            else:
                return

        parent = f"JT_{parent}"
        cmds.parent(self.joints[0], parent)

    def get_prefixes(self):
        s = "L_"
        r = "R_"
        if self.side == "R":
            r = "L_"
            s = "R_"
        
        self.prefixes = [s, r]

    def mirror_call(self):
        if not self.build:
            return

        if not cmds.getAttr(f"{self.meta_node}.Mirror"):
            return

        if self.side == "":
            return

        self.mirror()

    def mirror(self):
        self.get_prefixes()
        cmds.mirrorJoint(self.joints[0], myz=True, mb=True, sr=self.prefixes)

        if self.parent_name:
            parent = self.parent_name.replace(self.prefixes[0], self.prefixes[1])
            fst_joint = self.joints[0].replace(self.prefixes[0], self.prefixes[1])
            if cmds.objExists(parent):
                cmds.parent(fst_joint, parent)

            else:
                cmds.parent(fst_joint, "JT_Root")


class facialSkeletonBase(SkeletonBase):
    def _setup(self, meta_node):
        super()._setup(meta_node)
        self.skeleton_grp = f"JT_{core.FACIALS_ROOT_NAME}"


def main():
    cmds.undoInfo(ock=True)

    facials_root = f"JT_{core.FACIALS_ROOT_NAME}"
    meta_nodes = core.get_meta_nodes()
    facial_meta_nodes = core.get_facial_meta_nodes()
    facial_root_parent_name = cmds.getAttr(f"{meta_nodes[0]}.FacialRootName")
    facial_root_parent = f"JT_{facial_root_parent_name}"
    skeleton_modules = [None] * len(meta_nodes)
    facial_skeleton_modules = [None] * len(facial_meta_nodes)

    total_steps = len(meta_nodes) + len(facial_meta_nodes)

    # プログレスウィンドウの初期化
    if cmds.progressWindow(q=True, isCancelled=True):
        cmds.progressWindow(endProgress=True)

    cmds.progressWindow(title="Build Skeleton",
                        progress=0,
                        max=total_steps,
                        status="Initializing...",
                        isInterruptable=False)

    try:
        p = False

        # facials_rootがなければ作る
        if not cmds.objExists(facials_root):
            cmds.createNode("joint", name=facials_root)
            cmds.setAttr(f"{facials_root}.drawStyle", 3)
            p = True

        # bodyモジュールのメタノードを読み込んでインスタンスを作る
        for i, meta in enumerate(meta_nodes):
            module = cmds.getAttr(f"{meta}.Module")
            module = importlib.import_module(f"ysrig.modules.{module}.skeleton")
            klass = getattr(module, "Skeleton")
            skeleton_modules[i] = klass(meta)

            cmds.progressWindow(e=True, step=1, status=f"Loading Body Module: {meta}")

        # bodyモジュール同士をペアレント
        for module in skeleton_modules:
            module.mirror_call()
            module.parent_external_call()

        # facials_rootとfacialモジュールをペアレント
        if p:
            if facial_root_parent_name:
                cmds.parent(facials_root, facial_root_parent)
                cmds.matchTransform(facials_root, facial_root_parent, pos=True, rot=True)
                cmds.makeIdentity(facials_root, a=True)
            else:
                cmds.parent(facials_root, core.SKELETON_GROUP_NAME)

        # facialモジュールのメタノードを読み込んでインスタンスを作る
        for i, meta in enumerate(facial_meta_nodes):
            module = cmds.getAttr(f"{meta}.Module")
            module = importlib.import_module(f"ysrig.modules.{module}.skeleton")
            klass = getattr(module, "Skeleton")
            facial_skeleton_modules[i] = klass(meta)

            cmds.progressWindow(e=True, step=1, status=f"Loading Facial Module: {meta}")

        facial_joints = cmds.ls(facials_root, dag=True, type="joint")
        for joint in facial_joints:
            cmds.setAttr(f"{joint}.useOutlinerColor", True)
            cmds.setAttr(f"{joint}.overrideEnabled", True)
            cmds.setAttr(f"{joint}.outlinerColor", *core.FACIAL_COLOR_4)
            cmds.setAttr(f"{joint}.overrideColorRGB", *core.FACIAL_COLOR_1)

        # facialモジュールがなければfacials_rootを消す
        if not facial_meta_nodes:
            cmds.delete(facials_root)

        cmds.select(cl=True)
        cmds.undoInfo(cck=True)

    except:
        cmds.undoInfo(cck=True)
        cmds.undo()
        print_exc()
        MGlobal.displayError("予期せぬエラーが発生しました")

    cmds.progressWindow(endProgress=True)