import os
import inspect
import importlib
import winsound
from maya import cmds
from maya.api.OpenMaya import MGlobal
from ysrig import gui_base, core
from ysrig import skeleton_base, ctrl_base, rig_base
importlib.reload(gui_base)
importlib.reload(core)

if int(gui_base.ver) <= 2024:
    from PySide2 import QtWidgets, QtCore

elif int(gui_base.ver) >= 2025:
    from PySide6 import QtWidgets, QtCore


def get_style(bc:str, sc:str) -> str:
    base = [float(c) for c in bc.split(", ")]
    hover = [float(c)+10 for c in bc.split(", ")]
    pressed = [float(c)-10 for c in bc.split(", ")]
    style = f"""
        QPushButton {{
            background-color: rgb({base[0]}, {base[1]}, {base[2]});
            color: rgb({sc});
            border-radius: 15px;
            padding: 5px;
        }}
        QPushButton:hover {{
            background-color: rgb({hover[0]}, {hover[1]}, {hover[2]});
        }}
        QPushButton:pressed {{
            background-color: rgb({pressed[0]}, {pressed[1]}, {pressed[2]});
        }}
        """
    return style


class Gui(QtWidgets.QWidget):
    def __init__(self):
        super().__init__(gui_base.maya_main_window)
        self._setup()
        self._get_module_name()
        self.pre_close()
        self.window()
        self.add_help()
        self.gui()
        self.build_manager()
        self.add_widget()
        self.reload()

        self._app = QtWidgets.QApplication.instance()
        self._app.aboutToQuit.connect(self.save_window_settings_registry)
        self.load_window_settings_registry()

    def _setup(self):
        self.ysrig_window = True
        self.module_name = ""
        self.title = "Build Manager"
        self.file_path = ""
        self.dir_path = ""
        self.facial_root_joint = cmds.getAttr(f"{core.GUIDE_FACIALS_GROUP_NAME}.FacialRootName")
        self.help_window = None
        self.pre_widget = {}
        self.widget = {}
        self.build_widget = {}
        self.dyn_widget = {}

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
        self.setMinimumWidth(800)
        self.setStyleSheet(f"background-color: rgb({gui_base.WINDOW_COLOR_1});")

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(3)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.layout1 = QtWidgets.QHBoxLayout(self)
        self.layout1.setSpacing(10)
        self.layout2 = QtWidgets.QVBoxLayout(self)
        self.layout2.setSpacing(10)
        self.layout3 = QtWidgets.QVBoxLayout(self)
        self.layout3.setSpacing(10)
        self.layout3.setAlignment(QtCore.Qt.AlignTop)

        self.layout1.addLayout(self.layout2)
        self.layout1.addLayout(self.layout3)

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

        frame = Guide_Frame("Guide", core.GUIDE_GROUP_NAME, None, remove_guide)
        self.main_layout.addWidget(frame)

    def help(self):
        self.help_window = gui_base.YSHelpWindow(self)
        self.help_window.show()

    def gui(self):
        self.main_layout.addLayout(self.layout1)
        self.widget["FacialRoot"] = FacialParentList(self, label="Facial Root Joint")
        self.widget["FacialRoot"].set(self.facial_root_joint)
        self.widget["FacialRoot"].line_edit.textChanged.connect(self.set_facial_root)
        self.widget["ModuleList"] = ListWidget(self, "Module List")
        self.widget["ModuleList"].list_widget.currentItemChanged.connect(self.reload)

    def parent_list(self):
        name = self.widget["ModuleList"].get()
        self.meta_node = f'Meta_{name}'

        self.dyn_widget["Frame1"] = gui_base.YSFrame(label="Settings")
        self.dyn_widget["ModuelName"] = gui_base.YSLineEdit(label="GroupName")
        self.dyn_widget["ModuelName"].set(name)
        self.dyn_widget["ModuelName"].line_edit.setEnabled(False)

        if not cmds.objExists(self.meta_node):
            return

        parent = cmds.getAttr(f"{self.meta_node}.ParentName")
        if parent == "Facial":
            return

        self.dyn_widget["ParentName"] = ParentList(self, label="ParentName")
        self.dyn_widget["ParentName"].set(parent)
        self.dyn_widget["ParentName"].line_edit.textChanged.connect(self.set_parent)

    def dyn_gui(self):
        attrs = []
        self.settings_node = f'Guide_{self.widget["ModuleList"].get()}_Settings'
        if not cmds.objExists(self.settings_node):
            return

        for attr in cmds.listAttr(self.settings_node, userDefined=True):
            if attr == "MetaNode":
                continue

            if cmds.getAttr(f"{self.settings_node}.{attr}", k=True):
                attrs += [attr]

        for attr in attrs:
            full_attr = f"{self.settings_node}.{attr}"
            attr_type =  cmds.getAttr(full_attr, type=True)

            if attr_type == "enum":
                enum_str = cmds.addAttr(full_attr, q=True, enumName=True)
                self.dyn_widget[attr] = gui_base.YSComboBox(attr, items=enum_str.split(":"))
                self.dyn_widget[attr].set(cmds.getAttr(full_attr))

            elif attr_type == "bool":
                self.dyn_widget[attr] = gui_base.YSCheckBox(attr)
                self.dyn_widget[attr].set(cmds.getAttr(full_attr))

            elif attr_type == "double" or attr_type == "long":
                range = [False, False]
                decimals = 3
                step = 0.1

                if cmds.attributeQuery(attr, node=self.settings_node, minExists=True):
                    range[0] = cmds.attributeQuery(attr, node=self.settings_node, minimum=True)[0]

                if cmds.attributeQuery(attr, node=self.settings_node, maxExists=True):
                    range[1] = cmds.attributeQuery(attr, node=self.settings_node, maximum=True)[0]

                if attr_type == "long":
                    decimals = 0
                    step = 1

                self.dyn_widget[attr] = gui_base.YSDoubleSpinBox(attr, range=range, decimals=decimals, step=step)
                self.dyn_widget[attr].set(cmds.getAttr(full_attr))

            self.dyn_widget[attr].connect(lambda _, a=attr, w=self.dyn_widget[attr]: self.set_setting(w, a))

    def build_manager(self):
        self.build_widget["Skeleton"] = BuildManager("Skeleton", core.SKELETON_GROUP_NAME, build_skeleton, remove_skeleton)
        self.build_widget["Controller"] = BuildManager("Controller", core.CTRL_EDIT_GROUP_NAME, build_controller, remove_controller)
        self.build_widget["Rig"] = BuildManager("Rig", core.RIG_GROUP_NAME,build_rig, remove_rig)

    def add_widget(self):
        for w in self.widget:
            self.layout2.addWidget(self.widget[w])

        for w in self.build_widget:
            self.main_layout.addWidget(self.build_widget[w])

    def add_dyn_widget(self):
        for w in self.dyn_widget:
            self.layout3.addWidget(self.dyn_widget[w])

    def delete_dyn_widget(self):
        for w in self.dyn_widget:
            self.layout3.removeWidget(self.dyn_widget[w])
            self.dyn_widget[w].setParent(None)
            self.dyn_widget[w].deleteLater()

        self.dyn_widget = {}

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
        self.save_window_settings_registry()
        if self.help_window:
            self.help_window.close()

    def reload(self):
        self.delete_dyn_widget()
        self.parent_list()
        self.dyn_gui()
        self.add_dyn_widget()

    def set_setting(self, widget, attr):
        value = widget.get()
        cmds.setAttr(f"{self.settings_node}.{attr}", value)

    def set_parent(self):
        text = self.dyn_widget["ParentName"].get()
        cmds.setAttr(f"{self.meta_node}.ParentName", l=False)
        cmds.setAttr(f"{self.meta_node}.ParentName", text, l=True, type="string")

    def set_facial_root(self):
        text = self.widget["FacialRoot"].get()
        cmds.setAttr(f"{core.GUIDE_FACIALS_GROUP_NAME}.FacialRootName", l=False)
        cmds.setAttr(f"{core.GUIDE_FACIALS_GROUP_NAME}.FacialRootName", text, l=True, type="string")


