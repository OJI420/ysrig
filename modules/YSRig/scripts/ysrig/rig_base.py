import os
import inspect
from traceback import *
import importlib
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core
importlib.reload(core)

class RigBace:
    """
    リグビルドの基底クラス
    """

    ROOT_JOINT = "JT_Root"
    ROOT_CTRL = "Ctrl_Root"
    ROOT_OFFSET_CTRL = "Ctrl_Root_Offset"

    def __init__(self, meta_node):
        self._setup(meta_node)                          # 変数宣言
        self.setup()
        self.check_build()                              # ビルド条件を満たすかチェック

        if not self.build:
            return

        self._get_class()
        self._create_grp()
        self.parent_grp()
        self.pre_process()                 # 前処理
        self.get_base_joints()             # jointの名前を取得
        self.create_proxy()                # proxyジョイント作成
        self.create_ctrl_grp()             # コントローラーのグループ
        self._create()                     # ノード作成
        self.create()
        self.set_color()                   # 色設定
        self.set_shape_transform()
        self.add_settings()                # 設定用アトリビュート追加
        self._connect()                    # ノード接続
        self.connect()
        self.set_attr()                    # アトリビュート設定
        self._lock_attributes()            # ロックするアトリビュートを指定
        self.lock_attributes()
        self._lock()                       # アトリビュートロック
        self._distribute_shape_instances()
        self.collect_meta_data()           # メタノードに書き込む情報を指定
        self.post_process()                # 後処理
        self._set_meta_data()              # メタノードに情報書き込み
        self.connect_visibility()
        self.mirror()

    def _setup(self, meta_node):
        self.build = True
        self.error = False

        self.meta_data = {}

        self.color_class = None

        self.meta_node = meta_node
        self.grp = None
        self.settings_node = None
        self.ctrl_grp = None
        self.parent_joint = None

        self.base_joints = []
        self.proxies = []
        self.ctrls = []
        self.ctrl_spaces = []
        self.ctrl_instances = []

        self._lock_attrs = []
        self.lock_attrs = []

        self.grp_name = cmds.getAttr(f"{self.meta_node}.GroupName")
        self.side = cmds.getAttr(f"{self.meta_node}.Side")
        self.joint_count = cmds.getAttr(f"{self.meta_node}.JointCount")
        self.joint_names = core.get_list_attributes(self.meta_node, "JointName")

        self.ctrl_matrices = core.get_list_attributes(self.meta_node, "CtrlsMatrix")
        self.ctrl_space_matrices = core.get_list_attributes(self.meta_node, "CtrlSpacesMatrix")
        self.ctrl_line_width = cmds.getAttr(f"{self.meta_node}.LineWidth")

        self.translate_enabled = cmds.getAttr(f"{self.meta_node}.TranslateEnabled")
        self.connect_type = cmds.getAttr(f"{self.meta_node}.ConnectType")

    def setup(self):
        pass

    def check_build(self):
        if cmds.objExists(f"Controller_{self.grp_name}_Group"):
            self.build = False

        for name in self.joint_names:
            if  cmds.objExists(f"Proxy_{name}"):
                self.build = False

    def _get_class(self):
        file_path = inspect.getfile(self.__class__)  # クラスのあるファイルパス
        dir_path = os.path.dirname(file_path)        # 親ディレクトリのパス
        module_name = os.path.basename(dir_path)     # 親ディレクトリの名前
        self.color_class = getattr(importlib.import_module(f"ysrig.modules.{module_name}.ctrl"), "CtrlColor")
        self.mirror_class = getattr(importlib.import_module(f"ysrig.modules.{module_name}.rig"), "RigMirror")

    def _create_grp(self):
        lc = core.create_labeled_node("locator", "Controller_Setting")
        grp = cmds.listRelatives(lc, p=True)[0]
        lc = cmds.rename(lc, f"Controller_{self.grp_name}_Settings")
        grp = cmds.rename(grp, f"Controller_{self.grp_name}_Group")
        
        cmds.addAttr(grp, ln="YSNodeLabel", dt="string")
        cmds.setAttr(f"{grp}.YSNodeLabel", core.get_rig_module_group(), type="string")
        cmds.setAttr(f"{grp}.YSNodeLabel", l=True)
        
        for axis in "XYZ":
            cmds.setAttr(f"{grp}.scale{axis}", k=False, cb=False)
            cmds.setAttr(f"{lc}.localPosition{axis}", k=False, cb=False, l=True)
            cmds.setAttr(f"{lc}.localScale{axis}", k=False, cb=False, l=True)
        cmds.setAttr(f"{lc}.visibility", False)
        core.set_outliner_color(grp, [0.6, 0.0, 1.0])
        self.grp = grp
        self.settings_node = lc

    def parent_grp(self):
        cmds.parent(self.grp, RigBace.ROOT_OFFSET_CTRL)
        self.parent_joint = cmds.listRelatives(f"JT_{self.joint_names[0]}", p=True)[0]
        cmds.matchTransform(self.grp, self.parent_joint)

        if self.parent_joint == RigBace.ROOT_JOINT:
            return

        core.connect_parent_constraint(self.parent_joint, self.grp)
        core.connect_scale_constraint(self.parent_joint, self.grp)

    def pre_process(self):
        pass

    def get_base_joints(self):
        self.base_joints = [None] * self.joint_count
        for i, name in enumerate(self.joint_names):
            self.base_joints[i] = f"JT_{name}"

    def create_proxy(self):
        jts = cmds.duplicate(self.base_joints, po=True, rc=True)
        for jt in jts:
            cmds.setAttr(f"{jt}.drawStyle", 2)

        self.proxies = [cmds.rename(jt, f"Proxy_{name}") for jt, name in zip(jts, self.joint_names)]
        cmds.parent(self.proxies[0], self.grp)
        if "_GB" in self.proxies[-1]:
            cmds.delete(self.proxies[-1])
            self.proxies = self.proxies[:-1]

    def create_ctrl_grp(self):
        self.ctrl_grp = core.create_labeled_node("transform", "Ctrl_Group", name=f"{self.grp_name}_Ctrl_Group")
        cmds.parent(self.ctrl_grp, self.grp)
        cmds.makeIdentity(self.ctrl_grp)

    def _create(self):
        pass

    def create(self):
        pass

    def set_color(self):
        klass = self.color_class()
        klass.set_color(self.ctrls, self.side)

    def set_shape_transform(self):
        for ctrl, ctrl_mat, spase_mat in zip(self.ctrl_instances, self.ctrl_matrices, self.ctrl_space_matrices):
            offset_scale = core.decompose_matrix(spase_mat)[2]
            ctrl.set_matrix(ctrl_mat, offset_scale=offset_scale)
            ctrl.set_width(self.ctrl_line_width)

    def add_settings(self):
        pass

    def _connect(self):
        if self.parent_joint == RigBace.ROOT_JOINT:
            core.connect_parent_constraint(self.proxies[0], self.base_joints[0])
            core.connect_scale_constraint(self.proxies[0], self.base_joints[0])
            for px, jt in zip(self.proxies[1:], self.base_joints[1:]):
                core.connect_same_attr(px, jt, ["translate", "rotate", "scale"])

        else:
            for px, jt in zip(self.proxies, self.base_joints):
                core.connect_same_attr(px, jt, ["translate", "rotate", "scale"])

    def connect(self):
        pass

    def set_attr(self):
        pass

    def _lock_attributes(self):
        for ctrl in self.ctrls:
            self._lock_attrs += [ctrl, ["visibility"]]

    def lock_attributes(self):
        pass

    def _lock(self):
        core.lock_attr(self._lock_attrs)
        core.lock_attr(self.lock_attrs)

    def _distribute_shape_instances(self):
        for node in self.ctrls:
            tmp = cmds.instance(self.settings_node)[0]
            shape = f"{tmp}|{self.settings_node}"
            cmds.parent(shape, node, r=True, s=True)
            cmds.delete(tmp)

    def collect_meta_data(self):
        pass

    def post_process(self):
        pass

    def _set_meta_data(self):
        core.dict_to_attr(self.meta_node, self.meta_data)

    def connect_visibility(self):
        cmds.addAttr("Controller_Root_Settings", ln=self.grp_name, at="enum", en="Hide:Show", k=True, dv=1)
        cmds.connectAttr(f"Controller_Root_Settings.{self.grp_name}", f"{self.grp}.visibility")

    def mirror(self):
        if cmds.getAttr(f"{self.meta_node}.Mirror"):
            klass = self.mirror_class(self.meta_node)


