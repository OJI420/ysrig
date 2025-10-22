import os
import json
from maya import cmds
from maya.api.OpenMaya import MGlobal


def get_prefs_dir() -> str:
    current_dir = os.path.dirname(__file__)
    ysrig_dir = os.path.abspath(os.path.join(current_dir, "../../"))
    pref_dir = os.path.abspath(os.path.join(ysrig_dir, "prefs/ysrig/"))

    return pref_dir


def import_(data, modules):
    pref_dir = get_prefs_dir()
    mod_dir = os.path.abspath(os.path.join(pref_dir, "modules/"))

    for mod in modules:
        path = os.path.abspath(os.path.join(mod_dir, f"{mod}/settings/"))
        if not os.path.isdir(path):
            continue

        for setting in data[mod]:
            json_path = os.path.abspath(os.path.join(mod_dir, f"{path}/{setting}.json"))
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data[mod][setting], f, indent=4)


def main():
    file_path = cmds.fileDialog2(
        fileMode=1,
        caption="load settings",
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
    modules = modules[2:]

    if not ysrig == "YSRigUserSettingsJSON":
        MGlobal.displayError("データの形式が間違っています")
        return

    import_(data, modules)

    cmds.inViewMessage(
        amg="<hl>Impoer successful !</hl>",
        pos="midCenter",             # 表示位置
        fade=True,                   # フェードアウトする
        fadeStayTime=2000,           # 表示時間 (ミリ秒)
        dragKill=True                # ドラッグで消せる
    )