def main():
    if not cmds.objExists(core.GUIDE_GROUP_NAME):
        MGlobal.displayError("ガイドが見つかりませんでした")
        return

    G = Gui()
    G.show()


class ListWidget(gui_base.YSListWidget):
    def __init__(self, parent, label=""):
        super().__init__(label=label)
        self.reload_button = gui_base.YSPushButton("Reload")
        self.reload_button.clicked.connect(self.reset)
        self.main_layout.addWidget(self.reload_button, 1, 1, 1, 2)

        self.parent = parent
        self.get_module()
        self.set_list()
        self.list_widget.itemChanged.connect(self.set_guide_visibility)
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.open_menu)

    def get_module(self):
        self.meta_nodes = core.get_meta_nodes()[1:] + core.get_facial_meta_nodes()
        self.names = [cmds.getAttr(f"{node}.GroupName") for node in self.meta_nodes]

    def set_list(self):
        for name in self.names:
            item = QtWidgets.QListWidgetItem(name)
            guide_group = f"Guide_{name}_Group"

            if cmds.getAttr(f"{guide_group}.visibility"):
                item.setCheckState(QtCore.Qt.Checked)

            else:
                item.setCheckState(QtCore.Qt.Unchecked)

            self.list_widget.addItem(item)

    def reset(self):
        self.list_widget.clear()
        self.get_module()
        self.set_list()

    def set_guide_visibility(self, item: QtWidgets.QListWidgetItem):
        row = self.list_widget.row(item)
        name = self.names[row]
        state = (item.checkState() == QtCore.Qt.Checked)
        cmds.setAttr(f"Guide_{name}_Group.visibility", state)

    def open_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        menu = QtWidgets.QMenu(self)

        if item:
            hide_all = menu.addAction("Hide All")
            show_all = menu.addAction("Show All")
            hide_sel = menu.addAction("Hide Selected")
            show_sel = menu.addAction("Show Selected")
            hide_inverse_sel = menu.addAction("Hide Inverse Selected")
            show_inverse_sel = menu.addAction("Show Inverse Selected")
            delete_sel = menu.addAction("Delete Selected")
            action = menu.exec_(self.list_widget.mapToGlobal(pos))

            sels = self.list_widget.selectedItems()
            items = items = [self.list_widget.item(i) for i in range(self.list_widget.count())]

            if action == hide_all:
                for i in range(self.list_widget.count()):
                    item_ = self.list_widget.item(i)
                    item_.setCheckState(QtCore.Qt.Unchecked)

            elif action == show_all:
                for i in range(self.list_widget.count()):
                    item_ = self.list_widget.item(i)
                    item_.setCheckState(QtCore.Qt.Checked)

            elif action == hide_sel:
                for sel in sels:
                    sel.setCheckState(QtCore.Qt.Unchecked)

            elif action == show_sel:
                for sel in sels:
                    sel.setCheckState(QtCore.Qt.Checked)

            elif action == hide_inverse_sel:
                for item in items:
                    hide = True
                    for sel in sels:
                        if sel == item:
                            hide = False
                            continue

                    if hide:
                        item.setCheckState(QtCore.Qt.Unchecked)

            elif action == show_inverse_sel:
                for item in items:
                    show = True
                    for sel in sels:
                        if sel == item:
                            show = False
                            continue

                    if show:
                        item.setCheckState(QtCore.Qt.Checked)

            elif action == delete_sel:
                message = ""
                for sel in sels:
                    message += f'\n"{sel.text()}"'

                message += "\nを削除しますか？"
                dialog = gui_base.YSWarningDialog(self.parent, "Eelete Moduel", message)
                if dialog.get_result():
                    cmds.undoInfo(ock=True)
                    for sel in sels:
                        core.delete_meta_node(f"Meta_{sel.text()}")
                        cmds.delete(f"Guide_{sel.text()}_Group")

                    cmds.undoInfo(cck=True)
                    self.reset()