def get_mirror_names(side, group_name, joint_names):
    if not side:
        return [False, "", "", []]

    search_side = f"{side}_"
    replace_side = "R_"
    if side == "R":
        replace_side = "L_"

    if not search_side in group_name:
        return [False, "", "", []]

    for name in joint_names:
        if not search_side in name:
            return [False, "", "", []]

    group_name = group_name.replace(search_side, replace_side)
    joint_names = [name.replace(search_side, replace_side) for name in joint_names]

    return [True, replace_side.replace("_", ""), group_name, joint_names]


def main():
    cmds.undoInfo(ock=True)

    try:
        meta_nodes = core.get_meta_nodes()
        meta_nodes += core.get_facial_meta_nodes()
        modules = [None] * len(meta_nodes)

        # プログレスウィンドウの初期化
        if cmds.progressWindow(q=True, isCancelled=True):
            cmds.progressWindow(endProgress=True)

        cmds.progressWindow(title="Build Edit Controller",
                            progress=0,
                            max=len(meta_nodes),
                            status="Building...",
                            isInterruptable=False)

        # モジュールのメタノードを読み込んでインスタンスを作る
        for i, meta in enumerate(meta_nodes):
            if cmds.progressWindow(q=True, isCancelled=True):
                cmds.progressWindow(endProgress=True)
                cmds.warning("Cancelled by user")
                return

            module = cmds.getAttr(f"{meta}.Module")
            module = importlib.import_module(f"ysrig.modules.{module}.rig")
            klass = getattr(module, "Rig")
            modules[i] = klass(meta)

            # 進捗を更新
            cmds.progressWindow(e=True, step=1, status=f"Building {meta}...")

        cmds.select(cl=True)
        cmds.undoInfo(cck=True)

    except:
        cmds.undoInfo(cck=True)
        cmds.undo()
        print_exc()
        MGlobal.displayError("予期せぬエラーが発生しました")

    cmds.progressWindow(endProgress=True)