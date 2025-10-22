import os
import json
import importlib
from maya import cmds
from maya.api.OpenMaya import MGlobal
from ysrig import core


def main():
    if cmds.objExists(core.get_guide_group()):
        MGlobal.displayError("すでにガイドが存在します")
        return

    file_path = cmds.fileDialog2(
        fileMode=1,
        caption="load json",
        fileFilter="JSON Files (*.json)"
    )

    if not file_path:
        return

    file_path = file_path[0]
    
    with open(file_path, 'r') as f:
        data: dict = json.load(f)

    modules = list(data.keys())
    ysrig = modules[0]
    ver = data[modules[1]]
    build_type = "FromJSON"
    file_name = os.path.basename(file_path)
    facial_root = data[modules[-1]]
    modules = modules[2:-1]

    if not ysrig == "YSRigMetaDataJSON":
        MGlobal.displayError("データの形式が間違っています")
        return

    for mod in modules:
        module = data[mod]["Module"]
        module = importlib.import_module(f"ysrig.modules.{module}.guide")
        func = getattr(module, "build")
        func(data[mod])

    attrs = [
        [f"{core.get_root_group()}.YSRigVersion", ver],
        [f"{core.get_root_group()}.BuildType", build_type],
        [f"{core.get_root_group()}.SourceFileName", file_name],
        [f"{core.get_guide_facials_group()}.FacialRootName", facial_root]
    ]

    for attr in attrs:
        cmds.setAttr(attr[0], l=False)
        if attr[1]:
            cmds.setAttr(*attr, l=True, type="string")