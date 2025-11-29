import os
import json
import inspect
import importlib
import winsound
import re
from maya import cmds, OpenMayaUI
from maya.api.OpenMaya import MGlobal
from ysrig import core
importlib.reload(core)


ver = cmds.about(v=True) # mayaのバージョン


if int(ver) <= 2024:
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtWidgets import QAction
    from shiboken2 import wrapInstance

    validator_1 = QtGui.QRegExpValidator(QtCore.QRegExp("[A-Za-z0-9_]+"))
    validator_2 = QtGui.QRegExpValidator(QtCore.QRegExp("[a-z0-9_]+"))

elif int(ver) >= 2025:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtGui import QAction
    from shiboken6 import wrapInstance

    validator_1 = QtGui.QRegularExpressionValidator(QtCore.QRegularExpression("^[A-Za-z0-9_]+$"))
    validator_2 = QtGui.QRegularExpressionValidator(QtCore.QRegularExpression("^[a-z0-9_]+$"))

# validator_1 : lineEditが受け付けない文字を指定 ここでは英数字と_(アンダースコア)以外は弾く
# validator_2 : 上記に追加で、大文字も弾く

# グローバル変数
this_file = os.path.abspath(__file__)                                                       # このファイルのパス
prefs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "prefs"))  # prefsディレクトリのパス
maya_main_window = wrapInstance(int(OpenMayaUI.MQtUtil.mainWindow()), QtWidgets.QWidget)    # mayaのメインウィンドウ


# GUI上の色リスト(RGB, 0-255)
WINDOW_COLOR_1 = "80, 90, 85"
WINDOW_COLOR_2 = "60, 90, 110"
WINDOW_COLOR_3 = "255, 255, 255"
BACK_COLOR_1 = "60, 70, 65"
BACK_COLOR_2 = "180, 180, 180"
BUTTON_COLOR_1 = "40, 50, 45"
BUTTON_COLOR_2 = "30, 60, 80"
BUTTON_COLOR_3 = "200, 200, 200"
STR_COLOR_1 = "230, 215, 215"
STR_COLOR_2 = "170, 170, 175"
STR_COLOR_3 = "10, 0, 0"
ERROR_COLOR = "255, 0, 0"


