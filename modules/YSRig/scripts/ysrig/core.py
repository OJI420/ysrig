import os
import json
import math
from maya import cmds, mel
import maya.api.OpenMaya as om2


VERSION = "2.1.0"

this_file = os.path.abspath(__file__)
prefs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class Curve:
    """
    displaytype = オブジェクトの描画タイプ [Normal, Template, Reference]
    """
    def __init__(self, name, shape_type, display_type=0):
        self.setup(name, shape_type, display_type)
        self.get_json_path()
        self.pre_process()
        self.create()
        self._set_display_type()
        self.reset_shape_name()
        self.set_type()
        self.post_process()

    def setup(self, name, shape_type, display_type):
        self.name = name
        self.json_path = None
        self.shape_node = None
        self.parent_node = None
        self.shape_type = shape_type
        self.scale_uniformly = False
        self.display_type = display_type
        self.outliner_color = [1, 1, 1]

    def get_json_path(self):
        self.json_path = os.path.join(prefs_path, "prefs", "ysrig", "controller_sahpe.json")

    def pre_process(self):
        pass

    def create(self):
        with open(self.json_path, "r") as f:
            ld = json.load(f)
        cv_pos = ld.get(self.shape_type)
        self.scale_uniformly = ld.get(f"{self.shape_type}_Uniform_Scale")
        self.parent_node = cmds.curve(d=1, p=cv_pos, name=self.name)
        self.shape_node = cmds.listRelatives(self.parent_node, s=True)[0]
        cmds.addAttr(self.shape_node, ln="YSNodeType", dt="string")
        cmds.setAttr(f"{self.parent_node}.overrideEnabled", True)
        cmds.setAttr(f"{self.shape_node}.overrideEnabled", True)
        cmds.setAttr(f"{self.shape_node}.isHistoricallyInteresting", 0)

    def _set_display_type(self):
        cmds.setAttr(f"{self.parent_node}.overrideDisplayType", self.display_type)
        cmds.setAttr(f"{self.shape_node}.overrideDisplayType", self.display_type)

    def set_display_type(self, display_type):
        cmds.setAttr(f"{self.shape_node}.overrideDisplayType", display_type)

    def reset_shape_name(self):
        self.shape_node = cmds.rename(self.shape_node, f"{self.parent_node}Shape")

    def reparent_shape(self, parent_node):
        cmds.parent(self.shape_node, parent_node, r=True, s=True)
        cmds.delete(self.parent_node)
        self.parent_node = parent_node
        cmds.setAttr(f"{self.parent_node}.overrideEnabled", True)
        self.reset_shape_name()
        self.set_type()
        self.set_outliner_color(self.outliner_color)

    def set_type(self):
        pass

    def post_process(self):
        pass

    def set_outliner_color(self, color):
        cmds.setAttr(f"{self.parent_node}.useOutlinerColor", True)
        cmds.setAttr(f"{self.parent_node}.outlinerColor", color[0], color[1], color[2])
        self.outliner_color = color

    def set_shape_color(self, color):
        cmds.setAttr(f"{self.shape_node}.overrideRGBColors", 1)
        cmds.setAttr(f"{self.shape_node}.overrideColorRGB", color[0], color[1], color[2])

    def set_scale(self, *args):
        scale = args
        if len(args) == 1:
            scale = [args[0]] * 3

        tmp = cmds.createNode("transform")
        cmds.parent(self.shape_node, tmp, r=True, s=True)
        cmds.setAttr(f"{tmp}.scale", scale[0], scale[1], scale[2])
        cmds.makeIdentity(tmp, a=True)
        cmds.parent(self.shape_node, self.parent_node, r=True, s=True)
        cmds.delete(tmp)
        self.reset_shape_name()

    def set_rotate(self, rotate):
        tmp = cmds.createNode("transform")
        cmds.parent(self.shape_node, tmp, r=True, s=True)
        cmds.setAttr(f"{tmp}.rotate", rotate[0], rotate[1], rotate[2])
        cmds.makeIdentity(tmp, a=True)
        cmds.parent(self.shape_node, self.parent_node, r=True, s=True)
        cmds.delete(tmp)
        self.reset_shape_name()

    def set_translate(self, translate):
        tmp = cmds.createNode("transform")
        cmds.parent(self.shape_node, tmp, r=True, s=True)
        cmds.setAttr(f"{tmp}.translate", translate[0], translate[1], translate[2])
        cmds.makeIdentity(tmp, a=True)
        cmds.parent(self.shape_node, self.parent_node, r=True, s=True)
        cmds.delete(tmp)
        self.reset_shape_name()

    def set_matrix(self, matrix, offset_scale=[1, 1, 1]):
        tf = decompose_matrix(matrix)
        tmp = cmds.createNode("transform")
        cmds.parent(self.shape_node, tmp, r=True, s=True)

        sc = [sc * s for sc, s, in zip(tf[2], offset_scale)]
        cmds.setAttr(f"{tmp}.scale", *sc)
        cmds.setAttr(f"{tmp}.rotate", *tf[1])
        tl = [t * s for t, s, in zip(tf[0], offset_scale)]
        cmds.setAttr(f"{tmp}.translate", *tl)

        cmds.makeIdentity(tmp, a=True)
        cmds.parent(self.shape_node, self.parent_node, r=True, s=True)
        cmds.delete(tmp)
        self.reset_shape_name()

    def set_width(self, width):
        cmds.setAttr(f"{self.shape_node}.lineWidth", width)

    def match_transfomr(self, target, pos=True, rot=True, scl=True):
        cmds.matchTransform(self.parent_node, target, pos=pos, rot=rot, scl=scl)

    def disable_override(self):
        cmds.setAttr(f"{self.shape_node}.overrideEnabled", False)

    def show_pivot(self):
        cmds.setAttr(f"{self.parent_node}.displayRotatePivot", True)


class EditCurve(Curve):
    def pre_process(self):
        self.name = f"Edit_{self.name}"

    def set_type(self):
        if cmds.attributeQuery("YSNodeType", node=self.parent_node, exists=True):
            cmds.setAttr(f"{self.parent_node}.YSNodeType", l=False)

        else:
            cmds.addAttr(self.parent_node, ln="YSNodeType", dt="string")

        cmds.setAttr(f"{self.parent_node}.YSNodeType", "Edit_Curve", l=True, type="string")

        if cmds.attributeQuery("YSNodeType", node=self.shape_node, exists=True):
            cmds.setAttr(f"{self.shape_node}.YSNodeType", l=False)

        else:
            cmds.addAttr(self.shape_node, ln="YSNodeType", dt="string")

        cmds.setAttr(f"{self.shape_node}.YSNodeType", "Edit_Curve_Shape", l=True, type="string")

    def post_process(self):
        self.set_width(4)
        cmds.addAttr(self.shape_node, ln="ScaleUniformly", at="bool")
        cmds.setAttr(f"{self.shape_node}.ScaleUniformly", self.scale_uniformly, l=True)


class CtrlCurve(Curve):
    def pre_process(self):
        self.name = f"Ctrl_{self.name}"

    def set_type(self):
        if cmds.attributeQuery("YSNodeType", node=self.parent_node, exists=True):
            cmds.setAttr(f"{self.parent_node}.YSNodeType", l=False)

        else:
            cmds.addAttr(self.parent_node, ln="YSNodeType", dt="string")

        cmds.setAttr(f"{self.parent_node}.YSNodeType", "Ctrl_Curve", l=True, type="string")

        if cmds.attributeQuery("YSNodeType", node=self.shape_node, exists=True):
            cmds.setAttr(f"{self.shape_node}.YSNodeType", l=False)

        else:
            cmds.addAttr(self.shape_node, ln="YSNodeType", dt="string")

        cmds.setAttr(f"{self.shape_node}.YSNodeType", "Ctrl_Curve_Shape", l=True, type="string")

    def post_process(self):
        self.set_width(4)
        cmds.addAttr(self.shape_node, ln="ScaleUniformly", at="bool")
        cmds.setAttr(f"{self.shape_node}.ScaleUniformly", self.scale_uniformly, l=True)
        self.set_outliner_color([0.8, 0.9, 1.0])


class Hierarchy:
    nodes = []
    def __init__(self, node):
        self.node = node
        self.parent = None
        if Hierarchy.nodes:
            self.parent = Hierarchy.nodes[-1]

    def __enter__(self):
        if self.parent:
            cmds.parent(self.node, self.parent)

        Hierarchy.nodes += [self.node]

    def __exit__(self, *args):
        Hierarchy.nodes = Hierarchy.nodes[:-1]


###  固定の名前　###
def get_root_group():
    return "Rig_Group"

def get_guide_group():
    return "Guide_Group"

def get_guide_modules_group():
    return "Guide_Modules_Group"

def get_guide_facials_group():
    return "Guide_Facials_Group"

def get_skeleton_group():
    return "Skeleton_Group"

