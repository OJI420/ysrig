import os
import json
import inspect
import importlib
from maya import cmds
from ysrig import gui_base, core
importlib.reload(gui_base)


if int(gui_base.ver) <= 2024:
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtWidgets import QAction
    from shiboken2 import wrapInstance

elif int(gui_base.ver) >= 2025:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtGui import QAction
    from shiboken6 import wrapInstance

ysrig_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
json_path = os.path.abspath(os.path.join(ysrig_path, "prefs", "ysrig", "button_shape.json"))

class Gui(QtWidgets.QWidget):
    def __init__(self):
        super().__init__(gui_base.maya_main_window)
        # -変数宣言-
        self.TITLE = "PickerEditor"

        self.pre_close()
        self.window()
        self.back_ground()

    def pre_close(self):
        for widget in QtWidgets.QApplication.allWidgets():
            if widget.objectName() == f"YS_{self.TITLE}_Gui":
                widget.close()
                widget.deleteLater()

    def window(self):
        self.setWindowTitle(self.TITLE)
        self.setObjectName(f"YS_{self.TITLE}_Gui")
        self.setWindowFlags(QtCore.Qt.Window)
        self.setFixedSize(1500, 1000)

        self.main_layout = QtWidgets.QGridLayout(self)

    def back_ground(self):
        bg1 = QtWidgets.QWidget()
        bg2 = QtWidgets.QWidget()
        bg2.setStyleSheet(f"background-color: rgb({gui_base.WINDOW_COLOR_1});")

        self.main_layout.addWidget(bg1, 0, 0, 10, 10)
        self.main_layout.addWidget(bg2, 0, 10, 10, 5)


def main():
    G = Gui()
    G.show()


def load_shape() -> dict:
    with open(json_path, "r") as f:
        ld = json.load(f)

    return ld


class PickerModule:
    def __init__(self, meta_node):
        self.meta_node = meta_node
        self.module = ""
        self.name = meta_node.replace("Meta_", "")
        self.buttons = []
        self.translate = [0, 0]
        self.rotate = [0, 0]
        self.scale = [1, 1]

        self.get_module()
        self.set_info()

    def get_module(self):
        file_path = inspect.getfile(self.__class__)  # クラスのあるファイルパス
        dir_path = os.path.dirname(file_path)        # 親ディレクトリのパス
        self.module = os.path.basename(dir_path)     # 親ディレクトリの名前

    def set_button(self):
        pass


class PickerCanvas:
    def __init__():
        #meta_nodes = core.get_meta_nodes()
        #meta_nodes += core.get_facial_meta_nodes()
        meta_nodes = ["Meta_Spine"]

        modules = [None] * len(meta_nodes)

        for i, meta in enumerate(meta_nodes):
            module = cmds.getAttr(f"{meta}.Module")
            module = importlib.import_module(f"ysrig.modules.{module}.picker")
            klass = getattr(module, "PickerModule")
            modules[i] = klass(meta)