class GuiBase(QtWidgets.QWidget):
    """
    ガイド作成用のGUIベースクラス
    """
    def __init__(self):
        super().__init__(maya_main_window)
        self._setup()                 # 変数宣言
        self.setup()
        self._get_module_name()       # モジュールの名前をファイル名から取得
        self._get_title()             # モジュールの名前からウィンドウのタイトルを決定
        self.get_json_path()          # jsonのパスを、継承先のpyファイルのパスから決定
        self.pre_close()              # すでに同じGUIが存在する場合、事前に閉じておく
        self.window()                 # windowの設定
        self.add_help()               # ヘルプボタン追加
        self.add_preset_box()         # プリセットの呼び出しや保存をするウィジェットを追加
        self.add_parent_list()        # モジュールの親ジョイントを指定するためのウィジェットを追加
        self.gui()                    # 継承先でモジュールに必要なウィジェットを self.widget に追加
        self.add_widget()             # self.widget に追加したウィジェットをwindowに取り付ける
        self.add_create_button()      # ガイドを作成するボタンを追加
        self.load_selected_preset()   # 最後に呼び出していたプリセットを呼び出す

        self._app = QtWidgets.QApplication.instance()
        self._app.aboutToQuit.connect(self.save_window_settings_registry)
        self.load_window_settings_registry()

    def _setup(self):
        self.ysrig_window = True
        self.module_name = ""
        self.title = ""
        self.file_path = ""
        self.dir_path = ""
        self.json_path = ""
        self.txt_path = ""
        self.main_layout = None
        self.widget = {}
        self.pre_widget = {}
        self.help_window = None
        self.klass = None

    def setup(self):
        pass

    def _get_module_name(self):
        self.file_path = inspect.getfile(self.__class__)  # クラスのあるファイルパス
        self.dir_path = os.path.dirname(self.file_path)   # 親ディレクトリのパス
        module_name = os.path.basename(self.dir_path)     # 親ディレクトリの名前
        self.module_name = module_name
        self.klass = getattr(importlib.import_module(f"ysrig.modules.{self.module_name}.guide"), "Guide")

    def _get_title(self):
        title = ""
        for i, s in enumerate(self.module_name):
            if not i:
                title += s.upper()
                continue

            if s == "_":
                title += " "
                continue

            if self.module_name[i - 1] == "_":
                a = self.module_name[i:i+4]
                if not a == "and_":
                    title += s.upper()
                    continue

            title += s

        self.title = title

    def get_json_path(self):
        self.json_path = os.path.join(prefs_path, "ysrig", "modules", self.module_name, "settings")
        self.txt_path = os.path.join(prefs_path, "ysrig", "modules", self.module_name, "__preset__.txt")

    def pre_close(self):
        for widget in QtWidgets.QApplication.allWidgets():
            if widget.objectName() == f"YS_{self.module_name}_Gui":
                widget.close()
                widget.deleteLater()

    def window(self):
        self.setWindowTitle(self.title)
        self.setObjectName(f"YS_{self.module_name}_Gui")
        self.setWindowFlags(QtCore.Qt.Window)
        self.setMinimumWidth(600)
        self.setStyleSheet(f"background-color: rgb({WINDOW_COLOR_1});")

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

    def add_help(self):
        sub_layout = QtWidgets.QGridLayout()

        self.pre_widget["Help"] = YSPushButton("Help")
        self.pre_widget["Help"].setStyleSheet(f"background-color: rgb({BACK_COLOR_1}); color: rgb({STR_COLOR_1});")
        self.pre_widget["Help"].setFixedHeight(25)
        self.pre_widget["Help"].clicked.connect(self.help)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        sub_layout.addWidget(self.pre_widget["Help"], 0, 0, 1, 1)
        sub_layout.addItem(spacer, 0, 1, 1, 10)

        self.main_layout.addLayout(sub_layout)

    def add_preset_box(self):
        frame = YSFrame()
        self.pre_widget["Preset"] = YSPresetBox(self)
        self.main_layout.addWidget(frame)
        self.main_layout.addWidget(self.pre_widget["Preset"])

    def add_parent_list(self):
        frame = YSFrame("Parent")
        self.pre_widget["Parent"] = YSParentList(self, label="◆ Parent Name", placeholder_text="None")
        self.main_layout.addWidget(frame)
        self.main_layout.addWidget(self.pre_widget["Parent"])

    def gui(self):
        pass

    def add_widget(self):
        for w in self.widget:
            self.main_layout.addWidget(self.widget[w])

        self.pre_widget["Preset"].connect_checker()

    def add_create_button(self):
        self.pre_widget["Create"] = YSPushButton("Create")
        self.pre_widget["Create"].clicked.connect(self._call)
        self.main_layout.addWidget(self.pre_widget["Create"])

    def _call(self):
        error = False
        for w in self.widget:
            if isinstance(self.widget[w], YSLineEdit): # 空NGのLineEditが空だった場合
                if not self.widget[w].is_required:
                    continue

                if not self.widget[w].get():
                    self.widget[w].error()
                    error = True

        if error:
            MGlobal.displayError(f"必須項目に空欄があります")

        else:
            self.call()

    def call(self):
        pass

    def save_selected_preset(self):
        current_preset = self.pre_widget["Preset"].get_current_text()
        with open(self.txt_path, "w") as f:
            f.write(current_preset)

    def load_selected_preset(self):
        self.pre_widget["Preset"].load_preset()
        with open(self.txt_path, "r") as f:
            preset_name = f.read().strip()

        self.pre_widget["Preset"].set_current_text(preset_name)

    def help(self):
        self.help_window = YSHelpWindow(self)
        self.help_window.show()

    def save_window_settings_registry(self):
        """レジストリにウィンドウ状態を保存"""
        settings = QtCore.QSettings("YSRigSystem", self.objectName())
        settings.setValue("geometry", self.saveGeometry())

    def load_window_settings_registry(self):
        """レジストリからウィンドウ状態を復元"""
        settings = QtCore.QSettings("YSRigSystem", self.objectName())
        geometry_data = settings.value("geometry")

        if geometry_data:
            self.restoreGeometry(geometry_data)

    def closeEvent(self, event):
        try:
            self._app.aboutToQuit.disconnect(self.save_window_settings_registry)
        except (RuntimeError, TypeError):
            pass
        super().closeEvent(event)
        self.save_selected_preset()
        self.save_window_settings_registry()
        if self.help_window:
            self.help_window.close()


class facialGuiBase(GuiBase):
    def add_parent_list(self):
        pass


class YSFrame(QtWidgets.QWidget):
    """
    ウィンドウ内の区切り線
    設定項目は無いが、他ウィジェットと揃える為に load save メソッドを用意
    """
    def __init__(self, label=None, frame_shape="H"):
        super().__init__()
        if frame_shape == "V":
            shape = QtWidgets.QFrame.VLine

        else:
            shape = QtWidgets.QFrame.HLine

        if label:
            self.main_layout = QtWidgets.QGridLayout(self)
            self.main_layout.setSpacing(10)
            self.main_layout.setContentsMargins(0, 15, 0, 15)

            self.label = QtWidgets.QLabel(f"     {label}     ")
            self.label.setAlignment(QtCore.Qt.AlignCenter)
            self.label.setStyleSheet(
            f"""
            background-color: rgb({BACK_COLOR_2});
            color: rgb({STR_COLOR_3});
            border-radius: 10px;
            """)
    
            self.main_layout.addWidget(self.label, 0, 1)

            self.frame = QtWidgets.QFrame()
            self.frame.setFrameShape(shape)
            self.frame.setFrameShadow(QtWidgets.QFrame.Sunken)

            self.main_layout.addWidget(self.frame, 0, 2, 1, 10)

        else:
            self.main_layout = QtWidgets.QHBoxLayout(self)
            self.main_layout.setSpacing(10)
            self.main_layout.setContentsMargins(0, 0, 0, 0)

            self.frame = QtWidgets.QFrame()
            self.frame.setFrameShape(shape)
            self.frame.setFrameShadow(QtWidgets.QFrame.Sunken)
            self.main_layout.addWidget(self.frame)

    def set(self, data):
        pass

    def get(self):
        return "None"

    def connect(self, func):
        pass


class YSPushButton(QtWidgets.QPushButton):
    """
    ボタン
    初期の色を変えてるだけ
    """
    def __init__(self, label):
        super().__init__(label)
        self.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_1}); color: rgb({STR_COLOR_1});")

    def set_text(self, text):
        self.setText(text)


