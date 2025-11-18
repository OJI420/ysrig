import os
from ysrig import gui_base

if int(gui_base.ver) <= 2024:
    from PySide2 import QtWidgets, QtCore

elif int(gui_base.ver) >= 2025:
    from PySide6 import QtWidgets, QtCore


class YSHelpWindow(QtWidgets.QWidget):
    """
    ヘルプ用のmdファイルを読み込んで表示するウィンドウ
    """
    def __init__(self):
        super().__init__(gui_base.maya_main_window)
        self.setup()                  # 変数宣言
        self.pre_close()              # すでに同じGUIが存在する場合、事前に閉じておく
        self.window()                 # windowの設定
        self.gui()
        self.load()                   # mdを読み込んで表示

    def setup(self):
        self.dir_path = os.path.dirname(__file__)
        self.md_path = os.path.join(self.dir_path, "HELP.md")
        self.main_layout = None
        self.browser = None

    def pre_close(self):
        for widget in QtWidgets.QApplication.allWidgets():
            if widget.objectName() == "YSRig_Help_Gui":
                widget.close()
                widget.deleteLater()

    def window(self):
        self.setWindowTitle("YSRig - Help")
        self.setObjectName("YSRig_Help_Gui")
        self.setWindowFlags(QtCore.Qt.Window)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(500)
        self.setStyleSheet(f"background-color: rgb({gui_base.WINDOW_COLOR_2});")

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

    def gui(self):
        self.browser = QtWidgets.QTextBrowser()
        self.main_layout.addWidget(self.browser)

    def load(self):
        with open(self.md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        html = gui_base.simple_md_to_html(md_text)
        self.browser.setHtml(html)


def main():
    G = YSHelpWindow()
    G.show()