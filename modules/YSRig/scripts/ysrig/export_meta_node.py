import os
import json
from maya import cmds
from maya.api.OpenMaya import MGlobal
from ysrig import core


def get_meta_data():
    modules = {}
    meta_nodes = core.get_meta_nodes() + core.get_facial_meta_nodes()

    modules["YSRigMetaDataJSON"] = True
    modules["YSRigVersion"] = core.VERSION

    for meta_node in meta_nodes:
        data = {}
        attrs = cmds.listAttr(meta_node, ud=True)

        for attr in attrs:
            if attr == "YSNodeLabel":
                continue

            if cmds.attributeQuery(attr, node=meta_node, multi=True):
                data[attr] = core.get_list_attributes(meta_node, attr)

            else:
                data[attr] = cmds.getAttr(f"{meta_node}.{attr}")

        modules[meta_node] = data

    modules["FacialRootName"] = cmds.getAttr(f"{core.get_guide_facials_group()}.FacialRootName")

    return modules


def main():
    if not cmds.objExists(core.get_guide_group()):
        MGlobal.displayError("ガイドが見つかりませんでした")
        return

    file_path = cmds.fileDialog2(
        fileMode=0,
        caption="save meta data as json",
        okCaption="Save",
        fileFilter="JSON Files (*.json)"
    )

    if not file_path:
        return

    file_path = file_path[0]
    
    if not file_path.endswith(".json"):
        file_path += ".json"

    data = get_meta_data()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    cmds.inViewMessage(
        amg="<hl>Export successful !</hl>",
        pos="midCenter",             # 表示位置
        fade=True,                   # フェードアウトする
        fadeStayTime=2000,           # 表示時間 (ミリ秒)
        dragKill=True                # ドラッグで消せる
    )