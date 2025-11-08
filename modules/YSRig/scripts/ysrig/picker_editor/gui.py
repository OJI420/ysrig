from __future__ import annotations

import os
import json
import math
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal
import importlib
from maya import cmds
from ysrig import gui_base, core

if int(gui_base.ver) <= 2024:
    from PySide2 import QtWidgets, QtCore, QtGui
    IS_PYSIDE6 = False
elif int(gui_base.ver) >= 2025:
    from PySide6 import QtWidgets, QtCore, QtGui
    IS_PYSIDE6 = True


if IS_PYSIDE6:
    QUndoCommand = QtGui.QUndoCommand
    QUndoStack = QtGui.QUndoStack
    QAction = QtGui.QAction
    ITEM_SELECTED_CHANGE = QtWidgets.QGraphicsItem.GraphicsItemChange.ItemSelectedChange
    RESIZE_STRETCH = QtWidgets.QHeaderView.ResizeMode.Stretch
    NO_BUTTONS = QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
    WINDOW_MINIMIZED = QtCore.Qt.WindowMinimized
    WINDOW_NO_STATE = QtCore.Qt.WindowNoState
    SCROLLBAR_ALWAYS_OFF = QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    QMESSAGEBOX_YES = QtWidgets.QMessageBox.StandardButton.Yes
    QMESSAGEBOX_NO = QtWidgets.QMessageBox.StandardButton.No
    QSCREEN = QtGui.QGuiApplication.primaryScreen


else:
    QUndoCommand = QtWidgets.QUndoCommand
    QUndoStack = QtWidgets.QUndoStack
    QAction = QtWidgets.QAction
    ITEM_SELECTED_CHANGE = QtWidgets.QGraphicsItem.ItemSelectedChange
    RESIZE_STRETCH = QtWidgets.QHeaderView.Stretch
    NO_BUTTONS = QtWidgets.QAbstractSpinBox.NoButtons
    WINDOW_MINIMIZED = QtCore.Qt.WindowMinimized
    WINDOW_NO_STATE = QtCore.Qt.WindowNoState
    SCROLLBAR_ALWAYS_OFF = QtCore.Qt.ScrollBarAlwaysOff
    QMESSAGEBOX_YES = QtWidgets.QMessageBox.Yes
    QMESSAGEBOX_NO = QtWidgets.QMessageBox.No
    QSCREEN = QtWidgets.QApplication.desktop


TITLE = "Picker Editor"
OBJ = f"YS_{TITLE}_Gui"
THIS_FILE_PATH = os.path.abspath(__file__)
PREFS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "prefs"))
JSON_PATH = os.path.join(PREFS_PATH, "ysrig", "button_shape.json")
TLRT_SPIN_STEP = 10
SC_SPIN_STEP = 0.1


@dataclass
class ButtonData:
    name: str
    shape_points: List[List[float]]
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    color: Optional[str] = None
    child_modules: Optional[List["PickerModuleData"]] = None
    hide_attr: Optional[Dict[str, int]] = None
    hide_type: Optional[int] = None

@dataclass
class PickerModuleData:
    name: str
    buttons: List[ButtonData]
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    rotation: float = 0.0
    scale: float = 1.0
    flip_h: bool = False
    flip_v: bool = False
    mirror: bool = False
    side: Optional[Literal["L", "R"]] = None
    scripts: Optional[Dict[str, str]] = None


class TransformModuleCommand(QUndoCommand):
    """モジュールの変形を記録するためのアンドゥコマンド"""
    def __init__(self, module_item, description):
        super().__init__(description)
        self.module_item = module_item
        self.editor = module_item.editor

        self.before_props = {
            "tx": self.module_item.tx, "ty": self.module_item.ty,
            "rotation": self.module_item.rotation, "scale": self.module_item.scale,
            "flip_h": self.module_item.flip_h, "flip_v": self.module_item.flip_v,
        }
        self.after_props = {}

    def capture_after_state(self):
        self.after_props = {
            "tx": self.module_item.tx, "ty": self.module_item.ty,
            "rotation": self.module_item.rotation, "scale": self.module_item.scale,
            "flip_h": self.module_item.flip_h, "flip_v": self.module_item.flip_v,
        }

    def undo(self):
        for key, value in self.before_props.items():
            setattr(self.module_item, key, value)
        self.module_item.update_transform_from_properties()
        self.module_item.clamp_to_scene()
        self.editor._output_module_data(self.module_item)


    def redo(self):
        for key, value in self.after_props.items():
            setattr(self.module_item, key, value)
        self.module_item.update_transform_from_properties()
        self.module_item.clamp_to_scene()
        self.editor._output_module_data(self.module_item)

class VisibilityCommand(QUndoCommand):
    """モジュールの表示/非表示を記録するコマンド"""
    def __init__(self, module_item, tree_item, is_visible, description):
        super().__init__(description)
        self.module_item = module_item
        self.tree_item = tree_item
        self.editor = module_item.editor
        self.before_state = self.module_item.isVisible()
        self.after_state = is_visible

    def undo(self):
        self.editor.outliner.blockSignals(True)
        self.module_item.setVisible(self.before_state)
        check_state = QtCore.Qt.Checked if self.before_state else QtCore.Qt.Unchecked
        self.tree_item.setCheckState(0, check_state)
        self.editor.outliner.blockSignals(False)

    def redo(self):
        self.editor.outliner.blockSignals(True)
        self.module_item.setVisible(self.after_state)
        check_state = QtCore.Qt.Checked if self.after_state else QtCore.Qt.Unchecked
        self.tree_item.setCheckState(0, check_state)
        self.editor.outliner.blockSignals(False)

class LockCommand(QUndoCommand):
    """モジュールのロック状態を記録するコマンド"""
    def __init__(self, module_item, tree_item, is_locked, description):
        super().__init__(description)
        self.module_item = module_item
        self.tree_item = tree_item
        self.editor = module_item.editor
        self.before_state = self.module_item.is_locked
        self.after_state = is_locked

    def undo(self):
        self.editor.outliner.blockSignals(True)
        self.module_item.set_locked(self.before_state)
        check_state = QtCore.Qt.Checked if self.before_state else QtCore.Qt.Unchecked
        self.tree_item.setCheckState(1, check_state)
        self.editor.outliner.blockSignals(False)
        self.editor.update_transform_ui()

    def redo(self):
        self.editor.outliner.blockSignals(True)
        self.module_item.set_locked(self.after_state)
        check_state = QtCore.Qt.Checked if self.after_state else QtCore.Qt.Unchecked
        self.tree_item.setCheckState(1, check_state)
        self.editor.outliner.blockSignals(False)
        self.editor.update_transform_ui()


class PickerButtonItem(QtWidgets.QGraphicsPathItem):
    DEFAULT_COLOR = QtGui.QColor("#3498db")
    SELECTED_COLOR = QtGui.QColor("#00ff1e")

    def __init__(self, button_data: ButtonData, parent=None):
        super().__init__(parent)

        path = QtGui.QPainterPath()
        if not button_data.shape_points:
            pass
        else:
            try:
                start_point = button_data.shape_points[0]
                if isinstance(start_point, (list, tuple)) and len(start_point) >= 2:
                    path.moveTo(start_point[0], start_point[1])

                for point in button_data.shape_points[1:]:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        path.lineTo(point[0], point[1])
            except (IndexError, TypeError) as e:
                path = QtGui.QPainterPath()

        self.setPath(path)

        if button_data.color:
            self.color_default = QtGui.QColor(button_data.color)
        else:
            self.color_default = self.DEFAULT_COLOR
        
        self.color_selected = self.SELECTED_COLOR

        self.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        self.set_display_state("default")

    def set_display_state(self, state: str):
        if state == "selected":
            self.setBrush(self.color_selected)
        else:
            self.setBrush(self.color_default)