class FacialParentList(gui_base.YSParentList):
    def call(self):
        self.module_list = ModuleList1(self.parent, self.line_edit)
        self.module_list.exec()


class ModuleList1(gui_base.YSModuleList):
    def setup(self, parent, line_edit):
        super().setup(parent, line_edit)
        self.facial_meta_nodes = []


class ParentList(gui_base.YSParentList):
    def call(self):
        self.module_list = ModuleList2(self.parent, self.line_edit)
        self.module_list.exec()


class ModuleList2(gui_base.YSModuleList):
    def setup(self, parent, line_edit):
        super().setup(parent, line_edit)
        self.facial_meta_nodes = []
        self.meta_nodes.remove(self.parent.meta_node)


class BuildManager(QtWidgets.QWidget):
    def __init__(self, label, node, build_action, remove_action):
        super().__init__()
        self.node = node
        self.build_action = build_action
        self.remove_action = remove_action
        self.layout = None
        self.widgets = {}
        self.label = label

        self.add_layout()
        self.gui()
        self.add_widget()
        self.set_button_color()

    def add_layout(self):
        self.layout = QtWidgets.QGridLayout(self)

    def gui(self):
        self.widgets["Label"] = gui_base.YSFrame(self.label)

        self.widgets["Visivility"] = gui_base.YSPushButton("Hide")
        self.widgets["Visivility"].setStyleSheet(get_style(gui_base.BUTTON_COLOR_1, gui_base.STR_COLOR_1))
        self.widgets["Visivility"].clicked.connect(self.set_visibility)

        self.widgets["Build"] = gui_base.YSPushButton("Build")
        self.widgets["Build"].setStyleSheet(get_style(gui_base.BUTTON_COLOR_1, gui_base.STR_COLOR_1))
        self.widgets["Build"].clicked.connect(self.build_action)
        self.widgets["Build"].clicked.connect(self.set_button_color)

        self.widgets["Remove"] = gui_base.YSPushButton("Remove")
        self.widgets["Remove"].setStyleSheet(get_style(gui_base.BUTTON_COLOR_1, gui_base.STR_COLOR_1))
        self.widgets["Remove"].clicked.connect(self.remove_action)

    def add_widget(self):
        self.layout.addWidget(self.widgets["Label"], 0, 0, 1, 1)
        self.layout.addWidget(self.widgets["Visivility"], 0, 1, 1, 1)
        self.layout.addWidget(self.widgets["Build"], 0, 2, 1, 1)
        self.layout.addWidget(self.widgets["Remove"], 0, 3, 1, 1)

    def set_visibility(self):
        if not cmds.objExists(self.node):
            return

        value = cmds.getAttr(f"{self.node}.visibility")
        value = not value
        cmds.setAttr(f"{self.node}.visibility", value)
        self.set_button_color()

    def set_button_color(self):
        if not cmds.objExists(self.node):
            return

        value = cmds.getAttr(f"{self.node}.visibility")
        if value:
            self.widgets["Visivility"].setStyleSheet(get_style(gui_base.BUTTON_COLOR_1, gui_base.STR_COLOR_1))
            self.widgets["Visivility"].setText("Hide")

        else:
            self.widgets["Visivility"].setStyleSheet(get_style(gui_base.BUTTON_COLOR_3, gui_base.STR_COLOR_3))
            self.widgets["Visivility"].setText("Show")


