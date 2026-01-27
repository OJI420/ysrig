# YSRigのプラグインロード用のスクリプトです。
# Mayaのビューポート上にドラッグアンドドロップしてください

import sys
import os
import functools
import shutil
import json
import tempfile
from maya import cmds, OpenMayaUI

maya_ver = cmds.about(v=True)

if int(maya_ver) <= 2024:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance

elif int(maya_ver) >= 2025:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance

PLUGIN_NAME = "ysrig_plugin.py"
VERSION = "2.6.1"

MAYA_WINDOW = wrapInstance(int(OpenMayaUI.MQtUtil.mainWindow()), QtWidgets.QWidget) 

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
MAYA_DOC_PATH = os.path.join(os.path.expanduser("~"), "Documents", "maya")
MAYA_MOD_PATH = os.path.join(MAYA_DOC_PATH, "modules")

WIN_SIZE = (1000, 300)

WIN_COLOR = "#ffffff"
LABEL_COLOR = "#003253"
BUTTON_COLOR1 = "#003253"
BUTTON_COLOR2 = "#006EFF"
BUTTON_COLOR3 = "#FF0000"
BUTTON_LABEL_COLOR = "#ffffff"
LINEEDIT_COLOR = "#E3E3E3"
LINEEDIT_TXT_COLOR = "#003253"

font1 = QtGui.QFont()
font1.setPointSize(10)
font1.setBold(True)

font2 = QtGui.QFont()
font2.setPointSize(20)
font2.setBold(True)

font3 = QtGui.QFont()
font3.setPointSize(25)
font3.setBold(True)