class PickerModuleItem(QtWidgets.QGraphicsItemGroup):
    MIN_SCALE = 0.1
    MAX_SCALE = 2.0

    def __init__(self, module_data: PickerModuleData, editor: "GraphicsEditor", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_data = module_data
        self.editor = editor
        self.is_locked = False
        self.child_buttons = []

        self.tx = module_data.position.get("x", 0)
        self.ty = module_data.position.get("y", 0)
        self.rotation = module_data.rotation
        self.scale = module_data.scale
        self.flip_h = module_data.flip_h
        self.flip_v = module_data.flip_v

        self.mode = "none"
        self.mouse_press_pos = None
        self.undo_command = None
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)

    def update_transform_from_properties(self, update_ui=True):
        t = QtGui.QTransform()
        t.translate(self.tx, self.ty)
        t.rotate(self.rotation)
        scale_x = -self.scale if self.flip_h else self.scale
        scale_y = -self.scale if self.flip_v else self.scale
        t.scale(scale_x, scale_y)
        self.setTransform(t)
        if update_ui and self.editor and self.isSelected():
            self.editor.update_transform_ui()

    def set_locked(self, locked: bool):
        self.is_locked = locked

    def add_button(self, button: PickerButtonItem):
        self.child_buttons.append(button)
        self.addToGroup(button)

    def update_child_colors(self):
        state = "default"
        if self.isSelected():
            state = "selected"
        for button in self.child_buttons:
            button.set_display_state(state)

    def clamp_to_scene(self):
        if not self.scene():
            return
        item_scene_rect = self.sceneBoundingRect()
        scene_rect = self.scene().sceneRect()
        dx = 0
        if item_scene_rect.left() < scene_rect.left():
            dx = scene_rect.left() - item_scene_rect.left()
        elif item_scene_rect.right() > scene_rect.right():
            dx = scene_rect.right() - item_scene_rect.right()
        dy = 0
        if item_scene_rect.top() < scene_rect.top():
            dy = scene_rect.top() - item_scene_rect.top()
        elif item_scene_rect.bottom() > scene_rect.bottom():
            dy = scene_rect.bottom() - item_scene_rect.bottom()
        if dx != 0 or dy != 0:
            self.tx += dx
            self.ty += dy
            self.update_transform_from_properties()

    def world_flip_horizontal(self):
        self.tx = -self.tx
        self.rotation = -self.rotation
        self.flip_h = not self.flip_h
        self.update_transform_from_properties()

    def world_flip_vertical(self):
        self.ty = -self.ty
        self.rotation = -self.rotation
        self.flip_v = not self.flip_v
        self.update_transform_from_properties()

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        
        was_selected = self.isSelected()
        scene_had_multiple_selection = len(self.scene().selectedItems()) > 1

        is_shift_pressed = event.modifiers() & QtCore.Qt.ShiftModifier

        if is_shift_pressed:
            self.setSelected(not self.isSelected())
        else:
            if not was_selected or scene_had_multiple_selection:
                self.scene().clearSelection()
                self.setSelected(True)
        
        event.accept()
        if was_selected and self.isSelected() and not self.is_locked:
            if event.button() == QtCore.Qt.LeftButton:
                self.mode = "move"
            elif event.button() == QtCore.Qt.RightButton:
                self.mode = "rotate"
            elif event.button() == QtCore.Qt.MiddleButton:
                self.mode = "scale"
            else:
                return

            self.mouse_press_pos = event.scenePos()
            self.undo_command = TransformModuleCommand(self, f"Start {self.mode}")
        else:
            self.mode = "none"
            self.undo_command = None


    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if self.mode == "none":
            super().mouseMoveEvent(event)
            return
        if not self.undo_command:
            return

        initial_props = self.undo_command.before_props
        if self.mode == "move":
            delta = event.scenePos() - self.mouse_press_pos
            self.tx = initial_props["tx"] + delta.x()
            self.ty = initial_props["ty"] + delta.y()
        elif self.mode in ["rotate", "scale"]:
            center_in_scene = QtCore.QPointF(initial_props["tx"], initial_props["ty"])
            if self.mode == "rotate":
                v_start = self.mouse_press_pos - center_in_scene
                v_end = event.scenePos() - center_in_scene
                angle_start = math.atan2(v_start.y(), v_start.x())
                angle_end = math.atan2(v_end.y(), v_end.x())
                angle_delta_deg = math.degrees(angle_end - angle_start)
                self.rotation = initial_props["rotation"] + angle_delta_deg
            elif self.mode == "scale":
                v_start = self.mouse_press_pos - center_in_scene
                dist_start = math.hypot(v_start.x(), v_start.y())
                if dist_start > 0:
                    v_end = event.scenePos() - center_in_scene
                    dist_end = math.hypot(v_end.x(), v_end.y())
                    scale_factor = dist_end / dist_start
                    new_scale = initial_props["scale"] * scale_factor
                    self.scale = max(self.MIN_SCALE, min(self.MAX_SCALE, new_scale))
        self.update_transform_from_properties()
        self.clamp_to_scene()
        event.accept()

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if self.mode != "none" and self.undo_command:
            self.mode = "none"
            self.clamp_to_scene()
            self.undo_command.capture_after_state()
            self.editor.undo_stack.push(self.undo_command)
            self.editor._output_module_data(self)
            self.undo_command = None
            event.accept()
        else:
            if self.mode != "none":
                self.mode = "none"
            self.undo_command = None
            super().mouseReleaseEvent(event)


    def wheelEvent(self, event: QtWidgets.QGraphicsSceneWheelEvent):
        if not self.isSelected() or self.is_locked:
            event.ignore()
            return

        cmd = TransformModuleCommand(self, "Scale")
        delta = event.delta()
        if delta == 0: 
            event.accept()
            return
            
        scale_factor = 1.1 if delta > 0 else 1 / 1.1
        new_scale = self.scale * scale_factor
        if new_scale > self.MAX_SCALE or new_scale < self.MIN_SCALE:
            event.accept()
            return
            
        self.scale = new_scale
        self.update_transform_from_properties()
        self.clamp_to_scene()
        cmd.capture_after_state()
        self.editor.undo_stack.push(cmd)
        self.editor._output_module_data(self)
        event.accept()


    def itemChange(self, change, value):
        if change == ITEM_SELECTED_CHANGE:
            QtCore.QTimer.singleShot(0, self.update_child_colors)
        return super().itemChange(change, value)

    def paint(self, painter: QtGui.QPainter, option, widget=None):
        painter.setBrush(QtCore.Qt.NoBrush)
        if self.isSelected():
            pen = QtGui.QPen(QtGui.QColor(200, 200, 200), 1, QtCore.Qt.DashLine)
        else:
            pen = QtGui.QPen(QtGui.QColor(100, 100, 100), 1, QtCore.Qt.SolidLine)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())


def safe_copy_button_data(original: ButtonData) -> ButtonData:
    """ButtonData を安全にコピーする"""
    new_button = ButtonData(
        name=original.name,
        shape_points=[p.copy() for p in original.shape_points],
        position=original.position.copy(),
        color=original.color,
        child_modules=None
    )
    if original.child_modules:
        new_button.child_modules = [safe_copy_module_data(mod) for mod in original.child_modules]
    elif original.child_modules == []:
        new_button.child_modules = []
    return new_button

def safe_copy_module_data(original: PickerModuleData) -> PickerModuleData:
    """PickerModuleData を安全にコピーする"""
    new_module = PickerModuleData(
        name=original.name,
        buttons=[safe_copy_button_data(btn) for btn in original.buttons],
        position=original.position.copy(),
        rotation=getattr(original, "rotation", 0.0),
        scale=getattr(original, "scale", 1.0),
        flip_h=getattr(original, "flip_h", False),
        flip_v=getattr(original, "flip_v", False),
        mirror=getattr(original, "mirror", False),
        side=getattr(original, "side", None)
    )
    return new_module

def copy_module_transform_only(source: PickerModuleData, target: PickerModuleData):
    """位置・回転・スケール・flipのみコピーし、色などは維持する"""
    target.position = source.position.copy()
    target.rotation = source.rotation
    target.scale = source.scale
    target.flip_h = source.flip_h
    target.flip_v = source.flip_v

    # ボタン構造が同じ場合、子ボタンのpositionだけ同期
    if len(source.buttons) == len(target.buttons):
        for src_btn, tgt_btn in zip(source.buttons, target.buttons):
            tgt_btn.position = src_btn.position.copy()