def get_facials_root():
    return "Facial"

def get_controller_edit_group():
    return "ControllerEdit_Group"

def get_controller_edit_module_group():
    return "ControllerEdit_Module_Group"

def get_rig_group():
    return "Controller_Group"

def get_rig_module_group():
    return "Controller_Module_Group"

###################

### コントローラーの色 ###

CENTER_MAIN_COLOR = [1.0, 0.3, 0.2]
CENTER_SECOND_COLOR = [0.95, 0.2, 0.15]
CENTER_SARD_COLOR = [1.0, 0.1, 0.1]

RIGHT_MAIN_COLOR = [0.8, 0.8, 0.2]
RIGHT_SECOND_COLOR = [0.75, 0.6, 0.15]
RIGHT_SARD_COLOR = [0.7, 0.4, 0.1]

LEFT_MAIN_COLOR = [0.2, 0.35, 0.8]
LEFT_SECOND_COLOR = [0.1, 0.15, 0.5]
LEFT_SARD_COLOR = [0.0, 0.05, 0.2]

ROOT_MAIN_COLOR = [0.3, 0.0, 0.3]
ROOT_SECOND_COLOR = [0.1, 0.0, 0.1]

FACIAL_COLOR_1 = [0.0, 0.3, 0.3]
FACIAL_COLOR_2 = [0.4, 0.7, 0.1]
FACIAL_COLOR_3 = [0.1, 0.2, 0.15]
FACIAL_COLOR_4 = [0.7, 1.0, 1.0]

###################

def set_ctrl_shape_color(node: str, color: list) -> list:
    """
    カーブシェイプの色を設定する

    Args:
        node (str): ノード名
        color (list of float): shapeの色をRGBで設定する 0.0 ~ 1.0 の浮動小数点数型3つのリスト

    Returns:
        list: 設定されたRGB値 [R, G, B]
    """
    shapes = cmds.listRelatives(node, s=True, type="nurbsCurve")
    for shape in shapes:
        cmds.setAttr(f"{shape}.overrideRGBColors", 1)
        cmds.setAttr(f"{shape}.overrideColorRGB", color[0], color[1], color[2])

    return color


def clamp_curve_y_zero(node: str) -> None:
    """指定ノード配下のNURBSカーブCVを、Y<0の場合Y=0にクランプする

    Args:
        node (str): 処理対象となるtransformノード名

    Returns:
        None
    """
    # 子シェイプを取得（typeでフィルタ）
    shapes = cmds.listRelatives(node, children=True, type="nurbsCurve", fullPath=True) or []
    if not shapes:
        return

    for shape in shapes:
        # CV数を取得
        cv_count = cmds.getAttr(f"{shape}.controlPoints", size=True)

        for i in range(cv_count):
            cv_name = f"{shape}.cv[{i}]"

            # ワールド座標を取得
            pos = cmds.pointPosition(cv_name, world=True)

            if pos[1] < 0.0:
                # y=0 に補正した位置をセット
                new_pos = (pos[0], 0.0, pos[2])
                cmds.xform(cv_name, ws=True, t=new_pos)


def set_shape_matrix(node, matrix, offset_scale=[1, 1, 1]):
    tf = decompose_matrix(matrix)
    shapes = cmds.listRelatives(node, s=True)
    for shape in shapes:
        tmp = cmds.createNode("transform")
        cmds.parent(shape, tmp, r=True, s=True)

        sc = [sc * s for sc, s, in zip(tf[2], offset_scale)]
        cmds.setAttr(f"{tmp}.scale", *sc)
        cmds.setAttr(f"{tmp}.rotate", *tf[1])
        tl = [t * s for t, s, in zip(tf[0], offset_scale)]
        cmds.setAttr(f"{tmp}.translate", *tl)

        cmds.makeIdentity(tmp, a=True)
        cmds.parent(shape, node, r=True, s=True)
        cmds.delete(tmp)
        cmds.rename(shape, f"{node}Shape")


def set_curve_width(node, width):
    shapes = cmds.listRelatives(node, s=True)
    for shape in shapes:
        cmds.setAttr(f"{shape}.lineWidth", width)


def create_hierarchy(*args):
    """
    任意の階層を作成
    リストの0番目がrootノード
    ":"で階層を下がり
    ".."で階層を上がる
    """
    parents = [args[0]]
    nodes = args[1:]

    for i, node in enumerate(nodes):
        if node == ":":
            parents += [nodes[i - 1]]
            continue

        if node == "..":
            parents = parents[:-1]
            continue

        cmds.parent(node, parents[-1])


def create_labeled_node(node_type, ysnode_type, name=""):
    if not name:
        name = node_type

    node = cmds.createNode(node_type, name=name)
    cmds.addAttr(node, ln="YSNodeLabel", dt="string")
    cmds.setAttr(f"{node}.YSNodeLabel", ysnode_type, type="string", l=True)
    return node


def create_node(node_type, name=""):
    if not name:
        name = node_type

    node = cmds.createNode(node_type, name=name)
    cmds.setAttr(f"{node}.isHistoricallyInteresting", 0)
    return node


def create_space(node, suffix="Space", parent=False):
    space_node = cmds.createNode("transform", name=f"{node}_{suffix}")
    parent_node =  cmds.listRelatives(node, p=True) or []
    if parent_node:
        cmds.parent(space_node, parent_node[0])

    cmds.matchTransform(space_node, node, pos=True, rot=True, scl=True)
    if parent:
        cmds.parent(node, space_node)

    cmds.setAttr(f"{space_node}.useOutlinerColor", True)
    cmds.setAttr(f"{space_node}.outlinerColor", 0, 0, 0)
    return space_node


def create_guide_joint(prefix, name, style=3, display_type=0, view_axis=False, color=[0.6, 0.0, 0.6], radius=0.5, show_label=True, label=None, outliner=True):#ガイド用ジョイント作成
    """
    style = ジョイントの描画スタイル [Bone, Multi-child as Box, None, Joint]
    displaytype = オブジェクトの描画タイプ [Normal, Template, Reference]
    """

    if "_GB" in name:
        color = [0.6, 0.3, 0.0]

    if "_Global" in name:
        color = [0.6, 0.0, 0.0]

    if "GUideProxy" == prefix:
        style=0
        display_type=2
        if radius == 0.5:
            radius=0.2
        show_label=False
        outliner=False

    if not label:
        label = name

    joint = create_labeled_node("joint", "GudieJoint", name=f"{prefix}_{name}")
    cmds.setAttr(f"{joint}.segmentScaleCompensate", False)
    cmds.setAttr(f"{joint}.drawStyle", style)
    cmds.setAttr(f"{joint}.side", 0)
    cmds.setAttr(f"{joint}.type", 18)
    cmds.setAttr(f"{joint}.otherType", label, type="string")
    cmds.setAttr(f"{joint}.drawLabel", show_label)
    cmds.setAttr(f"{joint}.displayHandle", show_label)
    cmds.setAttr(f"{joint}.displayLocalAxis", view_axis)
    cmds.setAttr(f"{joint}.overrideEnabled", True)
    cmds.setAttr(f"{joint}.overrideDisplayType", display_type)
    cmds.setAttr(f"{joint}.overrideRGBColors", True)
    cmds.setAttr(f"{joint}.overrideColorRGB", color[0], color[1], color[2])
    cmds.setAttr(f"{joint}.useOutlinerColor", True)
    cmds.setAttr(f"{joint}.outlinerColor", color[0], color[1], color[2])
    cmds.setAttr(f"{joint}.radius", radius, cb=False)
    cmds.setAttr(f"{joint}.hiddenInOutliner", not outliner)
    return joint


def create_guide_node(name):
    guide = cmds.createNode("transform", name=f"JTSource_{name}")
    #cmds.setAttr(f"{guide}.displayLocalAxis", True)
    cmds.setAttr(f"{guide}.hiddenInOutliner", True)
    return guide


def create_rig_grp():
    rig_grp = create_labeled_node("transform", get_root_group(), name=get_root_group())
    set_outliner_color(rig_grp, [1.0, 1.0, 1.0])
    cmds.addAttr(rig_grp, ln="YSRigVersion", dt="string")
    cmds.addAttr(rig_grp, ln="BuildType", dt="string")
    cmds.addAttr(rig_grp, ln="SourceFileName", dt="string")
    cmds.setAttr(f"{rig_grp}.YSRigVersion", VERSION, type="string", l=True)
    cmds.setAttr(f"{rig_grp}.BuildType", "Manual", type="string", l=True)
    cmds.setAttr(f"{rig_grp}.SourceFileName", "", type="string", l=True)
    return rig_grp