class YSLineEdit(QtWidgets.QWidget):
    """
    文字列の入力を受け付けるフィールド
    """
    def __init__(self, label="", placeholder_text="", validator_type=0):
        super().__init__()
        self.is_required = True # ここがTrueだった場合、空でcallされるとエラーにする

        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(f"{label} :")
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")

        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setPlaceholderText(placeholder_text)
        self.line_edit.setStyleSheet(f"background-color: rgb({BACK_COLOR_1});")
        self.connect(self.color_reset)
        if validator_type == 0:
            self.line_edit.setValidator(validator_1)

        elif validator_type == 1:
            self.line_edit.setValidator(validator_2)

        self.main_layout.addWidget(self.label, 0, 0)
        self.main_layout.addWidget(self.line_edit, 0, 1, 1, 2)

    def set(self, data):
        self.line_edit.setText(data)

    def get(self):
        return self.line_edit.text()

    def connect(self, func):
        self.line_edit.textChanged.connect(func)

    def error(self):
        self.label.setStyleSheet(f"color: rgb({ERROR_COLOR});")

    def color_reset(self):
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")

    def enable(self, input):
        self.line_edit.setEnabled(input)


class YSComboBox(QtWidgets.QWidget):
    """
    プルダウンメニュー
    """
    def __init__(self, label="", items=[]):
        super().__init__()
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.items = items

        self.label = QtWidgets.QLabel(f"{label} :")
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")

        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.addItems(self.items)
        self.combo_box.setStyleSheet(f"background-color: rgb({BACK_COLOR_1});")

        self.main_layout.addWidget(self.label, 0, 0)
        self.main_layout.addWidget(self.combo_box, 0, 1, 1, 2)

    def set(self, data):
        self.combo_box.setCurrentIndex(data)

    def get(self):
        return self.combo_box.currentIndex()

    def connect(self, func):
        self.combo_box.currentIndexChanged.connect(func)

    def get_items(self):
        return ":".join(self.items)


class YSRadioButton(QtWidgets.QWidget):
    """
    ラジオボタン
    """
    def __init__(self, label="", radio_label=[]):
        super().__init__()
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.radio_count = len(radio_label)

        self.label = QtWidgets.QLabel(f"{label} :")
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")

        self.main_layout.addWidget(self.label, 0, 0)

        self.radio_group = QtWidgets.QButtonGroup()
        self.radio_layout = QtWidgets.QHBoxLayout()
        self.radio = [None] * self.radio_count

        for i in range(self.radio_count):
            self.radio[i] = QtWidgets.QRadioButton(radio_label[i])
            self.radio[i].setStyleSheet(
            f"""
            QRadioButton::indicator {{
                width: 10px;
                height: 10px;
                border-radius: 5;
                background-color: rgb({BACK_COLOR_1});
                border: 1px solid gray;
            }}
            QRadioButton::indicator:checked {{
                background-color: rgb({STR_COLOR_1});
            }}
            """
            
            )
            self.radio_group.addButton(self.radio[i], i)
            self.radio_layout.addWidget(self.radio[i])

        self.main_layout.addLayout(self.radio_layout, 0, 1, 1, 2)
        self.radio[0].setChecked(True)

    def set(self, data):
        self.radio[data].setChecked(True)

    def get(self):
        return self.radio_group.checkedId()

    def connect(self, func):
        self.radio_group.buttonClicked.connect(func)


class YSDoubleSpinBox(QtWidgets.QWidget):
    """
    数値を受け付けるフィールド
    decimals=小数点以下の桁数
    """
    def __init__(self, label="", range=[0.1, 100.0], decimals=2, step=0.1):
        super().__init__()
        self.decimals = decimals

        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(f"{label} :")
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")

        self.spin_box = QtWidgets.QDoubleSpinBox()
        self.spin_box.setDecimals(decimals)
        self.spin_box.setSingleStep(step)
        self.spin_box.setStyleSheet(f"background-color: rgb({BACK_COLOR_1});")

        if isinstance(range[0], float) or isinstance(range[0], int) and not isinstance(range[0], bool):
            self.spin_box.setMinimum(range[0])

        if isinstance(range[1], float) or isinstance(range[1], int) and not isinstance(range[1], bool):
            self.spin_box.setMaximum(range[1])

        self.main_layout.addWidget(self.label, 0, 0)
        self.main_layout.addWidget(self.spin_box, 0, 1, 1, 2)

    def set(self, data):
        self.spin_box.setValue(data)

    def get(self):
        if self.decimals:
            return self.spin_box.value()

        else:
            return int(self.spin_box.value())

    def connect(self, func):
        self.spin_box.valueChanged.connect(func)


class YSCheckBox(QtWidgets.QWidget):
    """
    チェックボックス
    """
    def __init__(self, label=""):
        super().__init__()
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(f"{label} :")
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")

        self.checkbox = QtWidgets.QCheckBox()

        self.main_layout.addWidget(self.label, 0, 0)
        self.main_layout.addWidget(self.checkbox, 0, 1, 1, 2)

    def set(self, data):
        self.checkbox.setChecked(data)

    def get(self):
        return self.checkbox.isChecked()

    def connect(self, func):
        self.checkbox.stateChanged.connect(func)

    def enable(self, input):
        self.checkbox.setEnabled(input)