class Guide_Frame(BuildManager):
    def gui(self):
        self.widgets["Label"] = gui_base.YSFrame(self.label)

        self.widgets["Visivility"] = gui_base.YSPushButton("Hide")
        self.widgets["Visivility"].setStyleSheet(get_style(gui_base.BUTTON_COLOR_1, gui_base.STR_COLOR_1))
        self.widgets["Visivility"].clicked.connect(self.set_visibility)

        self.widgets["Frame"] = gui_base.YSFrame()

        self.widgets["Remove"] = gui_base.YSPushButton("Remove")
        self.widgets["Remove"].setStyleSheet(get_style(gui_base.BUTTON_COLOR_1, gui_base.STR_COLOR_1))
        self.widgets["Remove"].clicked.connect(self.remove_action)

    def add_widget(self):
        self.layout.addWidget(self.widgets["Label"], 0, 0, 1, 1)
        self.layout.addWidget(self.widgets["Visivility"], 0, 1, 1, 1)
        self.layout.addWidget(self.widgets["Frame"], 0, 2, 1, 1)
        self.layout.addWidget(self.widgets["Remove"], 0, 3, 1, 1)


def build_skeleton():
    if not cmds.objExists(core.GUIDE_GROUP_NAME):
        MGlobal.displayError("ガイドが見つかりませんでした")
        return

    skeleton_base.main()


def build_controller():
    if not cmds.objExists(core.GUIDE_GROUP_NAME):
        MGlobal.displayError("ガイドが見つかりませんでした")
        return

    ctrl_base.main()


def build_rig():
    if not cmds.objExists(core.GUIDE_GROUP_NAME):
        MGlobal.displayError("ガイドが見つかりませんでした")
        return

    if not cmds.objExists(core.SKELETON_GROUP_NAME):
        MGlobal.displayError("スケルトンが見つかりませんでした")
        return

    if not cmds.objExists(core.CTRL_EDIT_GROUP_NAME):
        MGlobal.displayError("コントローラーが見つかりませんでした")
        return

    rig_base.main()


def remove_skeleton():
    if not cmds.objExists(core.SKELETON_GROUP_NAME):
        return

    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    dialog = gui_base.YSConfirmDialog(None, "remove skeleton", "スケルトンを削除しますか？")
    if dialog.get_result():
        cmds.delete(core.SKELETON_GROUP_NAME)


def remove_controller():
    if not cmds.objExists(core.CTRL_EDIT_GROUP_NAME):
        return

    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    dialog = gui_base.YSConfirmDialog(None, "remove controller", "コントローラーを削除しますか？")
    if dialog.get_result():
        cmds.delete(core.CTRL_EDIT_GROUP_NAME)


def remove_rig():
    if not cmds.objExists(core.RIG_GROUP_NAME):
        return

    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    dialog = gui_base.YSConfirmDialog(None, "remove rig", "リグを削除しますか？")
    if dialog.get_result():
        proxies = cmds.ls(core.RIG_GROUP_NAME, type="joint", dag=True)
        proxies = [proxy for proxy in proxies if "Proxy_" in proxy]
        cmds.delete(proxies + [core.RIG_GROUP_NAME])


def remove_guide():
    if not cmds.objExists(core.GUIDE_GROUP_NAME):
        return

    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    dialog = gui_base.YSConfirmDialog(None, "remove guide", "ガイドをすべて削除しますか？")
    if not dialog.get_result():
        return

    #for node in core.get_meta_nodes() + core.get_facial_meta_nodes():
    #    cmds.delete(node)
    cmds.delete(core.GUIDE_GROUP_NAME)