def convert_joint_to_controller(joints: list[str], prefix: str="Ctrl_", sr: list[str]=["", ""]) -> list:
    """
    ジョイントをコントローラー用に変換する
    ジョイントを複製し接頭辞をコントローラー用に変更、ジョイントのシェイプを非表示にする

    Args:
        joints (list of str): ジョイントのリスト
        prefix (str): "JT_"から置換する接頭辞

    Returns:
        list of str: コントローラー用に変換されたジョイント
    """

    ctrls = cmds.duplicate(joints, po=True, rc=True)
    joints = [jt.replace(sr[0], sr[1]) for jt in joints]
    for i, ctrl in enumerate(ctrls):
        cmds.setAttr(f"{ctrl}.drawStyle", 2)
        cmds.setAttr(f"{ctrl}.radius", l=False)
        cmds.setAttr(f"{ctrl}.radius", cb=False, k=False, l=True)
        name = joints[i].replace("JT_", prefix)
        ctrls[i] = cmds.rename(ctrl, name)

    return ctrls


def create_numbered_names(name, num, gb=True):
    names = [None] * num
    for i in range(num):
        if i == num - 1 and gb:
            names[i] = f"{name}_GB"

        else:
            names[i] = f"{name}_{i + 1:02d}"

    return names


def connect_curve_point(name, nodes: list, parent: str="", lc: bool=False) -> list:
    """
    各ノードに各コントロールポイントが拘束されたカーブを作成する

    Args:
        nodes (list of str): コントロールポイントを拘束するノードのリスト
        parent (str): カーブノードの親
        lc (bool): ローカル接続

    Returns:
        str: 作成したカーブノード
    """

    point_count = len(nodes)
    curve = cmds.curve(d=1, p=[[0, 0, 0]] * point_count, name=name)
    shape = cmds.listRelatives(curve, s=True)[0]
    cmds.setAttr(f"{curve}.overrideEnabled", True)
    cmds.setAttr(f"{curve}.overrideDisplayType", 2)
    if parent:
        cmds.parent(curve, parent)
        cmds.makeIdentity(curve)

    for i, node in enumerate(nodes):
        mm = create_node("multMatrix", name=f"Mm_{curve}_{i + 1}")
        if lc:
            connect_local_matrix_to_mm(node, curve, mm, start=0)

        else:
            connect_world_matrix_to_mm(node, curve, mm, start=0)

        dm = create_node("decomposeMatrix", name=f"Dm_{curve}_{i + 1}")
        cmds.connectAttr(f"{mm}.matrixSum", f"{dm}.inputMatrix")
        cmds.connectAttr(f"{dm}.outputTranslate", f"{shape}.controlPoints[{i}]")

    return curve


def compose_attr_paths(nodes, attr, multi=False):
    if not isinstance(nodes, list):
        nodes = [nodes]
    paths = [None] * len(nodes)
    for i, node in enumerate(nodes):
        paths[i] = f"{node}.{attr}"

    if multi:
        return paths
    else:
        return paths[0]


def print_list(name: str, in_list: list) -> None:
    l = len(in_list)
    print('"""')
    print(name)
    for i, item in enumerate(in_list):
        print(f"[{i}] [-{l - i}] -> {item}")

    print('"""')


def get_attr_is_locked(node: str, attr: str) -> bool:
    """
    ノードがロックされているか調べる

    Args:
        node (str): ノード名
        attr (str): 調べるアトリビュート

    Returns:
        bool: ロックされていたら -> True
    """

    special_attrs = {}
    special_attrs["translate"] = ["tx", "ty", "tz"]
    special_attrs["rotate"] = ["rx", "ry", "rz"]
    special_attrs["scale"]  = ["sx", "sy", "sz"]
    is_locked = False

    if cmds.getAttr(f"{node}.{attr}", l=True):
        is_locked = True

    if cmds.listConnections(f"{node}.{attr}", d=False, s=True):
        is_locked = True

    for sa in special_attrs:
        if attr == sa:
            for a in special_attrs[sa]:
                if cmds.getAttr(f"{node}.{a}", l=True):
                    is_locked = True

                if cmds.listConnections(f"{node}.{a}", d=False, s=True):
                    is_locked = True

    return is_locked


def get_list_attributes(node: str, attr: str) -> list:
    """
    multi型のアトリビュートをlistで返す

    Args:
        node (str): ノード名
        attr (str): multi型のアトリビュート名からインデックスを抜いた文字列

    Returns:
        list: ["ノード名.アトリビュート名[インデックス]"]
    """

    list_count = cmds.getAttr(f"{node}.{attr}", mi=True)[-1] + 1 # lenで取るとboolとlongの初期値と同じデータがmayaに削除される
    attrs = [None] * list_count
    for i in range(list_count):
        attrs[i] = cmds.getAttr(f"{node}.{attr}[{i}]")

    return attrs


def get_enum_attribute(node, attr):
    enum_str = cmds.addAttr(f"{node}.{attr}", q=True, enumName=True)
    index = cmds.getAttr(f"{node}.{attr}")
    labels = enum_str.split(":")

    return labels[index]


def get_meta_nodes():
    guide_group = get_guide_group()
    guide_modules_group = get_guide_modules_group()

    if not cmds.objExists(guide_group):
        return []

    root_module = cmds.listRelatives(guide_group, c=True)[0]
    guide_modules = cmds.listRelatives(guide_modules_group, c=True) or []

    modules_count = len(guide_modules)

    meta_nodes = [None] * modules_count

    root_settings = cmds.listRelatives(root_module, s=True)[0]
    meta_nodes[0] = cmds.listConnections(root_settings, s=False, d=True, type="network")[0]

    for i, module in enumerate(guide_modules):
        if module == get_guide_facials_group():
            continue
        
        settings = cmds.listRelatives(module, s=True)[0]
        meta_nodes[i] = cmds.listConnections(settings, s=False, d=True, type="network")[0]

    return meta_nodes


def get_facial_meta_nodes():
    guide_facials_group = get_guide_facials_group()

    if not cmds.objExists(guide_facials_group):
        return []

    guide_modules = cmds.listRelatives(guide_facials_group, c=True) or []

    modules_count = len(guide_modules)

    meta_nodes = [None] * modules_count

    for i, module in enumerate(guide_modules):
        if module == get_guide_facials_group():
            continue
        
        settings = cmds.listRelatives(module, s=True)[0]
        meta_nodes[i] = cmds.listConnections(settings, s=False, d=True, type="network")[0]

    return meta_nodes