class YSLabel(QtWidgets.QWidget):
    """
    ラベル
    文字列を表示するだけ
    """
    def __init__(self, label=""):
        super().__init__()
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(f"{label} :")
        self.label.setAlignment(QtCore.Qt.AlignRight)

        self.label2 = QtWidgets.QLabel()

        self.main_layout.addWidget(self.label, 0, 0)
        self.main_layout.addWidget(self.label2, 0, 1, 1, 2)

        self.setStyleSheet(f"color: rgb({STR_COLOR_1});")

    def set(self, data):
        self.label2.setText(data)

    def get(self):
        return self.label2.text()

    def connect(self, func):
        pass

    def setStyleSheet(self, input):
        self.label.setStyleSheet(input)
        self.label2.setStyleSheet(input)


class NonEmptyLineEditDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtWidgets.QLineEdit(parent)
        editor.setValidator(validator_1)
        return editor


class DragDropListWidget(QtWidgets.QListWidget):
    reordered = QtCore.Signal()
    countChanged = QtCore.Signal(int)

    def __init__(self):
        super().__init__()
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setItemDelegate(NonEmptyLineEditDelegate())

    def dropEvent(self, event):
        super().dropEvent(event)
        self.reordered.emit() 

    def _emit_count_if_changed(self, prev_count):
        new_count = self.count()
        if not new_count == prev_count:
            self.countChanged.emit(new_count)

    def addItem(self, item):
            prev = self.count()
            super().addItem(item)
            self._emit_count_if_changed(prev)

    def takeItem(self, row):
        prev = self.count()
        item = super().takeItem(row)
        self._emit_count_if_changed(prev)
        return item

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            for item in self.selectedItems():
                row = self.row(item)
                if self.count() > 1: # 最後の一個は消さない
                    self.takeItem(row)
        else:
            super().keyPressEvent(event)


class YSListWidget(QtWidgets.QWidget):
    def __init__(self, label=""):
        super().__init__()
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(f"{label} :")
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")
        self.label.setAlignment(QtCore.Qt.AlignRight)

        self.list_widget: QtWidgets.QListWidget = QtWidgets.QListWidget()
        self.list_widget.setStyleSheet(f"background-color: rgb({BACK_COLOR_1}); color: rgb({STR_COLOR_1});")

        self.main_layout.addWidget(self.label, 0, 0)
        self.main_layout.addWidget(self.list_widget, 0, 1, 1, 2)

    def set(self, data):
        self.list_widget.clear()
        self.list_widget.addItems(data)

    def get(self):
        text = ""
        item = self.list_widget.currentItem()
        if item:
            text = item.text()
        return text

    def connect(self, func):
        self.list_widget.currentItemChanged.connect(func)


class YSCheckList(QtWidgets.QWidget):
    def __init__(self, label="", message="✅Use Carpal"):
        super().__init__()
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(f"{label} :")
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")
        self.label.setAlignment(QtCore.Qt.AlignRight)

        self.message = QtWidgets.QLabel(message)
        self.message.setAlignment(QtCore.Qt.AlignLeft)

        self.add_button = YSPushButton("Add Name")
        self.add_button.clicked.connect(self.add)

        self.list_widget = DragDropListWidget()
        self.list_widget.setStyleSheet(f"background-color: rgb({BACK_COLOR_1}); color: rgb({STR_COLOR_1});")
        self.list_widget.itemChanged.connect(self.check_overlap)

        self.main_layout.addWidget(self.label, 0, 0)
        self.main_layout.addWidget(self.message, 0, 1)
        self.main_layout.addWidget(self.list_widget, 1, 1, 1, 2)
        self.main_layout.addWidget(self.add_button, 2, 1, 1, 2)

    def set(self, data):
        """
        dataの構造
        [[名前１, 名前1のチェック状況], [名前2, 名前2のチェック状況], [名前3, 名前3のチェック状況]]
        """

        self.list_widget.clear()

        for d in data:
            name = d[0]
            checked = d[1]

            item = QtWidgets.QListWidgetItem(name)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.list_widget.addItem(item)

    def get(self):
        data = []

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            name = item.text()
            checked = item.checkState() == QtCore.Qt.Checked
            data.append([name, checked])

        return data

    def connect(self, func):
        self.list_widget.itemChanged.connect(func)
        self.list_widget.reordered.connect(func)
        self.list_widget.countChanged.connect(func)

    def add(self):
        item = QtWidgets.QListWidgetItem("Finger_1")
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Unchecked)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.list_widget.addItem(item)

        # アイテムを選択状態にする
        self.list_widget.setCurrentItem(item)
        self.list_widget.editItem(item)

    def check_overlap(self):
        item = self.list_widget.currentItem()
        if not item:
            return

        base_name = item.text()
        names = set()

        # 自分以外の全アイテムの名前を取得
        for i in range(self.list_widget.count()):
            other_item = self.list_widget.item(i)
            if other_item is not item:
                names.add(other_item.text())

        # もし被ってなければそのまま終了
        if base_name not in names:
            return

        # 被っている場合は連番を付けて一意化
        index = 1
        new_name = f"{base_name}_{index}"
        while new_name in names:
            index += 1
            new_name = f"{base_name}_{index}"

        # 名前を更新
        item.setText(new_name)


