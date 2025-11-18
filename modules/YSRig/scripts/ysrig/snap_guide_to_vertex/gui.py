import os
import inspect
import importlib
from maya import cmds
from ysrig import gui_base, core
importlib.reload(gui_base)
importlib.reload(core)

if int(gui_base.ver) <= 2024:
    from PySide2 import QtWidgets, QtCore

elif int(gui_base.ver) >= 2025:
    from PySide6 import QtWidgets, QtCore


class Gui(QtWidgets.QWidget):
    def __init__(self):
        super().__init__(gui_base.maya_main_window)
        self._setup()
        self._get_module_name()
        self.pre_close()
        self.window()
        self.add_help()
        self.gui()
        self.add_widget()

    def _setup(self):
        self.module_name = ""
        self.title = "Snap Guide To Vertex"
        self.file_path = ""
        self.dir_path = ""
        self.help_window = None
        self.pre_widget = {}
        self.widget = {}

    def _get_module_name(self):
        self.file_path = inspect.getfile(self.__class__)  # クラスのあるファイルパス
        self.dir_path = os.path.dirname(self.file_path)   # 親ディレクトリのパス
        module_name = os.path.basename(self.dir_path)     # 親ディレクトリの名前
        self.module_name = module_name

    def pre_close(self):
        for widget in QtWidgets.QApplication.allWidgets():
            if widget.objectName() == f"YS_{self.module_name}_Gui":
                widget.close()
                widget.deleteLater()

    def window(self):
        self.setWindowTitle(self.title)
        self.setObjectName(f"YS_{self.module_name}_Gui")
        self.setWindowFlags(QtCore.Qt.Window)
        self.setMinimumWidth(500)
        self.setStyleSheet(f"background-color: rgb({gui_base.WINDOW_COLOR_1});")

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(3)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

    def add_help(self):
        sub_layout = QtWidgets.QGridLayout()

        self.pre_widget["Help"] = gui_base.YSPushButton("Help")
        self.pre_widget["Help"].setStyleSheet(f"background-color: rgb({gui_base.BACK_COLOR_1}); color: rgb({gui_base.STR_COLOR_1});")
        self.pre_widget["Help"].setFixedHeight(25)
        self.pre_widget["Help"].clicked.connect(self.help)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        sub_layout.addWidget(self.pre_widget["Help"], 0, 0, 1, 1)
        sub_layout.addItem(spacer, 0, 1, 1, 10)

        self.main_layout.addLayout(sub_layout)

    def help(self):
        self.help_window = gui_base.YSHelpWindow(self)
        self.help_window.show()

    def gui(self):
        self.widget["TargetGuide"] = gui_base.YSSelecterBox(label="★ Guide", placeholder_text="Guide Name")
        self.widget["Button"] = gui_base.YSPushButton("Set")
        self.widget["Button"].clicked.connect(self.call)

    def add_widget(self):
        for w in self.widget:
            self.main_layout.addWidget(self.widget[w])

    def closeEvent(self, event):
        super().closeEvent(event)
        if self.help_window:
            self.help_window.close()

    def call(self):
        node = self.widget["TargetGuide"].get()
        if not cmds.objExists(node):
            return

        core.set_vtx_average_point(node)


def main():
    G = Gui()
    G.show()