def page_update(func):
    """
    メソッドが実行される前に古いページを削除し、実行後に新しいページを追加するデコレータ
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.page:
            self.layout.removeWidget(self.page)
            self.page.setParent(None)
            self.page.deleteLater()

        result = func(self, *args, **kwargs)

        if self.page:
            self.layout.addWidget(self.page)

        return result
    return wrapper


class Window(QtWidgets.QWidget):
    def __init__(self, parent=MAYA_WINDOW):
        super().__init__(parent=parent)
        self.setWindowTitle(f"YSRig-{VERSION}-Setup")
        self.setWindowFlags(QtCore.Qt.Window)
        self.setFixedSize(*WIN_SIZE)
        self.setStyleSheet(f"background-color: {WIN_COLOR};")

        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        label = QtWidgets.QLabel(f"YSRig ver {VERSION} Installer")
        label.setStyleSheet(f"color: {LABEL_COLOR};")
        label.setFont(font3)
        label.setAlignment(QtCore.Qt.AlignCenter)

        self.main_layout.addWidget(label, 0, 0, 1, 1)

        self.layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(self.layout, 1, 0, 5, 1)

        self.install_path = MAYA_MOD_PATH
        self.page = None

        self.show_install_path_page()

    @page_update
    def show_install_path_page(self):
        self.page = InitPage(self)

    @page_update
    def show_install_success_page(self):
        self.page = InstallSuccessPage(self)

    @page_update
    def show_update_or_uninstall_page(self):
        self.page = UpdateOrUninstallPage(self)

    @page_update
    def show_uninstall_page(self):
        self.page = UninstallPage(self)

    @page_update
    def show_uninstall_success_page(self):
        self.page = UninstallSuccessPage(self)

    @page_update
    def show_update_page(self):
        self.page = UpdatePage(self)

    @page_update
    def show_update_success_page(self):
        self.page = UpdateSuccessPage(self)


class PageBase(QtWidgets.QWidget):
    def __init__(self, parent:Window):
        super().__init__(parent)
        self.parent = parent

        self.main_layout = QtWidgets.QGridLayout(self)
        self.dialog_layout = QtWidgets.QGridLayout()
        self.button_layout = QtWidgets.QGridLayout()

        self.main_layout.addLayout(self.dialog_layout, 0, 0, 5, 1)
        self.main_layout.addLayout(self.button_layout, 5, 0, 1, 1)

        self.next_button = QtWidgets.QPushButton()
        self.back_button = QtWidgets.QPushButton()
        self.next_button.clicked.connect(self.call_next)
        self.back_button.clicked.connect(self.call_back)
        self.next_button.setGraphicsEffect(None)
        self.back_button.setGraphicsEffect(None)
        self.next_button.setFont(font2)
        self.back_button.setFont(font2)
        self.next_button.setStyleSheet(f"background-color: {WIN_COLOR}; color: {BUTTON_COLOR2}; border-radius: 1px;")
        self.back_button.setStyleSheet(f"background-color: {WIN_COLOR}; color: {BUTTON_COLOR1}; border-radius: 1px;")

        self.button_layout.addWidget(self.back_button, 0, 0, 1, 1)
        self.button_layout.addWidget(self.next_button, 0, 5, 1, 1)
        self.next_button_label = False
        self.back_button_label = False

        self.set_button_settings()
        self.apply_button_settings()
        self.dialog()

    def set_button_settings(self):
        pass

    def apply_button_settings(self):
        for label, button in zip([self.next_button_label, self.back_button_label], [self.next_button, self.back_button]):
            if label:
                button.setText(label)

            else:
                button.setEnabled(False)

    def dialog(self):
        pass

    def call_next(self):
        pass

    def call_back(self):
        pass


class InitPage(PageBase):
    def set_button_settings(self):
        self.next_button_label = "Next"

    def dialog(self):
        label = QtWidgets.QLabel("Install Directory Path: ")
        label.setStyleSheet(f"color: {LABEL_COLOR};")
        label.setFont(font1)

        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setText(self.parent.install_path)
        self.line_edit.setFont(font1)
        self.line_edit.textChanged.connect(self.set_install_path)
        self.line_edit.setStyleSheet(f"background-color: {LINEEDIT_COLOR}; color: {LINEEDIT_TXT_COLOR};")

        button = QtWidgets.QPushButton("Browse")
        button.clicked.connect(self.call_file_dialog)
        button.setStyleSheet(f"background-color: {BUTTON_COLOR1}; color: {BUTTON_LABEL_COLOR};")

        self.dialog_layout.addWidget(label, 0, 0, 1, 1)
        self.dialog_layout.addWidget(self.line_edit, 0, 1, 1, 3)
        self.dialog_layout.addWidget(button, 0, 4, 1, 1)

    def call_file_dialog(self):
        current_path = self.line_edit.text()
        if os.path.isdir(current_path):
            open_path = current_path

        else:
            open_path = MAYA_DOC_PATH

        result = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "インストール先のフォルダを選択",
            open_path
        )
        if result:
            self.line_edit.setText(result)

    def call_next(self):
        install_path = os.path.join(self.line_edit.text(), "YSRig")
        if os.path.isdir(install_path):
            self.parent.show_update_or_uninstall_page()
            return

        # インストール
        install_path = self.line_edit.text()
        ysrig_mod_file = os.path.join(install_path, "YSRig.mod")

        source_dir = os.path.join(THIS_DIR, "modules", "YSRig")
        source_mod = os.path.join(THIS_DIR, "modules", "YSRig.mod")

        copy_folder(source_dir, install_path)
        shutil.copy(source_mod, ysrig_mod_file)
        self.parent.show_install_success_page()

    def set_install_path(self):
        self.parent.install_path = self.line_edit.text()


class InstallSuccessPage(PageBase):
    def set_button_settings(self):
        self.next_button_label = "OK"

    def dialog(self):
        if self.parent.install_path == MAYA_MOD_PATH:
            if load_plugin():
                text = "インストールが正常に完了しました。"

            else:
                text = "プラグインのロードに失敗しました。\nMayaを再起動し、プラグインマネージャーから 'ysrig_plugin.py' を有効にしてください。"

        else:
            text = "インストールが正常に完了しました。\nMayaを再起動し、プラグインマネージャーから 'ysrig_plugin.py' を有効にしてください。"

        label = QtWidgets.QLabel(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setFont(font1)
        label.setStyleSheet(f"color: {LABEL_COLOR};")
        self.dialog_layout.addWidget(label)

    def call_next(self):
        self.parent.close()
        self.parent.deleteLater()


class UpdateOrUninstallPage(PageBase):
    def set_button_settings(self):
        self.back_button_label = "Back"

    def dialog(self):
        text = "YSRigがすでにインストールされています。操作を選択してください。"
        label = QtWidgets.QLabel(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setFont(font1)
        label.setStyleSheet(f"color: {LABEL_COLOR};")

        update_button = QtWidgets.QPushButton("Update")
        update_button.clicked.connect(self.call_update)
        update_button.setFont(font2)
        update_button.setStyleSheet(f"background-color: {WIN_COLOR}; color: {BUTTON_COLOR2}; border-radius: 1px;")

        uninstall_button = QtWidgets.QPushButton("Uninstall")
        uninstall_button.clicked.connect(self.call_uninstall)
        uninstall_button.setFont(font2)
        uninstall_button.setStyleSheet(f"background-color: {WIN_COLOR}; color: {BUTTON_COLOR3}; border-radius: 1px;")

        self.dialog_layout.addWidget(label)
        self.dialog_layout.addWidget(update_button)
        self.dialog_layout.addWidget(uninstall_button)

    def call_back(self):
        self.parent.show_install_path_page()

    def call_update(self):
        self.parent.show_update_page()

    def call_uninstall(self):
        self.parent.show_uninstall_page()


class UninstallPage(PageBase):
    def set_button_settings(self):
        self.next_button_label = "Uninstall"
        self.back_button_label = "Back"
        self.next_button.setStyleSheet(f"color: {BUTTON_COLOR3}; border-radius: 1px;")

    def dialog(self):
        text = "本当にYSRigをアンインストールしますか？\nユーザー設定は消去されます。"
        label = QtWidgets.QLabel(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setFont(font1)
        label.setStyleSheet(f"color: {LABEL_COLOR};")
        self.dialog_layout.addWidget(label)

    def call_next(self):
        # アンインストール
        install_path = self.parent.install_path
        ysrig_path = os.path.join(install_path, "YSRig")
        ysrig_mod_file = os.path.join(install_path, "YSRig.mod")

        shutil.rmtree(ysrig_path)
        if os.path.exists(ysrig_mod_file):
            os.remove(ysrig_mod_file)

        self.parent.show_uninstall_success_page()

    def call_back(self):
        self.parent.show_update_or_uninstall_page()


class UninstallSuccessPage(PageBase):
    def set_button_settings(self):
        self.next_button_label = "OK"

    def dialog(self):
        text = "アンインストールが正常に完了しました。"
        label = QtWidgets.QLabel(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setFont(font1)
        label.setStyleSheet(f"color: {LABEL_COLOR};")
        self.dialog_layout.addWidget(label)

    def call_next(self):
        self.parent.close()
        self.parent.deleteLater()


class UpdatePage(PageBase):
    def set_button_settings(self):
        self.next_button_label = "Update"
        self.back_button_label = "Back"

    def dialog(self):
        text = "ユーザー設定を引き継ぐ : "
        checkbox_label = QtWidgets.QLabel(text)
        checkbox_label.setAlignment(QtCore.Qt.AlignRight)
        checkbox_label.setFont(font1)
        checkbox_label.setStyleSheet(f"color: {LABEL_COLOR};")

        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(True)

        self.dialog_layout.addWidget(checkbox_label, 0, 0, 1, 3)
        self.dialog_layout.addWidget(self.checkbox, 0, 3, 1, 2)

    def call_back(self):
        self.parent.show_update_or_uninstall_page()

    def call_next(self):
        install_path = self.parent.install_path
        ysrig_install_dir = os.path.join(install_path, "YSRig")
        ysrig_mod_file = os.path.join(install_path, "YSRig.mod")

        temp_dir = tempfile.gettempdir()
        tmp_settings_file = os.path.join(temp_dir, "ysrig_tmp_settings.json")
        export(tmp_settings_file, ysrig_install_dir)

        # 古いバージョンを削除
        shutil.rmtree(ysrig_install_dir)
        if os.path.exists(ysrig_mod_file):
            os.remove(ysrig_mod_file)

        # ファイルのコピー
        source_dir = os.path.join(THIS_DIR, "modules", "YSRig")
        source_mod = os.path.join(THIS_DIR, "modules", "YSRig.mod")

        copy_folder(source_dir, install_path)
        shutil.copy(source_mod, ysrig_mod_file)

        # 設定を引き継ぐ場合はインポート
        if self.checkbox.isChecked():
            import_(tmp_settings_file, ysrig_install_dir)

        os.remove(tmp_settings_file)
        self.parent.show_update_success_page()


class UpdateSuccessPage(PageBase):
    def set_button_settings(self):
        self.next_button_label = "OK"

    def dialog(self):
        load_success = False
        if self.parent.install_path == MAYA_MOD_PATH:
            load_success = load_plugin()

        if load_success:
            text = "アップデートが正常に完了しました。\nプラグインは正常に再ロードされました。"
        else:
            text = "アップデートが正常に完了しました。\nプラグインマネージャーから 'ysrig_plugin.py' を再ロードしてください。"

        label = QtWidgets.QLabel(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setFont(font1)
        label.setStyleSheet(f"color: {LABEL_COLOR};")
        self.dialog_layout.addWidget(label)

    def call_next(self):
        self.parent.close()
        self.parent.deleteLater()


# --- ファイル操作関数 ---

def copy_folder(src: str, dst: str):
    dst_path = os.path.join(dst, os.path.basename(src))
    shutil.copytree(src, dst_path)

def get_prefs_dir(ysrig_dir) -> str:
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

def export(file_path, ysrig_dir):
    data = {}
    pref_dir = get_prefs_dir(ysrig_dir)
    mod_dir = os.path.abspath(os.path.join(pref_dir, "modules/"))
    modules = [name for name in os.listdir(mod_dir) if os.path.isdir(os.path.join(mod_dir, name))]
    data["YSRigUserSettingsJSON"] = True
    data["YSRigVersion"] = VERSION

    for mod in modules:
        path = os.path.abspath(os.path.join(mod_dir, f"{mod}/settings/"))
        data[mod] = get_settings(path)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def import_(file_path, ysrig_dir):
    with open(file_path, 'r') as f:
        data: dict = json.load(f)

    modules = list(data.keys())

    ysrig = modules[0]
    ver = data[modules[1]]
    modules = modules[2:]

    pref_dir = get_prefs_dir(ysrig_dir)
    mod_dir = os.path.abspath(os.path.join(pref_dir, "modules/"))

    for mod in modules:
        path = os.path.abspath(os.path.join(mod_dir, f"{mod}/settings/"))
        if not os.path.isdir(path):
            continue

        if mod in data:
            for setting in data[mod]:
                json_path = os.path.abspath(os.path.join(path, f"{setting}.json"))
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data[mod][setting], f, indent=4)


def load_plugin():
    """
    プラグインをアンロードしてから、即時ロードとオートロード設定を試み、
    成功すればTrue、失敗すればFalseを返す。
    """
    try:
        # 1. 既存のプラグインがロードされている場合、アンロードする
        if cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True):
            cmds.unloadPlugin(PLUGIN_NAME)

        # 2. スクリプトパスの追加 (念のため)
        script_path = os.path.join(MAYA_MOD_PATH, "YSRig", "scripts")
        if script_path not in sys.path:
            sys.path.append(script_path)

        # 3. モジュールをスキャンして YSRig.mod を認識させる
        cmds.loadModule(scan=True)
        cmds.loadModule(allModules=True)

        # 4. プラグインのロード
        # (ステップ1でアンロード済みのため、'if'でのチェックは不要)
        cmds.loadPlugin(PLUGIN_NAME)
        
        # 5. オートロードをオンに設定
        cmds.pluginInfo(PLUGIN_NAME, edit=True, autoload=True)

        # 6. 最終確認 (ロードされているか？ AND オートロードがオンか？)
        if not cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True) or not cmds.pluginInfo(PLUGIN_NAME, query=True, autoload=True):
            # どちらかの設定に失敗した場合
            return False
        
        # すべての処理が完了した場合
        return True

    except Exception:
        # 例外が発生した場合（ロード失敗）
        return False


def onMayaDroppedPythonFile(*args, **kwargs):
    win = Window()
    win.show()