class YSSidePrefix(QtWidgets.QWidget):
    """
    モジュールが左右を決定するためのラジオボタン
    """
    def __init__(self):
        super().__init__()
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.radio_button = YSRadioButton(label="★ Side", radio_label=["None", "Left", "Right"])
        self.radio_button.connect(self.call)

        self.label = YSLabel(label="Prefix")
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_2});")
        self.call()

        self.main_layout.addWidget(self.radio_button)
        self.main_layout.addWidget(self.label)

    def call(self):
        id = self.radio_button.get()
        text = "None"
        if id == 1:
            text = "''  L_  ''"

        if id == 2:
            text = "''  R_  ''"

        self.label.set(text)

    def set_text(self, text):
        self.label.set(text)

    def get_text(self):
        return self.label.set()

    def get_prefix(self):
        id = self.radio_button.get()
        prefix = ""
        if id == 1:
            prefix = "L_"

        if id == 2:
            prefix = "R_"

        return prefix

    def set(self, data):
        self.radio_button.set(data)
        self.call()

    def get(self):
        return self.radio_button.get()

    def connect(self, func):
        self.radio_button.connect(func)


class YSParentList(QtWidgets.QWidget):
    """
    モジュールの親ジョイントを設定するためのフィールド
    右部のボタンからGUI上で設定可能
    """
    def __init__(self, parent, label="", placeholder_text=""):
        super().__init__()
        self.parent = parent
        self.module_list = None

        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.sub_layout = QtWidgets.QHBoxLayout(self)
        self.sub_layout.setSpacing(10)
        self.sub_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(f"{label} :")
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")
        self.label.setAlignment(QtCore.Qt.AlignRight)

        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setPlaceholderText(placeholder_text)
        self.line_edit.setStyleSheet(f"background-color: rgb({BACK_COLOR_1}); color: rgb({STR_COLOR_1});")
        self.line_edit.setValidator(validator_1)

        self.button = YSPushButton("  . . .  ")
        self.button.clicked.connect(self.call)

        self.sub_layout.addWidget(self.line_edit)
        self.sub_layout.addWidget(self.button)

        self.main_layout.addWidget(self.label, 0, 0)
        self.main_layout.addLayout(self.sub_layout, 0, 1, 1, 2)

    def call(self):
        self.module_list = YSModuleList(self.parent, self.line_edit)
        self.module_list.exec()

    def set(self, data):
        self.line_edit.setText(data)

    def get(self):
        return self.line_edit.text()

    def connect(self, func):
        self.line_edit.textChanged.connect(func)


class YSModuleList(QtWidgets.QDialog):
    """YSParentList の右部から呼び出されるダイアログ
    モジュールとジョイントのリストを表示し、そこからモジュールの親ジョイントを設定できる
    """
    def __init__(self, parent, line_edit):
        super().__init__(parent)
        self.setup(parent, line_edit)

        self.window()
        self.gui()
        self.load_module()

    def setup(self, parent, line_edit):
        self.meta_nodes = core.get_meta_nodes()
        self.facial_meta_nodes = core.get_facial_meta_nodes()
        self.parent = parent
        self.title = parent.title
        self.line_edit = line_edit

    def window(self):
        self.setWindowTitle(f"{self.title} - Module List")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setMinimumWidth(300)
        self.setStyleSheet(f"background-color: rgb({WINDOW_COLOR_2});")

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

    def gui(self):
        self.label1 = QtWidgets.QLabel("Module Names")
        self.label1.setStyleSheet(f"color: rgb({STR_COLOR_1});")
        self.module_list = QtWidgets.QListWidget()
        self.label2 = QtWidgets.QLabel("Joint Names")
        self.label1.setStyleSheet(f"color: rgb({STR_COLOR_1});")
        self.joint_list = QtWidgets.QListWidget()
        self.joint_list.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_2}); color: rgb({STR_COLOR_1});")
        self.button = YSPushButton("Accept")
        self.button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_2}); color: rgb({STR_COLOR_1});")

        self.module_list.currentItemChanged.connect(self.load_joint_name)
        self.joint_list.itemDoubleClicked.connect(self.call)
        self.button.clicked.connect(self.call)

        self.layout.addWidget(self.label1)
        self.layout.addWidget(self.module_list)
        self.layout.addWidget(self.label2)
        self.layout.addWidget(self.joint_list)
        self.layout.addWidget(self.button)

    def load_module(self):
        modules = [cmds.getAttr(f"{meta}.GroupName") for meta in self.meta_nodes + self.facial_meta_nodes]

        self.module_list.addItems(modules)

    def load_joint_name(self):
        module = self.module_list.currentItem()

        meta = f"Meta_{module.text()}"
        joints = core.get_list_attributes(meta, "JointName")
        joints = [jt for jt in joints if "_GB" not in jt]
        self.joint_list.clear()
        self.joint_list.addItems(joints)

    def call(self):
        joint_name = self.joint_list.currentItem()
        self.line_edit.setText(joint_name.text())
        self.close()
        self.deleteLater()