def get_distance(pos1 :list, pos2: list) -> float: 
    """
    2つの位置ベクトル間のユークリッド距離を返す

    Args:
        pos1 (list or tuple): [x, y, z] などの座標リスト
        pos2 (list or tuple): [x, y, z] などの座標リスト

    Returns:
        float: 2点間の距離
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos1, pos2)))


def get_round_rotate(rotate: list):
    """
    rotate値を90度ずつに丸める

    Args:
        rotate (list or tuple): rotate値

    Returns:
        list: 90度ずつに丸めたrotate値
    """
    return [round(r / 90) * 90 for r in rotate]


def get_divide_positions(start_end, divisions):
    """
    divisionsの数だけ三次元座標を分割して返す
    たとえば divisions = 3 なら
    [start, 中間, end] を返す
    """
    start = start_end[0]
    end = start_end[1]
    result = [None] * divisions
    for i in range(divisions):
        t = i / (divisions - 1)
        point = [
            start[0] + (end[0] - start[0]) * t,
            start[1] + (end[1] - start[1]) * t,
            start[2] + (end[2] - start[2]) * t
        ]
        result[i] = point
    return result


def get_chunk_list(src_list: list, chunk: int) -> list:
    """
    リストを指定した数ごとに分割したリストを返す

    Args:
        src_list (list or tuple): 分割したいリスト 
        chunk (int): 分割する単位

    Returns: 
        list: 分割されたリスト chunk=2の場合 -> [[0, 1], [2, 3], [4, 5], [6]]
    """
    return [src_list[i:i + chunk] for i in range(0, len(src_list), chunk)]


def get_average_pos_matrix(matrix_list: list) -> list:
    """
    複数のmatrixを受け取り、その平均位置のmatrixを返す

    Args:
        matrix_list (list of list of float): 各要素が16要素のfloatリストのリスト

    Returns:
        list of float: 平均位置を取ったmatrix（16要素のリスト）
    """
    total_translation = om2.MVector(0, 0, 0)

    for mat in matrix_list:
        m = om2.MMatrix(mat)
        t = om2.MTransformationMatrix(m).translation(om2.MSpace.kWorld)
        total_translation += t

    avg_translation = total_translation / len(matrix_list)

    # 平行移動のみの変換マトリックスを作成
    result_transform = om2.MTransformationMatrix()
    result_transform.setTranslation(avg_translation, om2.MSpace.kWorld)
    result_matrix = list(result_transform.asMatrix())

    return result_matrix


def multiply_list(float_list: list, multiplier: float) -> list:
    """
    listの各要素にある数を掛け合わせる

    Args:
        float_list (list of float): 掛け合わせたい数のリスト
        multiplier (float): 掛け合わせたい数

    Returns:
        list: 掛け合わせた数のリスト
    """
    return [x * multiplier for x in float_list]


def auto_scale_chain_ctrls(spaces: list, matrices: list, scale: float, scale_uniformly: bool) -> float:
    """
    Chain状に階層化される編集用コントローラースペースのスケールを自動で設定する

    Args:
        spaces (list or tuple): コントローラースペースのリスト
        matrices (list or tuple): 4*4行列のリスト
        scale (float): 最終的に設定されるscaleに掛け合わされる数
        scale_uniformly (bool): コントローラーのscaleが、三軸同じか、X軸のみ距離から設定するかの真偽値

    Returns:
        float: 最終的に設定されたscale値
    """
    all_dis = 0
    for i, space in enumerate(spaces):
        pos, rot = decompose_matrix(matrices[i])[:-1]
        next_pos = decompose_matrix(matrices[i + 1])[0]
        dis = get_distance(pos, next_pos)
        all_dis += dis
        cmds.setAttr(f"{space}.translate", *pos)
        cmds.setAttr(f"{space}.rotate", *rot)
        if not scale_uniformly:
            cmds.setAttr(f"{space}.scaleX", dis)

    average_dis = all_dis / len(spaces)
    scale  = average_dis * scale

    for space in spaces:
        if scale_uniformly:
            cmds.setAttr(f"{space}.scale", scale, scale, scale)

        else:
            cmds.setAttr(f"{space}.scaleY", scale)
            cmds.setAttr(f"{space}.scaleZ", scale)

    return scale


def decompose_matrix(matrix_list: list) -> list:
    """
    行列リストを分解し、translate, rotate, scaleを抽出

    Args:
        matrix_list (list or tuple): 4x4の行列

    Returns:
        list: [[tx, ty, tz], [rx, ry, rz], [sx, sy, sz]]
    """
    matrix = om2.MMatrix(matrix_list)
    transform = om2.MTransformationMatrix(matrix)

    # translate
    translation = transform.translation(om2.MSpace.kWorld)
    t = [translation.x, translation.y, translation.z]

    # rotate
    euler = transform.rotation(asQuaternion=False)
    r = [math.degrees(euler.x), math.degrees(euler.y), math.degrees(euler.z)]

    # scale
    s = transform.scale(om2.MSpace.kWorld)

    return [t, r, s]


def set_outliner_color(node, color):
    cmds.setAttr(f"{node}.useOutlinerColor", True)
    cmds.setAttr(f"{node}.outlinerColor", color[0], color[1], color[2])


def dict_to_attr(node: str, dict: dict) -> None:
    """
    辞書型のデータをアトリビュートとしてノードに追加し設定する

    文字列データのなかに"."が含まれていた場合、アトリビュートとして解釈し、追加したアトリビュートに接続する

    データがリスト型の場合、multi型アトリビュートとして設定する

    データがタプル型の場合、matirxとして処理する

    Args:
        node (str): アトリビュートを設定するノード名
        dict (dict): 追加するアトリビュート群
    """

    def check_attr(key: str) -> bool:
        """
        アトリビュートが存在しないかを調べて、あればFalse、なければTrueを返す
        存在した場合、アトリビュートのロックを外す

        Args:
            key: アトリビュートの名前
        
        Returns:
            bool: アトリビュートが存在しないかどうか
        """
        if cmds.attributeQuery(key, node=node, exists=True):
            cmds.setAttr(f"{node}.{key}", l=False)
            return False

        else:
            return True

    def check_list_attr(key: str) -> bool:
        """
        リスト型のアトリビュートが存在しないかを調べて、あればFalse、なければTrueを返す
        存在した場合、アトリビュートのロックを外す

        Args:
            key: アトリビュートの名前
        
        Returns:
            bool: アトリビュートが存在しないかどうか
        """
        if cmds.attributeQuery(key, node=node, exists=True):
            index = cmds.getAttr(f"{node}.{key}", size=True)
            for i in range(index):
                cmds.setAttr(f"{node}.{key}[{i}]", l=False)

            return False

        else:
            return True

    ### 静的な単数アトリビュート ###

    def str_attr(key, data): # 文字列型の静的アトリビュート
        if check_attr(key):
            cmds.addAttr(node, ln=key, dt="string")

        cmds.setAttr(f"{node}.{key}", data, type="string", l=True)

    def float_attr(key, data): # 浮動小数点数型の静的アトリビュート
        if check_attr(key):
            cmds.addAttr(node, ln=key, at="double")

        cmds.setAttr(f"{node}.{key}", data, l=True)

    def int_attr(key, data): # 整数型の静的アトリビュート
        if check_attr(key):
            cmds.addAttr(node, ln=key, at="long")

        cmds.setAttr(f"{node}.{key}", data, l=True)

    def bool_attr(key, data): # 真偽値型の静的アトリビュート
        if check_attr(key):
            cmds.addAttr(node, ln=key, at="bool")

        cmds.setAttr(f"{node}.{key}", data, l=True)

    def matrix_attr(key, data): # 行列型の静的アトリビュート
        if check_attr(key):
            cmds.addAttr(node, ln=key, dt="matrix")

        cmds.setAttr(f"{node}.{key}", data, type="matrix", l=True)

    ### 静的な複数アトリビュート ###

    def list_of_str_attr(key, data): # 文字列のリスト型静的アトリビュート
        if check_list_attr(key):
            cmds.addAttr(node, ln=key, dt="string", multi=True)

        for i, d in enumerate(data):
            cmds.setAttr(f"{node}.{key}[{i}]", d, type="string", l=True)

    def list_of_float_attr(key, data): # 浮動小数点数のリスト型静的アトリビュート
        if check_list_attr(key):
            cmds.addAttr(node, ln=key, at="double", multi=True)

        for i, d in enumerate(data):
            cmds.setAttr(f"{node}.{key}[{i}]", d, l=True)

    def list_of_int_attr(key, data): # 整数のリスト型静的アトリビュート
        if check_list_attr(key):
            cmds.addAttr(node, ln=key, at="long", multi=True)

        for i, d in enumerate(data):
            cmds.setAttr(f"{node}.{key}[{i}]", d, l=True)

    def list_of_bool_attr(key, data): # 真偽値のリスト型静的アトリビュート
        if check_list_attr(key):
            cmds.addAttr(node, ln=key, at="bool", multi=True)

        for i, d in enumerate(data):
            cmds.setAttr(f"{node}.{key}[{i}]", d, l=True)

    def list_of_matrix_attr(key, data): # 行列のリスト型静的アトリビュート
        if check_list_attr(key):
            cmds.addAttr(node, ln=key, dt="matrix", multi=True)

        for i, d in enumerate(data):
            cmds.setAttr(f"{node}.{key}[{i}]", d, type="matrix", l=True)

    # addAttrでdtの引数で設定されるアトリビュート型
    DT_TYPES = {
        "string", "matrix", "double3", "float3", "double2", "float2",
        "vectorArray", "pointArray", "nurbsCurve", "nurbsSurface",
        "reflectanceRGB", "spectrumRGB", "floatArray", "doubleArray",
        "Int32Array", "compound"
    }

    ### 動的な単数アトリビュート ###

    def connect_singular_attr(key, data, attr_type):
        if check_attr(key):
            if attr_type in DT_TYPES:
                cmds.addAttr(node, ln=key, dt=attr_type)
            
            elif attr_type == "enum":
                n, a = data.split(".")
                enum = cmds.attributeQuery(a, node=n, listEnum=True)[0]
                cmds.addAttr(node, ln=key, at=attr_type, en=enum)

            else:
                cmds.addAttr(node, ln=key, at=attr_type)

        cmds.connectAttr(data, f"{node}.{key}")
        cmds.setAttr(f"{node}.{key}", l=True)

    ### 動的な複数アトリビュート ###

    def connect_list_attr(key, data, attr_type):
        if check_list_attr(key):
            if attr_type in DT_TYPES:
                cmds.addAttr(node, ln=key, dt=attr_type, multi=True)

            else:
                cmds.addAttr(node, ln=key, at=attr_type, multi=True)

        for i, d in enumerate(data):
            cmds.connectAttr(d, f"{node}.{key}[{i}]")
            cmds.setAttr(f"{node}.{key}[{i}]", l=True)

    for key in dict:
        data = dict[key]
        if isinstance(data, list):
            d = data[0]
            if isinstance(d, str):
                if "." in d:
                    attr_type = cmds.getAttr(d, type=True)
                    connect_list_attr(key, data, attr_type)

                else:
                    list_of_str_attr(key, data)

            elif isinstance(d, tuple):
                list_of_matrix_attr(key, data)

            elif isinstance(d, float):
                list_of_float_attr(key, data)

            elif isinstance(d, bool):
                list_of_bool_attr(key, data)

            elif isinstance(d, int):
                list_of_int_attr(key, data)

        else:
            if isinstance(data, str):
                if "." in data:
                    attr_type = cmds.getAttr(data, type=True)
                    connect_singular_attr(key, data, attr_type)

                else:
                    str_attr(key, data)

            elif isinstance(data, tuple):
                matrix_attr(key, data)

            elif isinstance(data, float):
                float_attr(key, data)

            elif isinstance(data, bool):
                bool_attr(key, data)

            elif isinstance(data, int):
                int_attr(key, data)


def list_to_tuple(in_list: list[list]) -> list[tuple]:
    """
    リストのリストを、タプルのリストに変換する
    """
    return [tuple(l) for l in in_list]


def get_offset_matrix(node1: str, node2: str) -> list:
    """
    2つのノードのワールド上の差分のMatrixを返す

    Args:
        node1 (str): 差分を取りたいノード1
        node2 (str): 差分を取りたいノード2

    Returns:
        list : 差分の行列をリストにしたもの

    """
    mm = cmds.createNode("multMatrix", name="tmp")

    cmds.connectAttr(f"{node2}.worldMatrix[0]", f"{mm}.matrixIn[0]")
    cmds.connectAttr(f"{node1}.worldInverseMatrix[0]", f"{mm}.matrixIn[1]")

    offset_matrix = cmds.getAttr("%s.matrixSum"%(mm))
    cmds.delete(mm)

    return offset_matrix


def connect_world_matrix_to_mm(src: str, dest: str, mm_node: str, start: int=1) -> int:
    """
    multMatrixノードにworldMatrixを接続する

    Args:
        src (str): 拘束する側のノード名
        dest (str): 拘束される側のノード名
        start (str): 接続する一つ目のインデックス

    Returns:
        int : multMatrixノードの、次に空いているインデックス
    """
    cmds.connectAttr(f"{src}.worldMatrix[0]",f"{mm_node}.matrixIn[{start}]")
    cmds.connectAttr(f"{dest}.parentInverseMatrix[0]",f"{mm_node}.matrixIn[{start + 1}]")

    return start + 2


def connect_local_matrix_to_mm(src: str, dest: str, mm_node: str, start: int=1) -> int:
    """
    multMatrixノードにlocalMatrixを接続する

    Args:
        src (str): 拘束する側のノード名
        dest (str): 拘束される側のノード名
        start (str): 接続する一つ目のインデックス

    Returns:
        int : multMatrixノードの、次に空いているインデックス
    """
    srcs = cmds.listRelatives(src, allParents=True, fullPath=True)[0] + "|" + src
    dsts = cmds.listRelatives(dest, allParents=True, fullPath=True)[0]

    srcs = srcs.split('|')[1:]
    dsts = dsts.split('|')[1:]

    root = None
    i = 0
    src = srcs
    dest = dsts + [dest]
    while True:
        if src[i] == dest[i]:
            root = src[i]
            i += 1
        else:
            break

    srcs = list(reversed(srcs[srcs.index(root) + 1:]))
    dsts = dsts[dsts.index(root) + 1:]
    
    for i, node in enumerate(srcs, start=start):
        cmds.connectAttr(f"{node}.matrix", f"{mm_node}.matrixIn[{i}]")

    index = len(srcs) + start

    for i, node in enumerate(dsts, start=index):
        cmds.connectAttr(f"{node}.inverseMatrix", f"{mm_node}.matrixIn[{i}]")

    index += len(dsts)
    return index


def connect_matrix(src: str, dest: str, tl: bool=False, rt: bool=False, sc: bool=False, lc: bool=False, suffix: str="") -> list:
    """
    matrixでノード同士を拘束する

    Args:
        src (str): 拘束する側のノード名
        dest (str): 拘束される側のノード名
        tl (bool): translateを接続するかを設定します 既定値 -> False
        rt (bool): rotateを接続するかを設定します 既定値 -> False
        sc (bool): scaleを接続するかを設定します 既定値 -> False
        lc (bool): ローカル計算で接続するかを設定します 既定値 -> False
        suffix (str): ノードの接尾辞に追加する文字列

    Returns:
        list : 作成されたノードのリスト [mm_node, dm_node, mm_rot_node, dm_rot_node]
    """
    mm_node = create_node("multMatrix", name=f"Mm_{dest}{suffix}")
    cmds.setAttr(f"{mm_node}.matrixIn[0]", get_offset_matrix(src, dest), type="matrix")
    if lc:
        index = connect_local_matrix_to_mm(src, dest, mm_node)

    else:
        index = connect_world_matrix_to_mm(src, dest, mm_node)

    node_type = cmds.nodeType(dest)
    if node_type == "joint":
        tmp_cm = cmds.createNode("composeMatrix", name="tmp_Cm")
        tmp_im = cmds.createNode("inverseMatrix", name="tmp_Im")
        cmds.connectAttr(f"{dest}.jointOrient", f"{tmp_cm}.inputRotate")
        cmds.connectAttr(f"{tmp_cm}.outputMatrix", f"{tmp_im}.inputMatrix")
        cmds.setAttr(f"{mm_node}.matrixIn[{index}]", cmds.getAttr(f"{tmp_im}.outputMatrix"), type="matrix")
        cmds.delete(tmp_cm, tmp_im)

    dm_node = create_node("decomposeMatrix", name=f"Dm_{dest}{suffix}")
    cmds.connectAttr(f"{mm_node}.matrixSum", f"{dm_node}.inputMatrix")

    mm_rot_node = None
    dm_rot_node = None

    connect_type = 1
    if node_type == "joint":
        if tl or sc:
            mm_rot_node = cmds.rename(mm_node, f"{mm_node}_Rot")
            dm_rot_node = cmds.rename(dm_node, f"{dm_node}_Rot")
            mm_node, dm_node = cmds.duplicate([mm_rot_node, dm_rot_node], ic=True)

            mm_node = cmds.rename(mm_node, mm_node.replace("_Rot1", ""))
            dm_node = cmds.rename(dm_node, dm_node.replace("_Rot1", ""))
            cmds.setAttr(f"{mm_node}.matrixIn[{index}]", [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1], type="matrix")
            connect_type = 2

    if connect_type == 1:
        if tl:
            for axis in "XYZ":
                cmds.connectAttr(f"{dm_node}.outputTranslate{axis}", f"{dest}.translate{axis}")
        if rt:
            for axis in "XYZ":
                cmds.connectAttr(f"{dm_node}.outputRotate{axis}", f"{dest}.rotate{axis}")
        if sc:
            for axis in "XYZ":
                cmds.connectAttr(f"{dm_node}.outputScale{axis}", f"{dest}.scale{axis}")
            cmds.connectAttr(f"{dm_node}.outputShear", f"{dest}.shear")

    if connect_type == 2:
        if tl:
            for axis in "XYZ":
                cmds.connectAttr(f"{dm_node}.outputTranslate{axis}", f"{dest}.translate{axis}")
        if rt:
            for axis in "XYZ":
                cmds.connectAttr(f"{dm_rot_node}.outputRotate{axis}", f"{dest}.rotate{axis}")
        if sc:
            for axis in "XYZ":
                cmds.connectAttr(f"{dm_node}.outputScale{axis}", f"{dest}.scale{axis}")
            cmds.connectAttr(f"{dm_node}.outputShear", f"{dest}.shear")
        if not rt:
            cmds.delete(mm_node, dm_node)

    return [mm_node, dm_node, mm_rot_node, dm_rot_node]


def connect_uniform_scale(node):
    cmds.connectAttr(f"{node}.scaleX", f"{node}.scaleY")
    cmds.connectAttr(f"{node}.scaleX", f"{node}.scaleZ")
    if cmds.attributeQuery("radius", node=node, exists=True):
        if cmds.getAttr(f"{node}.radius", l=True):
            return

        cmds.setAttr(f"{node}.radius", k=True)
        cmds.connectAttr(f"{node}.scaleX", f"{node}.radius")


def connect_world_distance_node(node1, node2):
    db = create_node("distanceBetween", name=f"Db_{node1}_{node2}")
    for i, node in enumerate([node1, node2]):
        dm = create_node("decomposeMatrix", name=f"Dm_{db}_0{i + 1}")
        cmds.connectAttr(f"{node}.worldMatrix[0]", f"{dm}.inputMatrix")
        cmds.connectAttr(f"{dm}.outputTranslate", f"{db}.point{i + 1}")
    return db


def connect_distance_to_sx(src1, src2, dest, src_attr1="translate", src_attr2="translate"):
    db = create_node("distanceBetween", name=f"Db_{dest}")
    cmds.connectAttr(f"{db}.distance", f"{dest}.scaleX")
    cmds.connectAttr(f"{src1}.{src_attr1}", f"{db}.point1")
    if src2:
        cmds.connectAttr(f"{src2}.{src_attr2}", f"{db}.point2")
    return db


def connect_bend_constraint(src, target, dest, axis="XYZ", aim=[1, 0, 0]):
    aim_node = cmds.createNode("aimConstraint", name=f"{dest}_aimConstraint1")

    cmds.parent(aim_node, dest)
    cmds.makeIdentity(aim_node)

    cmds.setAttr(f"{aim_node}.worldUpType", 4)
    cmds.setAttr(f"{aim_node}.hiddenInOutliner", True)
    cmds.setAttr(f"{aim_node}.isHistoricallyInteresting", 0)
    cmds.setAttr(f"{aim_node}.aimVector", aim[0], aim[1], aim[2])

    cmds.connectAttr(f"{src}.rotate", f"{aim_node}.rotate")
    cmds.connectAttr(f"{target}.translate", f"{aim_node}.target[0].targetTranslate")
    cmds.connectAttr(f"{aim_node}.matrix", f"{aim_node}.target[0].targetParentMatrix")
    
    for a in axis:
        cmds.connectAttr(f"{aim_node}.constraintRotate{a}", f"{dest}.rotate{a}")

    return aim_node


def connect_aim_constraint(target, dest, aim=[1, 0, 0], offset=True, sk="x"):
    if sk:
        aim_node = cmds.aimConstraint(target, dest, mo=offset, w=1, aim=aim, u=[0, 1, 0], wut="none", sk=sk)[0]

    else:
        aim_node = cmds.aimConstraint(target, dest, mo=offset, w=1, aim=aim, u=[0, 1, 0], wut="none")[0]

    cmds.setAttr(f"{aim_node}.hiddenInOutliner", True)
    cmds.setAttr(f"{aim_node}.isHistoricallyInteresting", 0)
    return aim_node


def connect_point_constraint(src, dest, mo=False):
    node = cmds.pointConstraint(
                src,
                dest,
                mo=mo,
                w=1,
                )[0]

    cmds.setAttr(f"{node}.hiddenInOutliner", True)
    cmds.setAttr(f"{node}.isHistoricallyInteresting", 0)
    return node


def connect_orient_constraint(src, dest, mo=False):
    node = cmds.orientConstraint(
                src,
                dest,
                mo=mo,
                w=1,
                )[0]

    cmds.setAttr(f"{node}.hiddenInOutliner", True)
    cmds.setAttr(f"{node}.isHistoricallyInteresting", 0)
    return node


def connect_parent_constraint(src, dest, mo=False):
    node = cmds.parentConstraint(
                src,
                dest,
                mo=mo,
                w=1,
                )[0]

    cmds.setAttr(f"{node}.hiddenInOutliner", True)
    cmds.setAttr(f"{node}.isHistoricallyInteresting", 0)
    return node


def connect_scale_constraint(src, dest, mo=False):
    node = cmds.scaleConstraint(
                src,
                dest,
                mo=mo,
                w=1,
                )[0]

    cmds.setAttr(f"{node}.hiddenInOutliner", True)
    cmds.setAttr(f"{node}.isHistoricallyInteresting", 0)
    return node


def connect_same_attr(src: str, dest: str, attrs: list[str]) -> None:
    """
    同名のアトリビュート同士を接続する

    Args:
        src (str): 接続元のノード名
        dest (str): 接続先のノード名
        attrs (list[str]): 接続するアトリビュート名のリスト
            例: ["translate", "rotate", "scale", "visibility"]

    Returns:
        None
    """
    for attr in attrs:
        if attr == "translate":
            for axis in "XYZ":
                cmds.connectAttr(f"{src}.translate{axis}", f"{dest}.translate{axis}")

        elif attr == "rotate":
            for axis in "XYZ":
                cmds.connectAttr(f"{src}.rotate{axis}", f"{dest}.rotate{axis}")

        elif attr == "scale":
            for axis in "XYZ":
                cmds.connectAttr(f"{src}.scale{axis}", f"{dest}.scale{axis}")

        else:
            cmds.connectAttr(f"{src}.{attr}", f"{dest}.{attr}")


def connect_half_point(src1, src2, dest, src_attr1="translate", src_attr2="translate"):
    pb = create_node("pairBlend", name=f"PB_{dest}")
    cmds.setAttr(f"{pb}.weight", 0.5)
    cmds.connectAttr(f"{src1}.{src_attr1}", f"{pb}.inTranslate1")
    if src2:
        cmds.connectAttr(f"{src2}.{src_attr2}", f"{pb}.inTranslate2")
    cmds.connectAttr(f"{pb}.outTranslate", f"{dest}.translate")
    return pb


def connect_equal_point(nodes, offset=True):
    start_end = [nodes[0], nodes[-1]]
    if not offset:
        start_end = [nodes[-1]]

    pmas = [None] * len(start_end)
    for i, node in enumerate(start_end):
        name = f"Pma_{node}_{cmds.listRelatives(node, p=True)[0]}"
        if cmds.objExists(name):
            pmas[i] = name

        else:
            pmas[i] = create_node("plusMinusAverage", name=name)
            cmds.connectAttr(f"{node}.translate", f"{pmas[i]}.input3D[0]")
            cmds.connectAttr(f"{cmds.listRelatives(node, p=True)[0]}.translate", f"{pmas[i]}.input3D[1]")

    weight = 1 / (len(nodes) - 1)
    w = weight
    for node in nodes[1:-1]:
        p = cmds.listRelatives(node, p=True)[0]
        pb = create_node("pairBlend", name=f"Pb_{p}")
        cmds.setAttr(f"{pb}.weight", w)
        w += weight
        if offset:
            cmds.connectAttr(f"{pmas[0]}.output3D", f"{pb}.inTranslate1")
        
        cmds.connectAttr(f"{pmas[-1]}.output3D", f"{pb}.inTranslate2")
        cmds.connectAttr(f"{pb}.outTranslate", f"{p}.translate")


def connect_pair_blend(name: str="", weight: str|float=0.0, in_tl1: str="", in_tl2: str="", in_rt1: str="", in_rt2: str="", out_tl: str="", out_rt: str="") -> str:
    """
    pairBlendノードを作成、接続する
    各アトリビュートは "nodeName.attrName" の形で記述する
    in側のアトリビュートの最後に"!"をつけると、接続後すぐに切断し、アトリビュートに値だけ残す
    out側のアトリビュートを "nodeName.attrName:XYZ" のように記述すると、:後のXYZをアトリビュートに一文字ずつ追加してアトリビュートを全て接続する 例 nodeName.rotate:XYZ -> rotateX rotateY rotateZ

    Args:
        name (str): pairBlendノードの名前 規定は "Pb_" + out側のノード名
        weight (str | float): pairBlendノードのweight値 "nodeName.attrName"の形なら接続 数値なら値を設定する
        in_tl1 (str): inTranslate1に接続するアトリビュート
        in_tl2 (str): inTranslate2に接続するアトリビュート
        in_rt1 (str): inRotate1に接続するアトリビュート
        in_rt2 (str): inRotate2に接続するアトリビュート
        out_tl (str): outTranslateに接続するアトリビュート
        out_rt (str): outRotateに接続するアトリビュート

    Returns:
        str : pairBlendノード
    """
    if not name:
        if out_tl:
            name = f"Pb_{out_tl.split('.')[0]}"

        elif out_rt:
            name = f"Pb_{out_rt.split('.')[0]}"

        else:
            cmds.error("Unable to set name.")

    pb = create_node("pairBlend", name=name)
    cmds.setAttr(f"{pb}.rotInterpolation", 1)

    pb_tl1 = f"{pb}.inTranslate1"
    pb_tl2 = f"{pb}.inTranslate2"
    pb_rt1 = f"{pb}.inRotate1"
    pb_rt2 = f"{pb}.inRotate2"
    pb_out_tl = f"{pb}.outTranslate"
    pb_out_rt = f"{pb}.outRotate"

    for src, dest in zip([in_tl1, in_tl2, in_rt1, in_rt2, pb_out_tl, pb_out_rt], [pb_tl1, pb_tl2, pb_rt1, pb_rt2, out_tl, out_rt]):
        if src and dest:
            if ":" in dest:
                dest, axis =  dest.split(":")
                for axis1, axis2 in zip("XYZ", axis):
                    cmds.connectAttr(f"{src}{axis1}", f"{dest}{axis2}", f=True)

            elif "!" in src:
                src = src[:-1]
                cmds.connectAttr(src, dest, f=True)
                cmds.disconnectAttr(src, dest)

            else:
                cmds.connectAttr(src, dest, f=True)

    if isinstance(weight, str):
        cmds.connectAttr(weight, f"{pb}.weight")
    
    elif isinstance(weight, float) or isinstance(weight, int):
        cmds.setAttr(f"{pb}.weight", weight)

    else:
        cmds.error("Invalid value.")

    return pb


def connect_float_math(name: str="", operation: int=0, fa: str|float=0.0, fb: str|float=0.0, out: list[str]=[]) -> str:
    """
    floatMathノードを作成、接続する
    各アトリビュートは "nodeName.attrName" の形で記述する
    数値が入力されると値が設定される
    outは "nodeName.attrName" の文字列のリスト
    in側のアトリビュートの最後に"!"をつけると、接続後すぐに切断し、アトリビュートに値だけ残す
    out側のアトリビュートを "nodeName.attrName:XYZ" のように記述すると、:後のXYZをアトリビュートに一文字ずつ追加してアトリビュートを全て接続する 例 nodeName.rotate:XYZ -> rotateX rotateY rotateZ

    Args:
        name (str): floatMathノードの名前 規定は "Fm_" + out側のノード名
        operation (int): floatMath.operationの値を設定する
        fa (str | float): floatMath.floatAの値
        fb (str | float): floatMath.floatBの値
        out (list of str): floatMath.outFloatから接続するアトリビュートのリスト
    
    Returns:
        str : floatMathノード
    """
    if not name:
        name = f"Fm_{out[0].split('.')[0]}"

    fm = create_node("floatMath", name=name)
    cmds.setAttr(f"{fm}.operation", operation)

    fm_fa = f"{fm}.floatA"
    fm_fb = f"{fm}.floatB"
    fm_out = f"{fm}.outFloat"

    for src, dest in zip([fa, fb], [fm_fa, fm_fb]):
        if isinstance(src, str):
            if not src or not dest:
                continue

            if "!" in src:
                src = src[:-1]
                cmds.connectAttr(src, dest, f=True)
                cmds.disconnectAttr(src, dest)

            else:
                cmds.connectAttr(src, dest, f=True)

        elif isinstance(src, float) or isinstance(src, int):
            cmds.setAttr(dest, src)

        else:
            cmds.error("Invalid value.")

    for dest in out:
        if ":" in dest:
            d, axis = dest.split(":")
            for a in axis:
                cmds.connectAttr(fm_out, f"{d}{a}", f=True)

        else:
            cmds.connectAttr(fm_out, dest, f=True)

    return fm


def connect_multiply_divide(
        name: str="", operation: int=1, in1: str|list[float]="", in2: str|list[float]="",
        in1x: str|float="", in1y: str|float="", in1z: str|float="", in2x: str|float="", in2y: str|float="", in2z: str|float="",
        out: list[str]=[], outx: list[str]=[], outy: list[str]=[], outz: list[str]=[]
    ) -> str:
    """
    multiplyDivideノードを作成、接続する
    input側各アトリビュートは "nodeName.attrName" の形で記述する
    数値が入力されると値が設定される
    output側は "nodeName.attrName" の文字列のリスト
    in側のアトリビュートの最後に"!"をつけると、接続後すぐに切断し、アトリビュートに値だけ残す
    out側のアトリビュートを "nodeName.attrName:XYZ" のように記述すると、:後のXYZをアトリビュートに一文字ずつ追加してアトリビュートを全て接続する 例 nodeName.rotate:XYZ -> rotateX rotateY rotateZ

    Args:
        name (str): multiplyDivideノードの名前 規定は "Md_" + out側のノード名
        operation (int): multiplyDivide.operationの値を設定する
        in1 (str | list of float): multiplyDivide.input1
        in2 (str | list of float): multiplyDivide.input2
        in1x (str | float): multiplyDivide.input1X
        in1y (str | float): multiplyDivide.input1Y
        in1z (str | float): multiplyDivide.input1Z
        in2x (str | float): multiplyDivide.input2X
        in2y (str | float): multiplyDivide.input2Y
        in2z (str | float): multiplyDivide.input2Z
        out (list of str): multiplyDivide.outputから接続するアトリビュートのリスト
        outx (list of str): multiplyDivide.outputXから接続するアトリビュートのリスト
        outy (list of str): multiplyDivide.outputYから接続するアトリビュートのリスト
        outz (list of str): multiplyDivide.outputZから接続するアトリビュートのリスト

    Returns:
        str : multiplyDivideノード
    """
    if not name:
        for node in out + outx + outy + outz:
            name = f"Md_{node}"
            break

    md = create_node("multiplyDivide", name=name)
    cmds.setAttr(f"{md}.operation", operation)

    md_in1 = f"{md}.input1"
    md_in2 = f"{md}.input2"
    md_in1x = f"{md}.input1X"
    md_in1y = f"{md}.input1Y"
    md_in1z = f"{md}.input1Z"
    md_in2x = f"{md}.input2X"
    md_in2y = f"{md}.input2Y"
    md_in2z = f"{md}.input2Z"
    md_out = f"{md}.output"
    md_outx = f"{md}.outputX"
    md_outy = f"{md}.outputY"
    md_outz = f"{md}.outputZ"

    for src, dest in zip([in1, in2, in1x, in1y, in1z, in2x, in2y, in2z, md_out, md_outx, md_outy, md_outz], [md_in1, md_in2, md_in1x, md_in1y, md_in1z, md_in2x, md_in2y, md_in2z, out, outx, outy, outz]):
        if isinstance(src, str):
            if not src or not dest:
                continue

            if isinstance(dest, list):
                for d in dest:
                    if ":" in dest:
                        d, axis = d.split(":")
                        for a in axis:
                            cmds.connectAttr(src, f"{d}{a}", f=True)

                    else:
                        cmds.connectAttr(src, d, f=True)

            elif "!" in src:
                src = src[:-1]
                cmds.connectAttr(src, dest, f=True)
                cmds.disconnectAttr(src, dest)

            else:
                cmds.connectAttr(src, dest, f=True)

        elif isinstance(src, float) or isinstance(src, int):
            cmds.setAttr(dest, src)

        elif isinstance(src, list):
            cmds.setAttr(dest, *src)

        else:
            cmds.error("Invalid value.")

    return md


def connect_condition(
        name: str="", operation: int=0, ft: str|float="", st: str|float="", false: str|list[float]="", true: str|list[float]="",
        fr: str|float="", fg: str|float="", fb: str|float="", tr: str|float="", tg: str|float="", tb: str|float="", out: list[str]=[], outr: list[str]=[], outg: list[str]=[], outb: list[str]=[]
    ) -> str:
    """
    conditionノードを作成、接続する
    input側各アトリビュートは "nodeName.attrName" の形で記述する
    数値が入力されると値が設定される
    output側は "nodeName.attrName" の文字列のリスト
    in側のアトリビュートの最後に"!"をつけると、接続後すぐに切断し、アトリビュートに値だけ残す
    out側のアトリビュートを "nodeName.attrName:XYZ" のように記述すると、:後のXYZをアトリビュートに一文字ずつ追加してアトリビュートを全て接続する 例 nodeName.rotate:XYZ -> rotateX rotateY rotateZ

    Args:
        name (str): conditionノードの名前 規定は Cd_" + out側のノード名
        operation (int): condition.operationの値を設定する
        ft (str | float): condition.firstTerm
        st (str | float): condition.secondTerm
        false (str | list of float): condition.colorIfFalse
        true (str | list of float): condition.colorIfTrue
        fr (str | float): condition.colorIfFalseR
        fg (str | float): condition.colorIfFalseG
        fb (str | float): condition.colorIfFalseB
        tr (str | float): condition.colorIfTrueR
        tg (str | float): condition.colorIfTrueG
        tb (str | float): condition.colorIfTrueB
        out (list of str): condition.outColorから接続するアトリビュートのリスト
        outx (list of str): condition.outColorRから接続するアトリビュートのリスト
        outy (list of str): condition.outColorGから接続するアトリビュートのリスト
        outz (list of str): condition.outColorBから接続するアトリビュートのリスト

    Returns:
        str : conditionノード
    """

    if not name:
        for node in out + outr + outg + outb:
            name = f"Cd_{node}"
            break

    cd = create_node("condition", name=name)
    cmds.setAttr(f"{cd}.operation", operation)

    srcs = [
        ft, st, false, true,
        fr, fg, fb, tr, tg, tb, f"{cd}.outColor", f"{cd}.outColorR", f"{cd}.outColorG", f"{cd}.outColorB"
        ]

    dests = [
        f"{cd}.firstTerm", f"{cd}.secondTerm", f"{cd}.colorIfFalse", f"{cd}.colorIfTrue",
        f"{cd}.colorIfFalseR", f"{cd}.colorIfFalseG", f"{cd}.colorIfFalseB", f"{cd}.colorIfTrueR", f"{cd}.colorIfTrueG", f"{cd}.colorIfTrueB", out, outr, outg, outb
        ]

    for src, dest, in zip(srcs, dests):
        if isinstance(src, str):
            if not src or not dest:
                continue

            if isinstance(dest, list):
                for d in dest:
                    if ":" in dest:
                        d, axis = d.split(":")
                        for a in axis:
                            cmds.connectAttr(src, f"{d}{a}", f=True)

                    else:
                        cmds.connectAttr(src, d, f=True)

            elif "!" in src:
                src = src[:-1]
                cmds.connectAttr(src, dest, f=True)
                cmds.disconnectAttr(src, dest)

            else:
                cmds.connectAttr(src, dest, f=True)

        elif isinstance(src, float) or isinstance(src, int):
            cmds.setAttr(dest, src)

        elif isinstance(src, list):
            cmds.setAttr(dest, *src)

        else:
            cmds.error("Invalid value.")

    return cd


def connect_compose_matrix(
        name: str="", euler: bool=True, order: int=0,
        quat: str|list[float]="", qx: str|float="", qy: str|float="", qz: str|float="", qw: str|float="",
        tl: str|list[float]="", tx: str|float="", ty: str|float="", tz: str|float="",
        rt: str|list[float]="", rx: str|float="", ry: str|float="", rz: str|float="",
        sc: str|list[float]="", scx: str|float="", scy: str|float="", scz: str|float="",
        sh: str|list[float]="", shx: str|float="", shy: str|float="", shz: str|float="", out: list[str]=[]):
    """
    composeMatrixノードを作成、接続する
    input側各アトリビュートは "nodeName.attrName" の形で記述する
    数値が入力されると値が設定される
    output側は "nodeName.attrName" の文字列のリスト
    in側のアトリビュートの最後に"!"をつけると、接続後すぐに切断し、アトリビュートに値だけ残す

    Args:
        name (str): composeMatrixノードの名前 規定は Cm_" + out側のノード名
        euler (bool): composeMatrix.useEulerRotationの値を設定する
        order (int): composeMatrix.inputRotateOrderの値を設定する
        quat (str | list of float): condcomposeMatrixition.inputQuat
        qx (str | float): composeMatrix.inputQuatX
        qy (str | float): composeMatrix.inputQuatY
        qz (str | float): composeMatrix.inputQuatZ
        qw (str | float): composeMatrix.inputQuatW
        tl (str | list of float): composeMatrix.inputTranslate
        tx (str | float): composeMatrix.inputTranslateX
        ty (str | float): composeMatrix.inputTranslateY
        tz (str | float): composeMatrix.inputTranslateZ
        rt (str | list of float): concomposeMatrixdition.inputRotate
        rx (str | float): composeMatrix.inputRotateX
        ry (str | float): composeMatrix.inputRotateY
        rz (str | float): composeMatrix.inputRotateZ
        sc (str | list of float): composeMatrix.inputScale
        scx (str | float): composeMatrix.inputScaleX
        scy (str | float): composeMatrix.inputScaleY
        scz (str | float): composeMatrix.inputScaleZ
        sh (str | list of float): composeMatrix.inputShear
        shx (str | float): composeMatrix.inputShearX
        shy (str | float): composeMatrix.inputShearY
        shz (str | float): composeMatrix.inputShearZ
        out (list of str): composeMatrix.outputMatrixから接続するアトリビュートのリスト

    Returns:
        str : composeMatrix
    """

    if not name:
        for node in out:
            name = f"Cd_{node}"
            break

    cm = create_node("composeMatrix", name=name)
    cmds.setAttr(f"{cm}.useEulerRotation", euler)
    cmds.setAttr(f"{cm}.inputRotateOrder", order)

    srcs = [
        quat, qx, qy, qz, qw,
        tl, tx, ty, tz,
        rt, rx, ry, rz,
        sc, scx, scy, scz,
        sh, shx, shy, shz, f"{cm}.outputMatrix"
        ]

    dests = [
        f"{cm}.inputQuat", f"{cm}.inputQuatX", f"{cm}.inputQuatY", f"{cm}.inputQuatZ", f"{cm}.inputQuatW",
        f"{cm}.inputTranslate", f"{cm}.inputTranslateX", f"{cm}.inputTranslateY", f"{cm}.inputTranslateZ",
        f"{cm}.inputRotate", f"{cm}.inputRotateX", f"{cm}.inputRotateY", f"{cm}.inputRotateZ",
        f"{cm}.inputScale", f"{cm}.inputScaleX", f"{cm}.inputScaleY", f"{cm}.inputScaleZ",
        f"{cm}.inputShear", f"{cm}.inputShearX", f"{cm}.inputShearY", f"{cm}.inputShearZ", out
    ]

    for src, dest, in zip(srcs, dests):
        if isinstance(src, str):
            if not src or not dest:
                continue

            if isinstance(dest, list):
                for d in dest:
                    cmds.connectAttr(src, d, f=True)

            elif "!" in src:
                src = src[:-1]
                cmds.connectAttr(src, dest, f=True)
                cmds.disconnectAttr(src, dest)

            else:
                cmds.connectAttr(src, dest, f=True)

        elif isinstance(src, float) or isinstance(src, int):
            cmds.setAttr(dest, src)

        elif isinstance(src, list):
            cmds.setAttr(dest, *src)

        else:
            cmds.error("Invalid value.")

    return cm


def connect_switch_attr(dest_attr: str, true_attrs: list, false_attrs: list) -> None:
    """
    boolや01で表されるアトリビュートとboolアトリビュートを接続する

    Args:
        dest_attr (str): 接続元のアトリビュート名 "ノード名.アトリビュート名"
        true_attrs (list or tuple): 接続元アトリビュートがTrueだった場合にTrueに設定されるアトリビュートのリスト ["ノード名.アトリビュート名"]
        false_attrs (list or tuple): 接続元アトリビュートがFalseだった場合にTrueに設定されるアトリビュートのリスト ["ノード名.アトリビュート名"]

    Returns:
        None
    """
    dest = dest_attr.split(".")[0]
    if false_attrs:
        rev = create_node("reverse", name=f"Rev_{dest}")
        cmds.connectAttr(dest_attr, f"{rev}.inputX")
        rev_attr = f"{rev}.outputX"

    for attr in true_attrs:
        cmds.connectAttr(dest_attr, attr)

    for attr in false_attrs:
        cmds.connectAttr(rev_attr, attr)


def lock_attr(input, unlock=False):
    def lock(node, attr):
        if unlock:
            cmds.setAttr(f"{node}.{attr}", l=False)
            cmds.setAttr(f"{node}.{attr}", cb=True, k=True)
        else:
            cmds.setAttr(f"{node}.{attr}", cb=False, k=False, l=True)

    for node, attrs in zip(input[::2], input[1::2]):
        for attr in attrs:
            if attr == "translate":
                for axis in "XYZ":
                    lock(node, f"translate{axis}")
                    continue

            if attr == "rotate":
                for axis in "XYZ":
                    lock(node, f"rotate{axis}")
                    continue

            if attr == "scale":
                for axis in "XYZ":
                    lock(node, f"scale{axis}")
                    continue

            lock(node, attr)


def mirror_space(node: str, axis: str="X") -> list[list[float]]:
    """
        オブジェクトをワールド空間上で反転する
        シェイプにベイクはされずにアトリビュートに値が残る

    Args:
        node (str): 反転するノード
        axis (str): 反転する軸 既定値は"X" 有効な値は "X", "Y", "Z"

    Returns:
        list : 反転後のtransform情報 [[tx, ty, tz], [rx, ry, rz], [sx, sy, sz]]
    """

    parent = cmds.listRelatives(node, p=True)
    tmp_space = cmds.createNode("transform")

    cmds.parent(node, tmp_space)
    cmds.setAttr(f"{tmp_space}.scale{axis}", -1)
    if parent:
        cmds.parent(node, parent[0])

    else:
        cmds.parent(node, w=True)

    cmds.delete(tmp_space)
    matrix = cmds.getAttr(f"{node}.matrix")
    return decompose_matrix(matrix)


def meta_node_apply_settings(G, data):
    if "LineWidth" in data:
        meta_data = {}
        meta_data["CtrlsMatrix"] = list_to_tuple(data["CtrlsMatrix"])
        meta_data["LineWidth"] = data["LineWidth"]
        dict_to_attr(G.meta_node, meta_data)

    pos, rot, scl = decompose_matrix(data["GroupMatrix"])
    cmds.setAttr(f"{G.grp}.translate", *pos)
    cmds.setAttr(f"{G.grp}.rotate", *rot)
    cmds.setAttr(f"{G.grp}.scale", l=False)
    [cmds.setAttr(f"{G.grp}.scale{axis}", l=False) for axis in "XYZ"]
    cmds.setAttr(f"{G.grp}.scale", *scl, l=True)


def set_vtx_average_point(guide: str) -> list[float]:
    """
    選択しているvertexの平均座標を取得します。

    Args:
        guide (str): 配置するガイド

    Returns:
        lsit (float) : 平均座標値(xyz)
    """

    vtx_list = cmds.ls(sl=True, fl=True)

    if not vtx_list:
        return

    if not "vtx[" in vtx_list[0]:
        return

    pos = [cmds.pointPosition(vtx, w=True) for vtx in vtx_list]
    pos = [sum(p) / len(p) for p in zip(*pos)]

    cmds.move(*pos, guide, ws=True)