import os
import winsound
import subprocess
from maya import cmds
from ysrig import gui_base

if int(gui_base.ver) <= 2024:
    from PySide2 import QtWidgets, QtCore
    IS_PYSIDE6 = False
elif int(gui_base.ver) >= 2025:
    from PySide6 import QtWidgets, QtCore
    IS_PYSIDE6 = True

def main():
    winsound.MessageBeep()
    result = cmds.confirmDialog(
        title="reset settings",
        message="YSRig ウィンドウのレイアウトをリセットしますか？",
        button=["OK", "Cancel"],
        defaultButton="OK",
        cancelButton="Cancel",
        dismissString="Cancel"
    )

    if result == "Cancel":
        return

    for widget in QtWidgets.QApplication.allWidgets():
        if hasattr(widget, "ysrig_window"):
            widget.close()
            widget.deleteLater()

    org_name = "YSRigSystem"
    settings = QtCore.QSettings(org_name, "dummy")
    path = settings.fileName()

    if os.path.exists(path) and os.path.isfile(path):
        if path.endswith(".ini") or path.endswith(".conf"):
            try:
                os.remove(path)
            except Exception as e:
                pass

    reg_path = f"HKCU\\Software\\{org_name}"
    
    command = f'reg delete "{reg_path}" /f'

    try:
        # subprocessを使ってWindowsのコマンドプロンプト経由で削除
        subprocess.run(command, shell=True, capture_output=True, text=True)
    except Exception as e:
        pass