class YSPresetBox(QtWidgets.QWidget):
    """
    プリセットを呼び出したり保存するメニュー
    TODO : ごちゃついてる。まとめられそうなところはまとめたい。
    """
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.get_json_file_names()
        self.gui()

    def get_json_file_names(self):
        self.json_files = ["default"]
        for f in os.listdir(self.parent.json_path):
            if f.endswith(".json") and os.path.isfile(os.path.join(self.parent.json_path, f)):
                name = os.path.splitext(f)[0]
                if name == "default":
                    continue

                self.json_files.append(name)

    def gui(self):
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.sub_layout = QtWidgets.QHBoxLayout(self)
        self.sub_layout.setSpacing(10)
        self.sub_layout.setContentsMargins(0, 0, 0, 0)

        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.addItems(self.json_files)
        self.combo_box.currentIndexChanged.connect(self.load_preset)
        self.combo_box.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_1});")

        self.add_button = YSPushButton("Save As")
        self.add_button.clicked.connect(self.add)
        self.add_button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_1}); color: rgb({STR_COLOR_1});")

        self.remove_button = YSPushButton("Remove")
        self.remove_button.clicked.connect(self.remove)
        self.remove_button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_1}); color: rgb({STR_COLOR_1});")

        self.update_button = YSPushButton("  Save  ")
        self.update_button.clicked.connect(self.updata)
        self.update_button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_1}); color: rgb({STR_COLOR_1});")

        self.rename_button = YSPushButton("Rename")
        self.rename_button.clicked.connect(self.rename)
        self.rename_button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_1}); color: rgb({STR_COLOR_1});")

        self.save_checker = YSPushButton("")
        self.save_checker.clicked.connect(self.load_preset)
        self.save_checker.setStyleSheet(f"background-color: rgba(0, 0, 0, 0); font-size: 24px;")
        self.save_checker.setFixedSize(32, 32)

        self.sub_layout.addWidget(self.add_button)
        self.sub_layout.addWidget(self.update_button)
        self.sub_layout.addWidget(self.remove_button)
        self.sub_layout.addWidget(self.rename_button)
        self.sub_layout.addWidget(self.save_checker)

        self.main_layout.addWidget(self.combo_box, 0, 0, 1, 2)
        self.main_layout.addLayout(self.sub_layout, 0, 2, 1, 1)

    def connect_checker(self):
        for w in self.parent.widget:
            self.parent.widget[w].connect(self.set_checker)

    def set_checker(self):
        self.save_checker.set_text("🔄")

    def reset_checker(self):
        self.save_checker.set_text("")

    def set_current_index(self, index):
        self.combo_box.setCurrentIndex(index)

    def get_current_index(self):
        return self.combo_box.currentIndex()

    def set_current_text(self, text):
        self.combo_box.setCurrentText(text)

    def get_current_text(self):
        return self.combo_box.currentText()

    def reset(self):
        self.get_json_file_names()
        self.combo_box.clear()
        self.combo_box.addItems(self.json_files)
        self.reset_checker()

    def load_preset(self):
        name = self.combo_box.currentText()
        if not name:
            return

        json_path = os.path.join(self.parent.json_path, f"{name}.json")
        with open(json_path, "r") as f:
            data = json.load(f)

        for d in data:
            if d in self.parent.widget:
                self.parent.widget[d].set(data[d])

        self.reset_checker()

    def save_preset(self, name):
        json_path = os.path.join(self.parent.json_path, f"{name}.json")
        data = {}
        for w in self.parent.widget:
            data[w] = self.parent.widget[w].get()

        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)
        
        self.reset()
        self.set_current_text(name)

    def remove_preset(self, name):
        json_path = os.path.join(self.parent.json_path, f"{name}.json")
        os.remove(json_path)
        self.reset()

    def rename_preset(self, old, new):
        json_path = os.path.join(self.parent.json_path, f"{old}.json")
        with open(json_path, "r") as f:
            data = json.load(f)

        self.remove_preset(old)
        self.save_preset(new)

        for d in data:
            self.parent.widget[d].load(data[d])

        self.save_preset(new)

    def add(self):
        dialog = YSInputDialog(self.parent, "Save As", "Preset Name")
        ok, text = dialog.get_result()
        if not ok:
            return
        
        if text == "default":
            # 追加するプリセットの名前が "default" であった場合、処理を中断し、メッセージを表示する
            YSErrorDialog(self.parent, "Error", "'default' に変更を加えることはできません。")
            return
        
        add = True
        for file in self.json_files:
            if file == text:
                # 追加するプリセットの名前がすでに存在していた場合、上書きするかを確認する
                dialog = YSWarningDialog(self.parent, "Updata", f"'{text}' はすでに存在しています。上書きしますか？")
                add = dialog.get_result()
                break

        if add:
            self.save_preset(text)

    def remove(self):
        text = self.combo_box.currentText()
        if text == "default":
            # 選択中のプリセットが "default" であった場合、処理を中断し、メッセージを表示する
            YSErrorDialog(self.parent, "Error", "'default' を削除することはできません。")
            return

        dialog = YSWarningDialog(self.parent, "Remove", "本当に削除しますか？")
        if dialog.get_result():
            self.remove_preset(text)

    def updata(self):
        text = self.combo_box.currentText()
        if text == "default":
            # 選択中のプリセットが "default" であった場合、処理を中断し、メッセージを表示する
            YSErrorDialog(self.parent, "Error", "'default' に変更を加えることはできません。")
            return

        dialog = YSWarningDialog(self.parent, "Save", "本当に上書きしますか？")
        if dialog.get_result():
            self.save_preset(text)

    def rename(self):
        old_name = self.combo_box.currentText()
        if old_name == "default":
            # 選択中のプリセットが "default" であった場合、処理を中断し、メッセージを表示する
            YSErrorDialog(self.parent, "Error", "'default' に変更を加えることはできません。")
            return

        dialog = YSInputDialog(self.parent, "Rename", "New Name")
        ok, text = dialog.get_result()
        if not ok:
            return
        
        if text == "default":
            # リネームするプリセットの名前が "default" であった場合、処理を中断し、メッセージを表示する
            YSErrorDialog(self.parent, "Error", "'default' に変更を加えることはできません。")
            return
        
        rename = True
        for file in self.json_files:
            if file == text:
                # 変更後のプリセットの名前がすでに存在していた場合、上書きするかを確認する
                dialog = YSWarningDialog(self.parent, "Updata", f"'{text}' はすでに存在しています。上書きしますか？")
                rename = dialog.get_result()
                break

        if rename:
            self.rename_preset(old_name, text)


