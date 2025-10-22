import os
import json
from maya import cmds
from ysrig import core


def get_prefs_dir() -> str:
    current_dir = os.path.dirname(__file__)
    ysrig_dir = os.path.abspath(os.path.join(current_dir, "../../"))
    pref_dir = os.path.abspath(os.path.join(ysrig_dir, "prefs/ysrig/"))

    return pref_dir


def get_settings(dir) -> dict:
    settings = {}
    jsons = os.listdir(dir)
    for j in jsons:
        if j == "default.json":
            continue

        path = os.path.abspath(os.path.join(dir, j))
        with open(path, 'r') as f:
            settings[j.replace(".json", "")] = json.load(f)

    return settings


def export(file_path):
    data = {}
    pref_dir = get_prefs_dir()
    mod_dir = os.path.abspath(os.path.join(pref_dir, "modules/"))
    modules = [name for name in os.listdir(mod_dir) if os.path.isdir(os.path.join(mod_dir, name))]
    data["YSRigUserSettingsJSON"] = True
    data["YSRigVersion"] = core.VERSION

    for mod in modules:
        path = os.path.abspath(os.path.join(mod_dir, f"{mod}/settings/"))
        data[mod] = get_settings(path)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def main():
    file_path = cmds.fileDialog2(
        fileMode=0,
        caption="save user settings as json",
        okCaption="Save",
        fileFilter="JSON Files (*.json)"
    )

    if not file_path:
        return

    file_path = file_path[0]

    if not file_path.endswith(".json"):
        file_path += ".json"

    export(file_path)

    cmds.inViewMessage(
        amg="<hl>Export successful !</hl>",
        pos="midCenter",             # 表示位置
        fade=True,                   # フェードアウトする
        fadeStayTime=2000,           # 表示時間 (ミリ秒)
        dragKill=True                # ドラッグで消せる
    )