class GraphicsEditor(QtWidgets.QMainWindow):
    def __init__(self, modules_data: List[PickerModuleData],
                parent_editor: Optional[GraphicsEditor] = None,
                parent_button_data: Optional[ButtonData] = None,
                parent_module_item: Optional[PickerModuleItem] = None,
                is_mirrored_level: bool = False,
                parent=gui_base.maya_main_window):

        actual_parent = parent_editor if parent_editor else parent
        super().__init__(actual_parent)

        if parent_editor:
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.setWindowTitle(TITLE)
        self.setObjectName(OBJ)

        self.active_modules: List[PickerModuleItem] = []
        self.module_to_tree_item_map: Dict[PickerModuleItem, QtWidgets.QTreeWidgetItem] = {}
        self._is_syncing_selection = False
        self.current_selections: List[PickerModuleItem] = []
        self.undo_stack = QUndoStack(self)
        self.view_size = 1000
        self.panel_width = 375
        self.statusBar().setSizeGripEnabled(False)


        self.module_pairs: Dict[PickerModuleItem, PickerModuleItem] = {}
        self.name_to_module_map: Dict[str, PickerModuleItem] = {}

        self.child_editor_window: Optional[GraphicsEditor] = None
        self.parent_editor = parent_editor
        self.parent_button_data = parent_button_data
        self.parent_module_item = parent_module_item
        self.is_mirrored_level = is_mirrored_level

        self.modules_data: List[PickerModuleData] = []


        self._create_menu()
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._setup_scene_and_view(main_layout)

        control_panel = QtWidgets.QWidget()
        control_panel.setFixedWidth(self.panel_width)
        control_panel.setStyleSheet("background-color: #2c3e50; color: #ecf0f1;")
        panel_layout = QtWidgets.QVBoxLayout(control_panel)
        panel_layout.setContentsMargins(5, 5, 5, 5)

        self._setup_outliner(panel_layout)
        self._setup_transform_controls(panel_layout)
        main_layout.addWidget(control_panel)

        self.setCentralWidget(main_widget)

        if not self.parent_editor:
            QtCore.QTimer.singleShot(0, self._adjust_fix_and_center)


        is_main_window = self.parent_editor is None
        data_copy = [safe_copy_module_data(mod) for mod in modules_data]
        self.load_data(data_copy, apply_auto_flip=is_main_window)

        self.outliner.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.outliner.customContextMenuRequested.connect(self.on_outliner_context_menu)
        self.outliner.itemSelectionChanged.connect(self.on_outliner_selection_changed)
        self.scene.selectionChanged.connect(self.on_scene_selection_changed)
        self.outliner.itemChanged.connect(self.on_outliner_item_changed)

    def _adjust_fix_and_center(self):
        self._adjust_and_fix_size()
        if not self.parent_editor:
            self._center_window()

    def _center_window(self):
        """ウィンドウをプライマリスクリーンの中央に移動する"""
        try:
            screen_geometry = None
            if IS_PYSIDE6:
                screen = QSCREEN()
                if screen:
                    screen_geometry = screen.availableGeometry()
            else:
                desktop = QSCREEN()
                primary_screen_index = desktop.primaryScreen()
                screen_geometry = desktop.availableGeometry(primary_screen_index)

            if screen_geometry:
                window_geometry = self.frameGeometry()
                center_point = screen_geometry.center()
                window_geometry.moveCenter(center_point)
                self.move(window_geometry.topLeft())

        except Exception as e:
            pass

    def _adjust_and_fix_size(self):
        self.adjustSize()
        current_size = self.size()
        self.setFixedSize(current_size)


    def _update_window_title(self):
        if self.parent_module_item:
            self.setWindowTitle(f"{TITLE} - Child Level: {self.parent_module_item.module_data.name}")
        else:
            self.setWindowTitle(TITLE)

    def _setup_scene_and_view(self, main_layout):
        self.scene = QtWidgets.QGraphicsScene(self)
        self.scene.setSceneRect(-self.view_size / 2, -self.view_size / 2, self.view_size, self.view_size)
        background = QtWidgets.QGraphicsRectItem(self.scene.sceneRect())
        background.setBrush(QtGui.QColor(60, 60, 60))
        background.setZValue(-1)
        self.scene.addItem(background)
        guideline_pen = QtGui.QPen(QtGui.QColor(120, 120, 120), 1, QtCore.Qt.DashLine)
        self.scene.addLine(0, -self.view_size / 2, 0, self.view_size / 2, guideline_pen).setZValue(-0.5)
        self.scene.addLine(-self.view_size / 2, 0, self.view_size / 2, 0, guideline_pen).setZValue(-0.5)
        self.view = QtWidgets.QGraphicsView(self.scene, self)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.view.setHorizontalScrollBarPolicy(SCROLLBAR_ALWAYS_OFF)
        self.view.setVerticalScrollBarPolicy(SCROLLBAR_ALWAYS_OFF)
        self.view.setContentsMargins(0,0,0,0)
        self.view.setMinimumSize(self.view_size, self.view_size)
        main_layout.addWidget(self.view)


    def _setup_outliner(self, panel_layout):
        self.outliner = QtWidgets.QTreeWidget()
        self.outliner.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.outliner.setHeaderLabels(["👁", "🔒", "Name"])
        header = self.outliner.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(2, RESIZE_STRETCH)
        self.outliner.setColumnWidth(0, 25)
        self.outliner.setColumnWidth(1, 25)
        self.outliner.setStyleSheet("""
            QTreeWidget { background-color: #34495e; border: 1px solid #2c3e50; font-size: 14px; }
            QTreeWidget::item { padding: 4px; }
            QTreeWidget::item:selected { background-color: #3498db; }
            QHeaderView::section { background-color: #2c3e50; padding: 4px; border: 1px solid #1c2833; }
        """)
        panel_layout.addWidget(self.outliner)

    def load_data(self, modules_data: List[PickerModuleData], apply_auto_flip: bool = True):
        """
        指定されたモジュールデータをロード（またはリロード）する。
        渡される modules_data は既に安全コピーされているものと想定する。
        """
        for item in self.active_modules:
            self.scene.removeItem(item)

        self.active_modules.clear()
        self.module_to_tree_item_map.clear()
        self.current_selections.clear()
        self.module_pairs.clear()
        self.name_to_module_map.clear()
        self.undo_stack.clear() 

        self.modules_data = modules_data

        for mod_data in self.modules_data:
            self.create_module_from_data(mod_data)

        if apply_auto_flip:
            self._find_and_setup_mirror_pairs()
        else:
            self._find_mirror_pairs_only()

        self.populate_outliner()
        self.update_transform_ui()

        self._update_window_title()

        self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)


    def closeEvent(self, event):
        """ウィンドウが閉じるときの処理"""

        if self.parent_editor:
            self._save_child_data_to_parent()

        if not self.parent_editor:
            if self.child_editor_window:
                self.child_editor_window.close()
                self.child_editor_window = None
        else:
            if self.parent_editor.child_editor_window is self:
                self.parent_editor.child_editor_window = None
            self.parent_editor = None
            self.parent_button_data = None
            self.parent_module_item = None

        super().closeEvent(event)


    def _create_menu(self):
        menu_bar = self.menuBar()
        edit_menu = menu_bar.addMenu("&Edit")
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QtGui.QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo_stack.undo)
        self.undo_stack.canUndoChanged.connect(undo_action.setEnabled)
        edit_menu.addAction(undo_action)
        redo_action = QAction("&Redo", self)
        redo_action.setText("&Redo\tCtrl+Y / Ctrl+Shift+Z")
        redo_action.setShortcuts([QtGui.QKeySequence.StandardKey.Redo, QtGui.QKeySequence("Ctrl+Shift+Z")])
        redo_action.triggered.connect(self.undo_stack.redo)
        self.undo_stack.canRedoChanged.connect(redo_action.setEnabled)
        edit_menu.addAction(redo_action)

    def _setup_transform_controls(self, panel_layout: QtWidgets.QVBoxLayout):
        transform_group = QtWidgets.QGroupBox("Transform Controls")
        transform_group.setStyleSheet("""
            QGroupBox { font-size: 14px; border: 1px solid #34495e; border-radius: 4px; margin-top: 1ex; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }
        """)
        transform_layout = QtWidgets.QFormLayout(transform_group)
        transform_layout.setLabelAlignment(QtCore.Qt.AlignRight)
        transform_layout.setContentsMargins(10, 15, 10, 10)
        transform_layout.setSpacing(8)

        self.trans_x_spin = QtWidgets.QDoubleSpinBox()
        self.trans_y_spin = QtWidgets.QDoubleSpinBox()
        self.rot_spin = QtWidgets.QDoubleSpinBox()
        self.scale_spin = QtWidgets.QDoubleSpinBox()

        spin_style = """
            QDoubleSpinBox { background-color: #1c2833; border: 1px solid #34495e; border-radius: 4px; padding: 4px; }
            QDoubleSpinBox:disabled { background-color: #2c3e50; }
        """

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        reset_btn_style = """
            QPushButton { background-color: #95a5a6; color: white; border: none; padding: 4px 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #bdc3c7; }
            QPushButton:pressed { background-color: #7f8c8d; }
            QPushButton:disabled { background-color: #566573; }
        """

        spins = [self.trans_x_spin, self.trans_y_spin, self.rot_spin]
        for spin in spins:
            spin.setRange(-9999, 9999)
            spin.setSingleStep(TLRT_SPIN_STEP)
            spin.setStyleSheet(spin_style)
            spin.setSizePolicy(size_policy)

        self.scale_spin.setRange(PickerModuleItem.MIN_SCALE, PickerModuleItem.MAX_SCALE)
        self.scale_spin.setStyleSheet(spin_style)
        self.scale_spin.setSingleStep(SC_SPIN_STEP)
        self.scale_spin.setSizePolicy(size_policy)

        tx_layout = QtWidgets.QHBoxLayout()
        tx_layout.setContentsMargins(0, 0, 0, 0)
        tx_layout.setSpacing(5)
        self.reset_tx_btn = QtWidgets.QPushButton("Reset")
        self.reset_tx_btn.setStyleSheet(reset_btn_style)
        tx_layout.addWidget(self.trans_x_spin)
        tx_layout.addWidget(self.reset_tx_btn)
        transform_layout.addRow("Translate X:", tx_layout)

        ty_layout = QtWidgets.QHBoxLayout()
        ty_layout.setContentsMargins(0, 0, 0, 0)
        ty_layout.setSpacing(5)
        self.reset_ty_btn = QtWidgets.QPushButton("Reset")
        self.reset_ty_btn.setStyleSheet(reset_btn_style)
        ty_layout.addWidget(self.trans_y_spin)
        ty_layout.addWidget(self.reset_ty_btn)
        transform_layout.addRow("Translate Y:", ty_layout)

        rot_layout = QtWidgets.QHBoxLayout()
        rot_layout.setContentsMargins(0, 0, 0, 0)
        rot_layout.setSpacing(5)
        self.reset_rot_btn = QtWidgets.QPushButton("Reset")
        self.reset_rot_btn.setStyleSheet(reset_btn_style)
        rot_layout.addWidget(self.rot_spin)
        rot_layout.addWidget(self.reset_rot_btn)
        transform_layout.addRow("Rotate:", rot_layout)

        scl_layout = QtWidgets.QHBoxLayout()
        scl_layout.setContentsMargins(0, 0, 0, 0)
        scl_layout.setSpacing(5)
        self.reset_scl_btn = QtWidgets.QPushButton("Reset")
        self.reset_scl_btn.setStyleSheet(reset_btn_style)
        scl_layout.addWidget(self.scale_spin)
        scl_layout.addWidget(self.reset_scl_btn)
        transform_layout.addRow("Scale:", scl_layout)

        btn_style = """
            QPushButton { background-color: #3498db; color: white; border: none; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #5dade2; }
            QPushButton:pressed { background-color: #2e86c1; }
            QPushButton:disabled { background-color: #566573; }
        """
        flip_layout = QtWidgets.QHBoxLayout()
        self.flip_h_btn = QtWidgets.QPushButton("H")
        self.flip_v_btn = QtWidgets.QPushButton("V")
        for btn in [self.flip_h_btn, self.flip_v_btn]:
            btn.setStyleSheet(btn_style)
            flip_layout.addWidget(btn)
        transform_layout.addRow("Local Flip:", flip_layout)

        world_flip_layout = QtWidgets.QHBoxLayout()
        self.world_flip_h_btn = QtWidgets.QPushButton("H")
        self.world_flip_v_btn = QtWidgets.QPushButton("V")
        for btn in [self.world_flip_h_btn, self.world_flip_v_btn]:
            btn.setStyleSheet(btn_style)
            world_flip_layout.addWidget(btn)
        transform_layout.addRow("World Flip:", world_flip_layout)

        self.mirror_btn = QtWidgets.QPushButton("Mirror Module")
        self.mirror_btn.setStyleSheet(btn_style)
        transform_layout.addRow(self.mirror_btn)

        self.enter_child_btn = QtWidgets.QPushButton("Enter Child Level")
        self.enter_child_btn.setStyleSheet(btn_style)
        if not self.parent_editor:
            transform_layout.addRow(self.enter_child_btn)

        panel_layout.addWidget(transform_group)
        panel_layout.addStretch()

        if not self.parent_editor:
            reload_btn_layout = QtWidgets.QHBoxLayout()
            reload_btn_layout.addStretch()
            self.reload_btn = QtWidgets.QPushButton("Reload Data")
            reload_btn_style = """
                QPushButton { background-color: #e67e22; color: white; border: none; padding: 6px 12px; border-radius: 4px; }
                QPushButton:hover { background-color: #f39c12; }
                QPushButton:pressed { background-color: #d35400; }
            """
            self.reload_btn.setStyleSheet(reload_btn_style)
            self.reload_btn.setToolTip("Reload initial module data from source.\nThis will clear all changes and undo history.")
            self.reload_btn.clicked.connect(self.on_reload_clicked)
            reload_btn_layout.addWidget(self.reload_btn)
            panel_layout.addLayout(reload_btn_layout)

        if not self.parent_editor:
            self.enter_child_btn.clicked.connect(self.on_enter_child_level_clicked)

        self.trans_x_spin.valueChanged.connect(lambda val: self.on_transform_value_changed("tx", val))
        self.trans_y_spin.valueChanged.connect(lambda val: self.on_transform_value_changed("ty", val))
        self.rot_spin.valueChanged.connect(lambda val: self.on_transform_value_changed("rotation", val))
        self.scale_spin.valueChanged.connect(lambda val: self.on_transform_value_changed("scale", val))

        self.reset_tx_btn.clicked.connect(self.on_reset_tx_clicked)
        self.reset_ty_btn.clicked.connect(self.on_reset_ty_clicked)
        self.reset_rot_btn.clicked.connect(self.on_reset_rot_clicked)
        self.reset_scl_btn.clicked.connect(self.on_reset_scl_clicked)

        self.flip_h_btn.clicked.connect(self.on_flip_h_clicked)
        self.flip_v_btn.clicked.connect(self.on_flip_v_clicked)
        self.world_flip_h_btn.clicked.connect(self.on_world_flip_h_clicked)
        self.world_flip_v_btn.clicked.connect(self.on_world_flip_v_clicked)
        self.mirror_btn.clicked.connect(self.on_mirror_module_clicked)

    def on_reset_tx_clicked(self):
        """Translate X の値をリセットする"""
        if self.trans_x_spin.isEnabled():
            self.trans_x_spin.setValue(0.0)

    def on_reset_ty_clicked(self):
        """Translate Y の値をリセットする"""
        if self.trans_y_spin.isEnabled():
            self.trans_y_spin.setValue(0.0)

    def on_reset_rot_clicked(self):
        """Rotate の値をリセットする"""
        if self.rot_spin.isEnabled():
            self.rot_spin.setValue(0.0)

    def on_reset_scl_clicked(self):
        """Scale の値をリセットする"""
        if self.scale_spin.isEnabled():
            self.scale_spin.setValue(1.0)

    def on_reload_clicked(self):
        """Reloadボタンがクリックされたときの処理"""
        if self.parent_editor:
            return

        reply = QtWidgets.QMessageBox.question(self, "Confirm Reload",
                                            "データをシーンと同期しますか？\nUndo履歴は削除されます。",
                                            QMESSAGEBOX_YES | QMESSAGEBOX_NO, QMESSAGEBOX_NO)

        if reply == QMESSAGEBOX_YES:
            modules_data = get_shape_data()
            data_copy = [safe_copy_module_data(mod) for mod in modules_data]
            self.load_data(data_copy, apply_auto_flip=True)

    def _output_module_data(self, module_item: PickerModuleItem):
        """指定されたモジュールアイテムの現在の状態を PickerModuleData として出力する"""
        if not module_item:
            return

        buttons_copy = []
        if module_item.module_data.buttons:
            for btn_orig in module_item.module_data.buttons:
                buttons_copy.append(ButtonData(
                    name=btn_orig.name,
                    shape_points=[p.copy() for p in btn_orig.shape_points],
                    position=btn_orig.position.copy(),
                    color=btn_orig.color,
                    child_modules=None
                ))

        current_data = PickerModuleData(
            name=module_item.module_data.name,
            buttons=buttons_copy,
            position={"x": module_item.tx, "y": module_item.ty},
            rotation=module_item.rotation,
            scale=module_item.scale,
            flip_h=module_item.flip_h,
            flip_v=module_item.flip_v,
            mirror=getattr(module_item.module_data, "mirror", False),
            side=getattr(module_item.module_data, "side", None)
        )

    def update_transform_ui(self):
        single_item_selected = len(self.current_selections) == 1
        is_enabled = single_item_selected and not self.current_selections[0].is_locked
        flip_buttons_enabled = bool(self.current_selections)

        is_mirrorable = False
        has_child_level = False

        if single_item_selected:
            selected_module = self.current_selections[0]
            is_mirrorable = selected_module in self.module_pairs

            for btn_data in selected_module.module_data.buttons:
                if btn_data.child_modules is not None:
                    has_child_level = True
                    break

        self.mirror_btn.setEnabled(is_mirrorable)

        if not self.parent_editor:
            self.enter_child_btn.setEnabled(has_child_level and is_enabled)

        self.flip_h_btn.setEnabled(flip_buttons_enabled)
        self.flip_v_btn.setEnabled(flip_buttons_enabled)
        self.world_flip_h_btn.setEnabled(flip_buttons_enabled)
        self.world_flip_v_btn.setEnabled(flip_buttons_enabled)
        widgets_to_update = [self.trans_x_spin, self.trans_y_spin, self.rot_spin, self.scale_spin]
        for w in widgets_to_update:
            w.setEnabled(is_enabled)
        if is_enabled:
            selected_item = self.current_selections[0]
            for spin in widgets_to_update:
                spin.blockSignals(True)
            self.trans_x_spin.setValue(selected_item.tx)
            self.trans_y_spin.setValue(selected_item.ty)
            self.rot_spin.setValue(selected_item.rotation)
            self.scale_spin.setValue(selected_item.scale)
            for spin in widgets_to_update:
                spin.blockSignals(False)
        else:
            for spin in widgets_to_update:
                spin.clear()

    def on_transform_value_changed(self, prop_name, value):
        if len(self.current_selections) == 1 and not self.current_selections[0].is_locked:
            item = self.current_selections[0]
            cmd = TransformModuleCommand(item, f"Edit {prop_name}")
            setattr(item, prop_name, value)
            item.update_transform_from_properties(update_ui=False)
            item.clamp_to_scene()
            cmd.capture_after_state()
            self.undo_stack.push(cmd)
            self._output_module_data(item)

    def on_flip_h_clicked(self):
        if not self.current_selections: return
        self.undo_stack.beginMacro("Local Flip H")
        changed_items = []
        for item in self.current_selections:
            if not item.is_locked:
                cmd = TransformModuleCommand(item, "Local Flip H")
                item.flip_h = not item.flip_h
                item.update_transform_from_properties()
                cmd.capture_after_state()
                self.undo_stack.push(cmd)
                changed_items.append(item)
        self.undo_stack.endMacro()
        for item in changed_items:
            self._output_module_data(item)


    def on_flip_v_clicked(self):
        if not self.current_selections: return
        self.undo_stack.beginMacro("Local Flip V")
        changed_items = []
        for item in self.current_selections:
            if not item.is_locked:
                cmd = TransformModuleCommand(item, "Local Flip V")
                item.flip_v = not item.flip_v
                item.update_transform_from_properties()
                cmd.capture_after_state()
                self.undo_stack.push(cmd)
                changed_items.append(item)
        self.undo_stack.endMacro()
        for item in changed_items:
            self._output_module_data(item)

    def on_world_flip_h_clicked(self):
        if not self.current_selections: return
        self.undo_stack.beginMacro("World Flip H")
        changed_items = []
        for item in self.current_selections:
            if not item.is_locked:
                cmd = TransformModuleCommand(item, "World Flip H")
                item.world_flip_horizontal()
                cmd.capture_after_state()
                self.undo_stack.push(cmd)
                changed_items.append(item)
        self.undo_stack.endMacro()
        for item in changed_items:
            self._output_module_data(item)


    def on_world_flip_v_clicked(self):
        if not self.current_selections: return
        self.undo_stack.beginMacro("World Flip V")
        changed_items = []
        for item in self.current_selections:
            if not item.is_locked:
                cmd = TransformModuleCommand(item, "World Flip V")
                item.world_flip_vertical()
                cmd.capture_after_state()
                self.undo_stack.push(cmd)
                changed_items.append(item)
        self.undo_stack.endMacro()
        for item in changed_items:
            self._output_module_data(item)

    def on_mirror_module_clicked(self):
        if not (len(self.current_selections) == 1 and self.current_selections[0] in self.module_pairs):
            return

        source_module = self.current_selections[0]
        target_module = self.module_pairs[source_module]

        if target_module.is_locked:
            return

        cmd = TransformModuleCommand(target_module, "Mirror Module")

        target_module.tx = -source_module.tx
        target_module.ty = source_module.ty
        target_module.rotation = -source_module.rotation
        target_module.scale = source_module.scale
        target_module.flip_h = not source_module.flip_h
        target_module.flip_v = source_module.flip_v

        target_module.update_transform_from_properties()
        target_module.clamp_to_scene()

        cmd.capture_after_state()
        self.undo_stack.push(cmd)
        self._output_module_data(target_module)

    def _save_child_data_to_parent(self):
        """
        (子ウィンドウでのみ呼び出される想定)
        現在の編集内容を取得し、L基準データに変換して、
        親エディタの対応するボタンデータと、そのミラーボタンデータに保存する。
        """
        if not self.parent_editor or not self.parent_button_data or not self.parent_module_item:
            return

        current_is_mirrored = self.is_mirrored_level
        current_child_data_in_editor = self.get_data_from_modules()

        data_to_save: List[PickerModuleData] = []
        if current_is_mirrored:
            data_to_save = [self._mirror_module_data(d) for d in current_child_data_in_editor]
        else:
            data_to_save = current_child_data_in_editor

        self.parent_button_data.child_modules = [safe_copy_module_data(mod) for mod in data_to_save]

        mirror_parent_item = self.parent_editor.module_pairs.get(self.parent_module_item)

        if mirror_parent_item:
            mirror_plus_button: Optional[ButtonData] = None
            for btn in mirror_parent_item.module_data.buttons:
                if btn.child_modules is not None:
                    mirror_plus_button = btn
                    break

            if mirror_plus_button:
                if mirror_plus_button.child_modules:
                    for src_mod, tgt_mod in zip(data_to_save, mirror_plus_button.child_modules):
                        copy_module_transform_only(src_mod, tgt_mod)
                else:
                    mirror_plus_button.child_modules = [safe_copy_module_data(mod) for mod in data_to_save]

    def on_enter_child_level_clicked(self):
        if not (len(self.current_selections) == 1): return

        source_module_item = self.current_selections[0]
        if source_module_item.is_locked: return

        if self.child_editor_window and self.child_editor_window.isVisible():
            if self.child_editor_window.parent_module_item is not source_module_item:
                self.child_editor_window._save_child_data_to_parent()

        plus_button: Optional[ButtonData] = None
        child_data_list_for_display: List[PickerModuleData] = []
        is_mirrored_level = False

        for btn in source_module_item.module_data.buttons:
            if btn.child_modules is not None:
                plus_button = btn
                break

        if plus_button is None:
            return
        elif plus_button.child_modules is None:
            plus_button.child_modules = []

        mirror_module_item = self.module_pairs.get(source_module_item)

        if source_module_item.module_data.name.startswith("R_"):
            is_mirrored_level = True

        if is_mirrored_level:
            if not plus_button.child_modules and mirror_module_item:
                mirror_plus_button: Optional[ButtonData] = None
                for btn in mirror_module_item.module_data.buttons:
                    if btn.child_modules is not None:
                        mirror_plus_button = btn
                        break

                if mirror_plus_button and mirror_plus_button.child_modules:
                    child_data_list_for_display = [self._mirror_module_data(d) for d in mirror_plus_button.child_modules]
                    plus_button.child_modules = [safe_copy_module_data(mod) for mod in mirror_plus_button.child_modules]
                else:
                    mirror_button_name = mirror_plus_button.name if mirror_plus_button else "N/A"
                    child_data_list_for_display = []
                    plus_button.child_modules = []
            elif plus_button.child_modules:
                child_data_list_for_display = [self._mirror_module_data(d) for d in plus_button.child_modules]
            else:
                child_data_list_for_display = []
        else:
            if not plus_button.child_modules:
                child_data_list_for_display = []
            else:
                child_data_list_for_display = [safe_copy_module_data(mod) for mod in plus_button.child_modules]


        window_title = f"Child Level: {source_module_item.module_data.name}"
        parent_pos = self.pos()
        parent_size = self.size()
        offset_x = int(parent_size.width() * 0.1)
        offset_y = int(parent_size.height() * 0.1)
        child_pos = parent_pos + QtCore.QPoint(offset_x, offset_y)


        if self.child_editor_window is None:
            data_copy = [safe_copy_module_data(mod) for mod in child_data_list_for_display]
            self.child_editor_window = GraphicsEditor(
                modules_data=data_copy,
                parent_editor=self,
                parent_module_item=source_module_item,
                parent_button_data=plus_button,
                is_mirrored_level=is_mirrored_level
            )
            self.child_editor_window.move(child_pos)
            self.child_editor_window.show()
            self.child_editor_window.activateWindow()
        else:
            self.child_editor_window.parent_editor = self
            self.child_editor_window.parent_module_item = source_module_item
            self.child_editor_window.parent_button_data = plus_button
            self.child_editor_window.is_mirrored_level = is_mirrored_level
            data_copy = [safe_copy_module_data(mod) for mod in child_data_list_for_display]
            self.child_editor_window.load_data(data_copy, apply_auto_flip=False)
            self.child_editor_window.move(child_pos)
            self.child_editor_window.show()
            self.child_editor_window.activateWindow()
            self.child_editor_window.raise_()

    def get_data_from_modules(self) -> List[PickerModuleData]:
        """
        現在のシーンのアクティブモジュールの状態を
        PickerModuleDataのリストに変換して返す (常に新しい安全コピーを返す)
        """
        data_list: List[PickerModuleData] = []

        for module_item in self.active_modules:
            new_data = safe_copy_module_data(module_item.module_data)

            new_data.position = {"x": module_item.tx, "y": module_item.ty}
            new_data.rotation = module_item.rotation
            new_data.scale = module_item.scale
            new_data.flip_h = module_item.flip_h
            new_data.flip_v = module_item.flip_v

            data_list.append(new_data)
        return data_list

    def _mirror_module_data(self, data: PickerModuleData) -> PickerModuleData:
        """
        PickerModuleData を安全にコピーし、水平反転させた新しいデータを返す。
        L->R と R->L の両方の変換（可逆的な操作）に対応する。
        """
        new_data = safe_copy_module_data(data)

        original_name = getattr(data, "name", "")
        original_side = getattr(data, "side", None)

        if original_side == "L" and original_name.startswith("L_"):
            new_data.name = "R_" + original_name[2:]
            new_data.side = "R"
        elif original_side == "R" and original_name.startswith("R_"):
            new_data.name = "L_" + original_name[2:]
            new_data.side = "L"

        original_pos = getattr(data, "position", {})
        new_data.position["x"] = -original_pos.get("x", 0)
        new_data.rotation = -getattr(data, "rotation", 0.0)
        new_data.flip_h = not getattr(data, "flip_h", False)
        new_data.flip_v = getattr(data, "flip_v", False)

        return new_data

    def create_module_from_data(self, module_data: PickerModuleData):
        module_item = PickerModuleItem(module_data, self)
        for button_data in module_data.buttons:
            button_item = PickerButtonItem(button_data)
            button_item.setPos(button_data.position["x"], button_data.position["y"])
            module_item.add_button(button_item)

        module_item.update_transform_from_properties(update_ui=False)
        self.scene.addItem(module_item)
        self.active_modules.append(module_item)
        self.name_to_module_map[module_data.name] = module_item

    def _find_mirror_pairs_only(self):
        """
        現在のモジュールリストから対称ペアを検索し、self.module_pairs を設定する。
        mirror=True かつ side が "L"/"R" のモジュールのみを対象とする。
        """
        processed = set()
        self.module_pairs.clear()

        mirror_candidates_L: Dict[str, PickerModuleItem] = {}
        mirror_candidates_R: Dict[str, PickerModuleItem] = {}

        for item in self.active_modules:
            mod_data = item.module_data
            is_mirror = getattr(mod_data, "mirror", False)
            side = getattr(mod_data, "side", None)
            name = getattr(mod_data, "name", "")

            if is_mirror and side == "L":
                mirror_candidates_L[name] = item
            elif is_mirror and side == "R":
                mirror_candidates_R[name] = item

        for l_name, l_item in mirror_candidates_L.items():
            if l_item in processed:
                continue

            if l_name.startswith("L_"):
                expected_r_name = "R_" + l_name[2:]
                r_item = mirror_candidates_R.get(expected_r_name)

                if r_item:
                    self.module_pairs[l_item] = r_item
                    self.module_pairs[r_item] = l_item
                    processed.add(l_item)
                    processed.add(r_item)

    def _find_and_setup_mirror_pairs(self):
        """
        ルートレベルのモジュールから対称ペアを検索・設定し、side="R" のモジュールを反転させる。
        """
        self._find_mirror_pairs_only()

        processed_pairs = set()
        for module, mirror_module in self.module_pairs.items():
            if module in processed_pairs:
                continue

            module_side = getattr(module.module_data, "side", None)
            mirror_side = getattr(mirror_module.module_data, "side", None)

            if module_side == "L" and mirror_side == "R":
                mirror_module.world_flip_horizontal()
                processed_pairs.add(module)
                processed_pairs.add(mirror_module)

    def on_outliner_item_changed(self, item: QtWidgets.QTreeWidgetItem, column: int):
        module_item = item.data(2, QtCore.Qt.UserRole)
        if not module_item: return
        if column == 0:
            is_checked = item.checkState(0) == QtCore.Qt.Checked
            cmd = VisibilityCommand(module_item, item, is_checked, f"Set Visible {is_checked}")
            self.undo_stack.push(cmd)
        elif column == 1:
            is_checked = item.checkState(1) == QtCore.Qt.Checked
            cmd = LockCommand(module_item, item, is_checked, f"Set Lock {is_checked}")
            self.undo_stack.push(cmd)

    def populate_outliner(self):
        self.outliner.blockSignals(True)
        self.outliner.clear()
        self.module_to_tree_item_map.clear()
        for module_item in self.active_modules:
            tree_item = QtWidgets.QTreeWidgetItem(self.outliner)
            tree_item.setText(2, module_item.module_data.name)
            tree_item.setData(2, QtCore.Qt.UserRole, module_item)
            self.module_to_tree_item_map[module_item] = tree_item
            tree_item.setFlags(tree_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            vis_state = QtCore.Qt.Checked if module_item.isVisible() else QtCore.Qt.Unchecked
            tree_item.setCheckState(0, vis_state)
            lock_state = QtCore.Qt.Checked if module_item.is_locked else QtCore.Qt.Unchecked
            tree_item.setCheckState(1, lock_state)
        self.outliner.blockSignals(False)

    def on_outliner_selection_changed(self):
        if self._is_syncing_selection:
            return
        self._is_syncing_selection = True
        self.scene.blockSignals(True)
        for item in self.scene.selectedItems():
            item.setSelected(False)
        selected_tree_items = self.outliner.selectedItems()
        for tree_item in selected_tree_items:
            module_item = tree_item.data(2, QtCore.Qt.UserRole)
            if module_item:
                module_item.setSelected(True)
        self.scene.blockSignals(False)
        self._is_syncing_selection = False
        self.current_selections = self.scene.selectedItems()
        self.update_transform_ui()

    def on_scene_selection_changed(self):
        if self._is_syncing_selection:
            return
        self._is_syncing_selection = True
        self.outliner.blockSignals(True)
        self.outliner.clearSelection()
        self.current_selections = self.scene.selectedItems()
        for module_item in self.current_selections:
            if module_item in self.module_to_tree_item_map:
                tree_item = self.module_to_tree_item_map[module_item]
                tree_item.setSelected(True)
        self.outliner.blockSignals(False)
        self._is_syncing_selection = False
        self.update_transform_ui()

    def on_outliner_context_menu(self, point):
        menu = QtWidgets.QMenu(self.outliner)
        has_selection = bool(self.outliner.selectedItems())
        show_selection_action = menu.addAction("Show Selection")
        show_selection_action.triggered.connect(self.show_selection)
        show_selection_action.setEnabled(has_selection)
        show_inverse_action = menu.addAction("Show Inverse Selection")
        show_inverse_action.triggered.connect(self.show_inverse_selection)
        show_inverse_action.setEnabled(has_selection)
        show_all_action = menu.addAction("Show All")
        show_all_action.triggered.connect(self.show_all_modules)
        menu.addSeparator()
        hide_selection_action = menu.addAction("Hide Selection")
        hide_selection_action.triggered.connect(self.hide_selection)
        hide_selection_action.setEnabled(has_selection)
        hide_inverse_action = menu.addAction("Hide Inverse Selection")
        hide_inverse_action.triggered.connect(self.hide_inverse_selection)
        hide_inverse_action.setEnabled(has_selection)
        hide_all_action = menu.addAction("Hide All")
        hide_all_action.triggered.connect(self.hide_all_modules)
        menu.addSeparator()
        lock_selection_action = menu.addAction("Lock Selection")
        lock_selection_action.triggered.connect(self.lock_selection)
        lock_selection_action.setEnabled(has_selection)
        lock_inverse_action = menu.addAction("Lock Inverse Selection")
        lock_inverse_action.triggered.connect(self.lock_inverse_selection)
        lock_inverse_action.setEnabled(has_selection)
        lock_all_action = menu.addAction("Lock All")
        lock_all_action.triggered.connect(self.lock_all_modules)
        menu.addSeparator()
        unlock_selection_action = menu.addAction("Unlock Selection")
        unlock_selection_action.triggered.connect(self.unlock_selection)
        unlock_selection_action.setEnabled(has_selection)
        unlock_inverse_action = menu.addAction("Unlock Inverse Selection")
        unlock_inverse_action.triggered.connect(self.unlock_inverse_selection)
        unlock_inverse_action.setEnabled(has_selection)
        unlock_all_action = menu.addAction("Unlock All")
        unlock_all_action.triggered.connect(self.unlock_all_modules)
        menu.exec_(self.outliner.mapToGlobal(point))

    def show_selection(self):
        selected_tree_items = self.outliner.selectedItems()
        if not selected_tree_items: return
        self.undo_stack.beginMacro("Show Selected Modules")
        for tree_item in selected_tree_items:
            module = tree_item.data(2, QtCore.Qt.UserRole)
            if module and not module.isVisible():
                cmd = VisibilityCommand(module, tree_item, True, "Show")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()
        self.on_outliner_selection_changed()

    def hide_selection(self):
        selected_tree_items = self.outliner.selectedItems()
        if not selected_tree_items: return
        self._is_syncing_selection = True
        self.undo_stack.beginMacro("Hide Selected Modules")
        for tree_item in selected_tree_items:
            module = tree_item.data(2, QtCore.Qt.UserRole)
            if module and module.isVisible():
                cmd = VisibilityCommand(module, tree_item, False, "Hide")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()
        self._is_syncing_selection = False
        self.current_selections = [item.data(2, QtCore.Qt.UserRole) for item in self.outliner.selectedItems()]
        self.update_transform_ui()

    def lock_selection(self):
        selected_tree_items = self.outliner.selectedItems()
        if not selected_tree_items: return
        self.undo_stack.beginMacro("Lock Selected Modules")
        for tree_item in selected_tree_items:
            module = tree_item.data(2, QtCore.Qt.UserRole)
            if module and not module.is_locked:
                cmd = LockCommand(module, tree_item, True, "Lock")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def unlock_selection(self):
        selected_tree_items = self.outliner.selectedItems()
        if not selected_tree_items: return
        self.undo_stack.beginMacro("Unlock Selected Modules")
        for tree_item in selected_tree_items:
            module = tree_item.data(2, QtCore.Qt.UserRole)
            if module and module.is_locked:
                cmd = LockCommand(module, tree_item, False, "Unlock")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def _get_inverse_selection(self):
        selected_modules = set(self.current_selections)
        all_modules = set(self.active_modules)
        inverse_selection = all_modules - selected_modules
        return list(inverse_selection)

    def hide_inverse_selection(self):
        inverse_modules = self._get_inverse_selection()
        if not inverse_modules: return
        self.undo_stack.beginMacro("Hide Inverse Selection")
        for module in inverse_modules:
            if module.isVisible():
                tree_item = self.module_to_tree_item_map[module]
                cmd = VisibilityCommand(module, tree_item, False, "Hide Inverse")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def show_inverse_selection(self):
        inverse_modules = self._get_inverse_selection()
        if not inverse_modules: return
        self.undo_stack.beginMacro("Show Inverse Selection")
        for module in inverse_modules:
            if not module.isVisible():
                tree_item = self.module_to_tree_item_map[module]
                cmd = VisibilityCommand(module, tree_item, True, "Show Inverse")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def lock_inverse_selection(self):
        inverse_modules = self._get_inverse_selection()
        if not inverse_modules: return
        self.undo_stack.beginMacro("Lock Inverse Selection")
        for module in inverse_modules:
            if not module.is_locked:
                tree_item = self.module_to_tree_item_map[module]
                cmd = LockCommand(module, tree_item, True, "Lock Inverse")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def unlock_inverse_selection(self):
        inverse_modules = self._get_inverse_selection()
        if not inverse_modules: return
        self.undo_stack.beginMacro("Unlock Inverse Selection")
        for module in inverse_modules:
            if module.is_locked:
                tree_item = self.module_to_tree_item_map[module]
                cmd = LockCommand(module, tree_item, False, "Unlock Inverse")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def show_all_modules(self):
        self.undo_stack.beginMacro("Show All Modules")
        for module in self.active_modules:
            if not module.isVisible():
                tree_item = self.module_to_tree_item_map[module]
                cmd = VisibilityCommand(module, tree_item, True, "Show")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def hide_all_modules(self):
        self.undo_stack.beginMacro("Hide All Modules")
        for module in self.active_modules:
            if module.isVisible():
                tree_item = self.module_to_tree_item_map[module]
                cmd = VisibilityCommand(module, tree_item, False, "Hide")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def lock_all_modules(self):
        self.undo_stack.beginMacro("Lock All Modules")
        for module in self.active_modules:
            if not module.is_locked:
                tree_item = self.module_to_tree_item_map[module]
                cmd = LockCommand(module, tree_item, True, "Lock")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def unlock_all_modules(self):
        self.undo_stack.beginMacro("Unlock All Modules")
        for module in self.active_modules:
            if module.is_locked:
                tree_item = self.module_to_tree_item_map[module]
                cmd = LockCommand(module, tree_item, False, "Unlock")
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def showEvent(self, event: QtGui.QShowEvent):
        super().showEvent(event)

# ------------------------------------------------------------------------------
# 外部データ定義（★修正★）
# ------------------------------------------------------------------------------
def get_sample_data():
    """
    外部データ（サンプル）を生成して返す関数。
    ミラーリング対象モジュールに mirror=True と side="L"/"R" を設定。
    shape_points を List[List[float]] 形式に変更。
    """

    # --- 指モジュールのサンプルデータ ---
    def create_finger_module(name_prefix: str) -> PickerModuleData:
        side = None
        if name_prefix.startswith("L_"):
            side = "L"
        elif name_prefix.startswith("R_"):
            side = "R"

        # ★ 修正: shape_points 形式
        shape = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        btn1 = ButtonData(name=f"{name_prefix}_1", shape_points=shape, position={"x": 0, "y": 0})
        btn2 = ButtonData(name=f"{name_prefix}_2", shape_points=shape, position={"x": 0, "y": -15})
        btn3 = ButtonData(name=f"{name_prefix}_3", shape_points=shape, position={"x": 0, "y": -30})
        return PickerModuleData(name=f"{name_prefix}", buttons=[btn1, btn2, btn3], mirror=True, side=side)


    L_thumb_mod = create_finger_module("L_Thumb")
    L_thumb_mod.position = {"x": -50, "y": 0}
    L_index_mod = create_finger_module("L_Index")
    L_index_mod.position = {"x": -20, "y": -20}
    L_middle_mod = create_finger_module("L_Middle")
    L_middle_mod.position = {"x": 10, "y": -25}
    L_ring_mod = create_finger_module("L_Ring")
    L_ring_mod.position = {"x": 40, "y": -20}
    L_pinky_mod = create_finger_module("L_Pinky")
    L_pinky_mod.position = {"x": 70, "y": 0}

    # ★ 修正: shape_points 形式
    plus_shape = [[-5, -1], [5, -1], [5, 1], [-5, 1], [-5, -1], [-1, -5], [1, -5], [1, 5], [-1, 5], [-1, -5]]

    L_finger_plus_btn = ButtonData(
        name="L_Finger_Expand",
        shape_points=plus_shape, # ★ 修正
        position={"x": 0, "y": 0},
        color="#f1c40f",
        child_modules=[L_thumb_mod, L_index_mod, L_middle_mod, L_ring_mod, L_pinky_mod]
    )

    mod_L_finger = PickerModuleData(name="L_Finger", position={"x": -150, "y": -100}, buttons=[L_finger_plus_btn], mirror=True, side="L")

    R_finger_plus_btn = ButtonData(
        name="R_Finger_Expand",
        shape_points=plus_shape, # ★ 修正
        position={"x": 0, "y": 0},
        color="#f1c40f",
        child_modules=[]
    )
    mod_R_finger = PickerModuleData(name="R_Finger", position={"x": -150, "y": -100}, buttons=[R_finger_plus_btn], mirror=True, side="R")


    # --- 既存のサンプルデータ ---
    # ★ 修正: shape_points 形式
    mod1_btn = ButtonData(name="s", shape_points=[[0, 0], [40, 0], [40, 40], [0, 40], [0, 0]], position={"x": 0, "y": 0}, color="#e74c3c")
    mod2_btn = ButtonData(name="e", shape_points=[[30, 0], [0, -30], [70, -30], [40, 0], [30, 0]], position={"x": 0, "y": 0}, color="#2ecc71")
    mod_asym_btn = ButtonData(name="L_shape", shape_points=[[0, 0], [80, 0], [80, 20], [20, 20], [20, 80], [0, 80], [0, 0]], position={"x": 0, "y": 0})
    mod1 = PickerModuleData(name="sh_module_01", position={"x": -400, "y": -150}, buttons=[mod1_btn])
    mod2 = PickerModuleData(name="sh_module_02", position={"x": 100, "y": 100}, buttons=[mod2_btn])
    mod_asymmetric = PickerModuleData(name="asymmetric_module", position={"x": -60, "y": -40}, buttons=[mod_asym_btn])
    mod17 = PickerModuleData(name="sh", position={"x": -400, "y": 350}, buttons=[
        ButtonData(name="s", shape_points=[[0, 0], [40, 0], [40, 40], [0, 40], [0, 0]], position={"x": 0, "y": 0}, color="#e74c3c"),
        ButtonData(name="u", shape_points=[[0, 10], [60, 5], [60, 35], [0, 30], [0, 10]], position={"x": 50, "y": 0}, color="#f1c40f")
    ])

    arm_btn_shape = [[0, 0], [50, 0], [50, 20], [0, 20], [0, 0]]
    L_arm_btn = ButtonData(name="L_arm_ctrl", shape_points=arm_btn_shape, color="#e74c3c")
    R_arm_btn = ButtonData(name="R_arm_btn", shape_points=arm_btn_shape, color="#3498db")

    mod_L_arm = PickerModuleData(name="L_Arm", position={"x": -300, "y": 50}, buttons=[L_arm_btn], mirror=True, side="L")
    mod_R_arm = PickerModuleData(name="R_Arm", position={"x": -300, "y": 50}, buttons=[R_arm_btn], mirror=True, side="R")


    modules_list = [
        mod1, mod2, mod_asymmetric, mod17,
        mod_L_arm, mod_R_arm,
        mod_L_finger, mod_R_finger
    ]
    return modules_list


def get_shape_data():
    with open(JSON_PATH, "r") as f:
        data = json.load(f)

    modules_list = []

    #meta_nodes = core.get_meta_nodes()
    meta_nodes = ["Meta_Root", "Meta_Spine", "Meta_Neck", "Meta_L_Arm", "Meta_L_Finger", "Meta_L_Leg"]
    for meta in meta_nodes:
        module = cmds.getAttr(f"{meta}.Module")
        module = importlib.import_module(f"ysrig.modules.{module}.picker")
        func = getattr(module, "main")
        modules_list += func(data[cmds.getAttr(f"{meta}.Module")]["default"], meta)

    return modules_list


def main():
    existing_window = None
    app = QtWidgets.QApplication.instance()
    if app:
        for widget in app.allWidgets():
            if widget.objectName() == OBJ and isinstance(widget, QtWidgets.QMainWindow):
                existing_window = widget
                break

    if existing_window:
        current_state = existing_window.windowState()
        is_visible = existing_window.isVisible()

        if current_state & WINDOW_MINIMIZED or not is_visible:
            if current_state & WINDOW_MINIMIZED:
                existing_window.setWindowState(current_state & ~WINDOW_MINIMIZED | WINDOW_NO_STATE)

            existing_window.show()
            existing_window.activateWindow()
            existing_window.raise_()
            return existing_window

        else:
            existing_window.activateWindow()
            existing_window.raise_()
            return existing_window


    # 既存ウィンドウがない場合
    modules_data = get_shape_data()
    initial_data_copy = [safe_copy_module_data(mod) for mod in modules_data]
    editor_instance = GraphicsEditor(modules_data=initial_data_copy, parent_editor=None)
    editor_instance.show()
    return editor_instance