class YSDialog(QtWidgets.QDialog):
    """
    ダイアログのベースクラス
    get_result により、ユーザーの選択を受け取る
    """
    def __init__(self, parent, title, message):
        if not parent:
            parent = maya_main_window

        super().__init__(parent)
        self.setup(parent, title, message)
        self.set_title()
        self.window()
        self.add_label()
        self.gui()
        self.add_button()
        self.beep()
        self.result = self.exec()

    def setup(self, parent, title, message):
        self.parent = parent
        self.title = title
        self.message = message
        self.parent_title = ""
        if not parent == maya_main_window:
            self.parent_title = parent.title

    def set_title(self):
        pass

    def window(self):
        self.setWindowTitle(self.title)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setStyleSheet(f"background-color: rgb({WINDOW_COLOR_2});")
        self.setMinimumWidth(300)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 20, 10, 10)

    def add_label(self):
        pass

    def gui(self):
        pass

    def add_button(self):
        pass

    def beep(self):
        pass

    def get_result(self):
        if self.result == QtWidgets.QDialog.Accepted:
            return True

        else:
            return False

    def ok(self):
        self.accept()

    def cancel(self):
        self.reject()

    def closeEvent(self, event):
        self.deleteLater()
        super().closeEvent(event)


class YSConfirmDialog(YSDialog):
    """
    メッセージとok cancelボタンがあるだけのシンプルなダイアログ
    YSWarningDialogに統合するかも
    """
    def set_title(self):
        self.title = f"{self.parent_title} - {self.title}"

    def add_label(self):
        self.label = QtWidgets.QLabel(self.message)
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.label)

    def add_button(self):
        self.sub_layout = QtWidgets.QHBoxLayout()

        self.ok_button = QtWidgets.QPushButton("OK")
        self.ok_button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_2});")
        self.ok_button.clicked.connect(self.ok)

        self.cl_button = QtWidgets.QPushButton("Cancel")
        self.cl_button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_2});")
        self.cl_button.clicked.connect(self.cancel)

        self.sub_layout.addWidget(self.ok_button)
        self.sub_layout.addWidget(self.cl_button)

        self.layout.addLayout(self.sub_layout)


class YSWarningDialog(YSDialog):
    """
    警告メッセージとok cancelボタンがあるダイアログ
    """
    def set_title(self):
        self.title = f"{self.parent_title} - {self.title}"

    def add_label(self):
        self.label = QtWidgets.QLabel(f"⚠️  {self.message}")
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.label)

    def add_button(self):
        self.sub_layout = QtWidgets.QHBoxLayout()

        self.ok_button = QtWidgets.QPushButton("OK")
        self.ok_button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_2});")
        self.ok_button.clicked.connect(self.ok)

        self.cl_button = QtWidgets.QPushButton("Cancel")
        self.cl_button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_2});")
        self.cl_button.clicked.connect(self.cancel)

        self.sub_layout.addWidget(self.ok_button)
        self.sub_layout.addWidget(self.cl_button)

        self.layout.addLayout(self.sub_layout)

    def beep(self):
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)


class YSErrorDialog(YSDialog):
    """
    エラーメッセージとokボタンがあるダイアログ
    """
    def window(self):
        super().window()
        self.setStyleSheet(f"background-color: rgb({WINDOW_COLOR_3});")

    def set_title(self):
        self.title = f"{self.parent_title} - {self.title}"

    def add_label(self):
        self.label = QtWidgets.QLabel(f"🚫  {self.message}")
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_3});")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.label)

    def add_button(self):
        self.ok_button = QtWidgets.QPushButton("OK")
        self.ok_button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_3}); color: rgb({STR_COLOR_3});")
        self.ok_button.clicked.connect(self.ok)

        self.layout.addWidget(self.ok_button)

    def beep(self):
        winsound.MessageBeep(winsound.MB_ICONHAND)


