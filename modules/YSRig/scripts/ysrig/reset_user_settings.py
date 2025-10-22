import os
import winsound
from maya import cmds, mel

def get_prefs_dir() -> str:
    current_dir = os.path.dirname(__file__)
    ysrig_dir = os.path.abspath(os.path.join(current_dir, "../../"))
    pref_dir = os.path.abspath(os.path.join(ysrig_dir, "prefs/ysrig/"))

    return pref_dir


def main():
    winsound.MessageBeep()
    result = cmds.confirmDialog(
        title="reset settings",
        message="ユーザー設定をリセットしますか？",
        button=["OK", "Cancel"],
        defaultButton="OK",
        cancelButton="Cancel",
        dismissString="Cancel"
    )

    if result == "Cancel":
        return

    pref_dir = get_prefs_dir()
    mod_dir = os.path.abspath(os.path.join(pref_dir, "modules/"))
    modules = [name for name in os.listdir(mod_dir) if os.path.isdir(os.path.join(mod_dir, name))]

    for mod in modules:
        path = os.path.abspath(os.path.join(mod_dir, f"{mod}/settings/"))
        jsons = os.listdir(path)
        for j in jsons:
            if j == "default.json":
                continue

            json_path = os.path.abspath(os.path.join(path, j))
            os.remove(json_path)

    cmds.confirmDialog(
        title="reset settings",
        message="ユーザー設定をリセットしました",
        button=["OK"],
        defaultButton="OK"
    )