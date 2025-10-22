import os
import inspect
from traceback import *
import importlib
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core
importlib.reload(core)

class CtrlBace:
    """
    コントローラー作成の基底クラス
    """
    def __init__(self, meta_node):
        self._setup(meta_node)                 # 変数宣言
        self.setup()
        self.check_build()                     # ビルド条件を満たすかチェック

        if not self.build:
            return

        self._get_color_class()
        self._create_grp()
        self.pre_process()                 # 前処理
        self._create()                     # ノード作成
        self.create()
        self.set_color()                   # 色設定
        self.set_space_transform()         # spaceノードのmatrix設定
        self._add_settings()               # 設定用アトリビュート追加
        self.add_settings()
        self._connect()                    # ノード接続
        self.connect()
        self._set_attr()                   # アトリビュート設定
        self._lock_attributes()            # ロックするアトリビュートを指定
        self.lock_attributes()
        self._lock()                       # アトリビュートロック
        self._distribute_shape_instances()
        self._collect_meta_data()          # メタノードに書き込む情報を指定
        self.collect_meta_data()
        self.post_process()                # 後処理
        self._set_meta_data()              # メタノードに情報書き込み

    def _setup(self, meta_node):
        self.build = True
        self.error = False

        self.meta_data = {}

        self.color_class = None

        self.meta_node = meta_node
        self.grp = None
        self.settings_node = None
        self.ctrls = [] 
        self.ctrl_spaces = []

        self._lock_attrs = []
        self.lock_attrs = []

        self.grp_name = cmds.getAttr(f"{self.meta_node}.GroupName")
        self.side = cmds.getAttr(f"{self.meta_node}.Side")
        self.joint_count = cmds.getAttr(f"{self.meta_node}.JointCount")
        self.joint_names = core.get_list_attributes(self.meta_node, "JointName")
        self.guide_world_matrices = core.get_list_attributes(self.meta_node, "GuidesWorldMatrix")

    def setup(self):
        pass

    def check_build(self):
        if cmds.objExists(f"CtrlEdit_{self.grp_name}_Group"):
            self.build = False

        for name in self.joint_names:
            if  cmds.objExists(f"Edit_{name}"):
                self.build = False

    def _get_color_class(self):
        file_path = inspect.getfile(self.__class__)  # クラスのあるファイルパス
        dir_path = os.path.dirname(file_path)        # 親ディレクトリのパス
        module_name = os.path.basename(dir_path)     # 親ディレクトリの名前
        self.color_class = getattr(importlib.import_module(f"ysrig.modules.{module_name}.ctrl"), "CtrlColor")

    def _create_grp(self):
        lc = core.create_labeled_node("locator", "CtrlEdit_Setting")
        grp = cmds.listRelatives(lc, p=True)[0]
        lc = cmds.rename(lc, f"CtrlEdit_{self.grp_name}_Settings")
        grp = cmds.rename(grp, f"CtrlEdit_{self.grp_name}_Group")
        
        cmds.addAttr(grp, ln="YSNodeLabel", dt="string")
        cmds.setAttr(f"{grp}.YSNodeLabel", core.get_controller_edit_module_group(), type="string")
        cmds.setAttr(f"{grp}.YSNodeLabel", l=True)
        
        for axis in "XYZ":
            cmds.setAttr(f"{grp}.scale{axis}", k=False, cb=False)
            cmds.setAttr(f"{lc}.localPosition{axis}", k=False, cb=False, l=True)
            cmds.setAttr(f"{lc}.localScale{axis}", k=False, cb=False, l=True)
        cmds.setAttr(f"{lc}.visibility", False)
        core.set_outliner_color(grp, [0.6, 1.0, 1.0])
        self.grp = grp
        self.settings_node = lc
        cmds.parent(self.grp, core.get_controller_edit_group())

    def pre_process(self):
        pass

    def _create(self):
        pass

    def create(self):
        pass

    def set_color(self):
        klass = self.color_class()
        klass.set_color(self.ctrls, self.side)

    def set_space_transform(self):
        pass

    def _add_settings(self):
        cmds.addAttr(self.settings_node, ln="LineWidth", at="double", min=0, dv=2, k=True)

    def add_settings(self):
        pass

    def _connect(self):
        for ctrl in self.ctrls:
            shapes = cmds.listRelatives(ctrl, s=True, type="nurbsCurve")
            for shape in shapes:
                cmds.connectAttr(f"{self.settings_node}.LineWidth", f"{shape}.lineWidth")

    def connect(self):
        pass

    def _set_attr(self):
        if not cmds.attributeQuery("LineWidth", node=self.meta_node, exists=True):
            return
        
        width = cmds.getAttr(f"{self.meta_node}.LineWidth")
        ctrl_matrices = core.get_list_attributes(self.meta_node, "CtrlsMatrix")

        for ctrl, matrix in zip(self.ctrls, ctrl_matrices):
            pos, rot, scl = core.decompose_matrix(matrix)
            if not core.get_attr_is_locked(ctrl, "translate"):
                cmds.setAttr(f"{ctrl}.translate", *pos)

            if not core.get_attr_is_locked(ctrl, "rotate"):
                cmds.setAttr(f"{ctrl}.rotate", *rot)

            if not core.get_attr_is_locked(ctrl, "scale"):
                cmds.setAttr(f"{ctrl}.scale", *scl)

        cmds.setAttr(f"{self.settings_node}.LineWidth", width)

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

    def _collect_meta_data(self):
        self.meta_data["LineWidth"] = core.compose_attr_paths(self.settings_node, "LineWidth")
        self.meta_data["CtrlsMatrix"] = core.compose_attr_paths(self.ctrls, "matrix", multi=True)
        self.meta_data["CtrlSpacesMatrix"] = core.compose_attr_paths(self.ctrl_spaces, "matrix", multi=True)

    def collect_meta_data(self):
        pass

    def post_process(self):
        pass

    def _set_meta_data(self):
        core.dict_to_attr(self.meta_node, self.meta_data)


class CtrlColorBase:
    """
    コントローラーの色を設定するためのクラス
    CtrlBaseとRigBaseのset_colorメソッドに合成
    """
    def __init__(self):
        pass

    def set_color(self, ctrls, side):
        if side == "L":
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.LEFT_MAIN_COLOR)

        elif side == "R":
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.RIGHT_MAIN_COLOR)

        else:
            for ctrl in ctrls:
                core.set_ctrl_shape_color(ctrl, core.CENTER_MAIN_COLOR)


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
            module = cmds.getAttr(f"{meta}.Module")
            module = importlib.import_module(f"ysrig.modules.{module}.ctrl")
            klass = getattr(module, "Ctrl")
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