class YSInputDialog(YSDialog):
    """
    lineEditと各ボタンがあるダイアログ
    get_result でユーザーの選択と、入力された文字列を取得できる
    文字列が空の場合、okボタンは無効
    """
    def set_title(self):
        self.title = f"{self.parent_title} - {self.title}"

    def add_label(self):
        self.line_edit = YSLineEdit(label=self.message, placeholder_text="Text", validator_type=1)
        self.line_edit.line_edit.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_2});")
        self.layout.addWidget(self.line_edit)

    def add_button(self):
        self.sub_layout = QtWidgets.QGridLayout()

        self.ok_button = QtWidgets.QPushButton("OK")
        self.ok_button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_2});")
        self.ok_button.clicked.connect(self.ok)

        self.cl_button = QtWidgets.QPushButton("Cancel")
        self.cl_button.setStyleSheet(f"background-color: rgb({BUTTON_COLOR_2});")
        self.cl_button.clicked.connect(self.cancel)

        self.sub_layout.addWidget(self.ok_button, 1, 0, 1, 2)
        self.sub_layout.addWidget(self.cl_button, 1, 2, 1, 2)

        self.layout.addLayout(self.sub_layout)

    def ok(self):
        string = self.line_edit.get()
        if string:
            self.accept()

    def get_result(self):
        string = self.line_edit.get()
        if self.result == QtWidgets.QDialog.Accepted:
            return True, string

        else:
            return False, string


class YSHelpWindow(QtWidgets.QWidget):
    """
    ヘルプ用のmdファイルを読み込んで表示するウィンドウ
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setup(parent)            # 変数宣言
        self.get_md_path()            # mdのパスを取得
        self.pre_close()              # すでに同じGUIが存在する場合、事前に閉じておく
        self.window()                 # windowの設定
        self.gui()
        self.load()                   # mdを読み込んで表示

    def setup(self, parent):
        self.parent = parent
        self.module_name = parent.module_name
        self.parent_title = parent.title
        self.dir_path = parent.dir_path
        self.md_path = ""
        self.main_layout = None
        self.browser = None

    def get_md_path(self):
        self.md_path = os.path.join(self.dir_path, "HELP.md")

    def pre_close(self):
        for widget in QtWidgets.QApplication.allWidgets():
            if widget.objectName() == f"YS_{self.module_name}_Help_Gui":
                widget.close()
                widget.deleteLater()

    def window(self):
        self.setWindowTitle(f"{self.parent_title} - Help")
        self.setObjectName(f"YS_{self.module_name}_Help_Gui")
        self.setWindowFlags(QtCore.Qt.Window)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(500)
        self.setStyleSheet(f"background-color: rgb({WINDOW_COLOR_2});")

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

    def gui(self):
        self.browser = QtWidgets.QTextBrowser()
        self.main_layout.addWidget(self.browser)

    def load(self):
        with open(self.md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        html = simple_md_to_html(md_text)
        self.browser.setHtml(html)


def simple_md_to_html(md_text):
    lines = md_text.splitlines()
    html_lines = []
    in_list = False

    for line in lines:
        line = line.strip()

        # 水平線
        if line == "---":
            html_lines.append("<hr>")
            continue

        # h1
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:].strip()}</h1>")
            continue

        # h2
        if line.startswith("## "):
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
            continue

        # h3
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")
            continue

        # h4
        if line.startswith("#### "):
            html_lines.append(f"<h4>{line[4:].strip()}</h4>")
            continue

        # 箇条書き（ul対応）
        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line[2:].strip()}</li>")
            continue

        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False

        # Q&A形式（Q: or A:）
        if line.startswith("**Q:**"):
            question = line.replace("**Q:**", "").strip()
            html_lines.append(f"<p><strong>Q:</strong> {question}</p>")
            continue

        if line.startswith("**A:**"):
            answer = line.replace("**A:**", "").strip()
            html_lines.append(f"<p><strong>A:</strong> {answer}</p>")
            continue

        # 太字対応（**text**）
        def bold_repl(match):
            return f"<strong>{match.group(1)}</strong>"

        line = re.sub(r"\*\*(.+?)\*\*", bold_repl, line)

        # 通常段落
        if line:
            html_lines.append(f"<p>{line}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


class YSSelecterBox(QtWidgets.QWidget):
    """
    ノードを選択して登録できるテキストボックス
    """
    def __init__(self, label="", placeholder_text=""):
        super().__init__()
        self.is_required = True # ここがTrueだった場合、空でcallされるとエラーにする

        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.sub_layout = QtWidgets.QHBoxLayout(self)
        self.sub_layout.setSpacing(10)
        self.sub_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(f"{label} :")
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")
        self.label.setAlignment(QtCore.Qt.AlignRight)

        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setPlaceholderText(placeholder_text)
        self.line_edit.setStyleSheet(f"background-color: rgb({BACK_COLOR_1}); color: rgb({STR_COLOR_1});")
        self.line_edit.setValidator(validator_1)

        self.button = YSPushButton("Set Selected")
        self.button.clicked.connect(self.call)

        self.sub_layout.addWidget(self.line_edit)
        self.sub_layout.addWidget(self.button)

        self.main_layout.addWidget(self.label, 0, 0)
        self.main_layout.addLayout(self.sub_layout, 0, 1, 1, 2)

    def set(self, data):
        self.line_edit.setText(data)

    def get(self):
        return self.line_edit.text()

    def connect(self, func):
        self.line_edit.textChanged.connect(func)

    def error(self):
        self.label.setStyleSheet(f"color: rgb({ERROR_COLOR});")

    def color_reset(self):
        self.label.setStyleSheet(f"color: rgb({STR_COLOR_1});")

    def enable(self, input):
        self.line_edit.setEnabled(input)

    def call(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        
        self.set(sel[0])