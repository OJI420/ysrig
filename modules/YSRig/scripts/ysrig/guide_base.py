import os
import inspect
from traceback import *
from importlib import *
from maya.api.OpenMaya import MGlobal
from maya import cmds
from ysrig import core
reload(core)

META_NODE_SHOW = 0

class GuideBase:
    """
    ガイド作成の基底クラス
    """
    def __init__(self, name, joint_count, parent, side, *args):
        self._setup(name, joint_count, parent, side)         # 変数宣言
        self.setup(*args)
        self._handle_error()                   # エラーハンドリング用
        self.handle_error()

        if self.error:                         # 事前検知でエラーがあればここで終了
            return
        
        cmds.undoInfo(ock=True)
        try:
            self._set_module_name()            # モジュールの名前をファイル名から取得
            self._create_grp()                 # グループノード作成
            self._add_settings()               # 設定用アトリビュート追加
            self.add_settings()
            self._create_meta_node()           # メタノード作成
            self.pre_process()                 # 前処理
            self._create()                     # ノード作成
            self.create()
            self._connect()                    # ノード接続
            self.connect()
            self._lock_attributes()            # ロックするアトリビュートを指定
            self.lock_attributes()
            self._lock()                       # アトリビュートロック
            self._distribute_shape_instances()
            self._collect_meta_data()          # メタノードに書き込む情報を指定
            self.collect_meta_data()
            self._post_process()               # 後処理
            self.post_process()
            self._set_meta_data()              # メタノードに情報書き込み

            cmds.select(cl=True)

        except:
            self.error = True
            cmds.undoInfo(cck=True)
            cmds.undo()
            print_exc()
            MGlobal.displayError("予期せぬエラーが発生しました")
            return

    def _setup(self, name, joint_count, parent, side):
        self.error = False
        self.connect_scale = True
        self.meta_data = {}

        self.grp = None
        self.settings_node = None
        self.meta_node = None

        self.module_name = ""
        self.grp_name = name
        self.parent = parent
        self.side = side
        self.joint_count = joint_count
        self.joint_names = []

        self._lock_attrs = []
        self.lock_attrs = []

        self.root_joint = None
        self.guide_joints = []
        self.guide_joint_spaces = []
        self.guide_proxies = []
        self.guide_nodes = []
        self.guide_node_spaces = []
        self.other_nodes = []
        self.other_node_spaces = []
        self.aim_nodes = []

        self.connect_aim_axis = "XYZ"
        self.aim_vector = [1, 0, 0]
        self.root_radius = 1.0

        self.modules_grp = core.get_guide_modules_group()
        self.facials_grp = core.get_guide_facials_group()

    def setup(self, *args):
        pass

    def _handle_error(self):
        if not cmds.objExists(core.get_root_group()):
            MGlobal.displayError(f"'{core.get_root_group()}' が見つかりませんでした")
            self.error = True
            return

        if not cmds.objExists(core.get_guide_group()):
            MGlobal.displayError(f"'{core.get_guide_group()}' が見つかりませんでした")
            self.error = True
            return

        if not cmds.objExists(core.get_guide_modules_group()):
            MGlobal.displayError(f"'{core.get_guide_modules_group()}' が見つかりませんでした")
            self.error = True
            return

        if cmds.objExists(f"Guide_{self.grp_name}_Group"):
            MGlobal.displayError(f"'{self.grp_name}' はすでに存在しています")
            self.error = True
            return

    def handle_error(self):
        pass

    def _set_module_name(self):
        file_path = inspect.getfile(self.__class__)  # クラスのあるファイルパス
        dir_path = os.path.dirname(file_path)        # 親ディレクトリのパス
        module_name = os.path.basename(dir_path)     # 親ディレクトリの名前
        self.module_name = module_name

    def _create_grp(self):
        lc = core.create_labeled_node("locator", "Guide_Setting")
        grp = cmds.listRelatives(lc, p=True)[0]
        lc = cmds.rename(lc, f"Guide_{self.grp_name}_Settings")
        grp = cmds.rename(grp, f"Guide_{self.grp_name}_Group")
        
        cmds.addAttr(grp, ln="YSNodeLabel", dt="string")
        cmds.setAttr(f"{grp}.YSNodeLabel", core.get_guide_modules_group(), type="string")
        cmds.setAttr(f"{grp}.YSNodeLabel", l=True)
        
        for axis in "XYZ":
            cmds.setAttr(f"{grp}.scale{axis}", k=False, cb=False)
            cmds.setAttr(f"{lc}.localPosition{axis}", k=False, cb=False, l=True)
            cmds.setAttr(f"{lc}.localScale{axis}", k=False, cb=False, l=True)
        cmds.setAttr(f"{lc}.visibility", False)
        core.set_outliner_color(grp, [1.0, 0.6, 0.6])
        self.grp = grp
        self.settings_node = lc

    def _add_settings(self):
        cmds.addAttr(self.settings_node, ln="Orient", at="double", k=True, min=-360, max=360)
        cmds.addAttr(self.settings_node, ln="GoalBone", at="bool", k=True)
        cmds.addAttr(self.settings_node, ln="Mirror", at="bool", k=True)
        cmds.addAttr(self.settings_node, ln="TranslateEnabled", at="bool", k=True)
        cmds.addAttr(self.settings_node, ln="ConnectType", at="enum", en="World:Local:", k=True)

    def add_settings(self):
        pass

    def _create_meta_node(self):
        self.meta_node = core.create_labeled_node("network", "Meta_Node", name=f"Meta_{self.grp_name}")
        cmds.addAttr(self.settings_node, ln="MetaNode", at="message", k=True)
        cmds.connectAttr(f"{self.meta_node}.message", f"{self.settings_node}.MetaNode")
        cmds.setAttr(f"{self.meta_node}.isHistoricallyInteresting", META_NODE_SHOW)

    def pre_process(self):
        pass

    def _create(self):
        self.root_joint = core.create_guide_joint("Guide", f"{self.grp_name}_Global", radius=self.root_radius)

    def create(self):
        pass

    def _connect(self):
        cmds.addAttr(self.root_joint, ln="UniformScale", at="double", min=0.1, dv=1.0, k=True)
        cmds.setAttr(f"{self.root_joint}.radius", k=True)
        cmds.connectAttr(f"{self.root_joint}.UniformScale", f"{self.root_joint}.radius")
        for axis in "XYZ":
            cmds.connectAttr(f"{self.root_joint}.UniformScale", f"{self.root_joint}.scale{axis}")

        aim_nodes = [None] * (len(self.guide_joints) - 1)
        for i, jt, proxy, guide in zip(range(self.joint_count), self.guide_joints, self.guide_proxies, self.guide_node_spaces):
            if i == (len(self.guide_joints) - 1):
                core.connect_point_constraint(jt, proxy)
                core.connect_same_attr(self.guide_node_spaces[i - 1], guide, ["rotate"])

            else:
                core.connect_point_constraint(jt, proxy)
                aim_nodes[i] = core.connect_bend_constraint(proxy, self.guide_proxies[i + 1], guide, axis=self.connect_aim_axis, aim=self.aim_vector)

        self.aim_nodes = aim_nodes

        for guide in self.guide_nodes:
            cmds.connectAttr(f"{self.settings_node}.Orient", f"{guide}.rotateX")

    def connect(self):
        pass

    def _lock_attributes(self):
        self._lock_attrs = [
        self.grp, ["scale"],
        self.root_joint, ["scale", "visibility"],
        self.guide_joints[0], ["translate"]
        ]
        for gj in self.guide_joints:
            self._lock_attrs += [
            gj, ["rotate", "scale", "visibility"]
            ]

    def lock_attributes(self):
        pass

    def _lock(self):
        core.lock_attr(self._lock_attrs)
        core.lock_attr(self.lock_attrs)

    def _distribute_shape_instances(self):
        for node in self.guide_joints + [self.root_joint] + self.other_nodes:
            tmp = cmds.instance(self.settings_node)[0]
            shape = f"{tmp}|{self.settings_node}"
            cmds.parent(shape, node, r=True, s=True)
            cmds.delete(tmp)

    def _collect_meta_data(self):
        self.meta_data["Module"] = self.module_name
        self.meta_data["GroupName"] = self.grp_name
        self.meta_data["ParentName"] = self.parent
        self.meta_data["Side"] = self.side.replace("_", "")
        self.meta_data["JointName"] = self.joint_names
        self.meta_data["JointCount"] = self.joint_count
        self.meta_data["GroupMatrix"] = core.compose_attr_paths(self.grp, "matrix")
        self.meta_data["RootMatrix"] = core.compose_attr_paths(self.root_joint, "matrix")
        self.meta_data["GuideJointsMatrix"] = core.compose_attr_paths(self.guide_joints, "matrix", multi=True)
        self.meta_data["GuidesWorldMatrix"] = core.compose_attr_paths(self.guide_nodes, "worldMatrix[0]", multi=True)
        if self.other_nodes:
            self.meta_data["OtherGuidesMatrix"] = core.compose_attr_paths(self.other_nodes, "matrix", multi=True)
            self.meta_data["OtherGuidesWorldMatrix"] = core.compose_attr_paths(self.other_nodes, "worldMatrix[0]", multi=True)

        self.meta_data["GoalBone"] = core.compose_attr_paths(self.settings_node, "GoalBone")
        self.meta_data["Mirror"] = core.compose_attr_paths(self.settings_node, "Mirror")
        self.meta_data["ConnectType"] = core.compose_attr_paths(self.settings_node, "ConnectType")
        self.meta_data["TranslateEnabled"] = core.compose_attr_paths(self.settings_node, "TranslateEnabled")

    def collect_meta_data(self):
        pass

    def _post_process(self):
        cmds.setAttr(f"{self.root_joint}.otherType", self.joint_names[0], type="string")
        cmds.setAttr(f"{self.root_joint}.drawLabel", True)

        cmds.setAttr(f"{self.guide_joints[0]}.drawStyle", 2)
        cmds.setAttr(f"{self.guide_joints[0]}.drawLabel", False)
        cmds.setAttr(f"{self.guide_joints[0]}.displayHandle", False)
        cmds.setAttr(f"{self.guide_joints[0]}.displayLocalAxis", False)

        cmds.setAttr(f"{self.guide_nodes[0]}.displayLocalAxis", True)

    def post_process(self):
        pass

    def _set_meta_data(self):
        core.dict_to_attr(self.meta_node, self.meta_data)

    def apply_settings(self):
        pass

