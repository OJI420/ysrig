import sys
import math
from dataclasses import dataclass, field
from typing import List, Dict
from ysrig import gui_base

if int(gui_base.ver) <= 2024:
    from PySide2 import QtWidgets, QtCore, QtGui
    IS_PYSIDE6 = False
elif int(gui_base.ver) >= 2025:
    from PySide6 import QtWidgets, QtCore, QtGui
    IS_PYSIDE6 = True

# --- Compatibility Layer ---
if IS_PYSIDE6:
    QUndoCommand = QtGui.QUndoCommand
    QUndoStack = QtGui.QUndoStack
    QAction = QtGui.QAction
    ITEM_SELECTED_CHANGE = QtWidgets.QGraphicsItem.GraphicsItemChange.ItemSelectedChange
    RESIZE_STRETCH = QtWidgets.QHeaderView.ResizeMode.Stretch
    NO_BUTTONS = QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons

else: # PySide2
    QUndoCommand = QtWidgets.QUndoCommand
    QUndoStack = QtWidgets.QUndoStack
    QAction = QtWidgets.QAction
    ITEM_SELECTED_CHANGE = QtWidgets.QGraphicsItem.ItemSelectedChange
    RESIZE_STRETCH = QtWidgets.QHeaderView.Stretch
    NO_BUTTONS = QtWidgets.QAbstractSpinBox.NoButtons

TITLE = "Picker Editor"

# ------------------------------------------------------------------------------
# データクラス（変更なし）
# ------------------------------------------------------------------------------
@dataclass
class ButtonData:
    name: str
    shape_points: List[Dict[str, float]]
    position: Dict[str, float] = field(default_factory=lambda: {'x': 0, 'y': 0})

@dataclass
class PickerModuleData:
    name: str
    buttons: List[ButtonData]
    position: Dict[str, float] = field(default_factory=lambda: {'x': 0, 'y': 0})

# ------------------------------------------------------------------------------
# アンドゥコマンド（変更なし）
# ------------------------------------------------------------------------------
class TransformModuleCommand(QUndoCommand):
    """モジュールの変形を記録するためのアンドゥコマンド"""
    def __init__(self, module_item, description):
        super().__init__(description)
        self.module_item = module_item
        
        self.before_props = {
            'tx': self.module_item.tx, 'ty': self.module_item.ty,
            'rotation': self.module_item.rotation, 'scale': self.module_item.scale,
            'flip_h': self.module_item.flip_h, 'flip_v': self.module_item.flip_v,
        }
        self.after_props = {}

    def capture_after_state(self):
        self.after_props = {
            'tx': self.module_item.tx, 'ty': self.module_item.ty,
            'rotation': self.module_item.rotation, 'scale': self.module_item.scale,
            'flip_h': self.module_item.flip_h, 'flip_v': self.module_item.flip_v,
        }

    def undo(self):
        for key, value in self.before_props.items():
            setattr(self.module_item, key, value)
        self.module_item.update_transform_from_properties()
        self.module_item.clamp_to_scene()

    def redo(self):
        for key, value in self.after_props.items():
            setattr(self.module_item, key, value)
        self.module_item.update_transform_from_properties()
        self.module_item.clamp_to_scene()

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

# ------------------------------------------------------------------------------
# 任意の形状を描画できるように変更したボタンアイテム（変更なし）
# ------------------------------------------------------------------------------
class PickerButtonItem(QtWidgets.QGraphicsPathItem):
    """
    QGraphicsPathItemを継承し、ButtonDataのshape_pointsから任意の形状を生成する。
    """
    def __init__(self, button_data: ButtonData, parent=None):
        super().__init__(parent)
        
        path = QtGui.QPainterPath()
        for i, command in enumerate(button_data.shape_points):
            if i == 0:
                path.moveTo(*command["pos"])
                continue
            cmd_type = command.get("type", "line")
            if cmd_type == "line":
                path.lineTo(*command["pos"])
            elif cmd_type == "cubic":
                path.cubicTo(
                    QtCore.QPointF(*command["ctrl1"]),
                    QtCore.QPointF(*command["ctrl2"]),
                    QtCore.QPointF(*command["end"])
                )
        self.setPath(path)
        self.color_default = QtGui.QColor("#3498db")
        self.color_selected = QtGui.QColor("#f1c40f")
        self.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        self.set_display_state('default')

    def set_display_state(self, state: str):
        if state == 'selected':
            self.setBrush(self.color_selected)
        else:
            self.setBrush(self.color_default)

# ------------------------------------------------------------------------------
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★ 不安定な動作を修正し、選択処理を安定化させたモジュール ★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
class PickerModuleItem(QtWidgets.QGraphicsItemGroup):
    """
    自身のTransformプロパティを一元管理し、UIとの連携を行うモジュール。
    """
    MIN_SCALE = 0.1
    MAX_SCALE = 2.0

    def __init__(self, module_data: PickerModuleData, editor: "GraphicsEditor", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_data = module_data
        self.editor = editor
        self.is_locked = False
        self.child_buttons = []
        self.tx = module_data.position.get('x', 0)
        self.ty = module_data.position.get('y', 0)
        self.rotation = 0.0
        self.scale = 1.0
        self.flip_h = False
        self.flip_v = False
        self.mode = 'none'
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
        state = 'default'
        if self.isSelected():
            state = 'selected'
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
    
    # ★★★ 修正箇所 ★★★
    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        """
        マウスプレス時のイベント。選択処理を完全に手動で管理し、安定させる。
        """
        # --- 選択処理 ---
        is_shift_pressed = event.modifiers() & QtCore.Qt.ShiftModifier

        if is_shift_pressed:
            # Shiftキーが押されている場合：このアイテムの選択状態を反転させる
            self.setSelected(not self.isSelected())
        else:
            # Shiftキーが押されていない場合：
            selected_items = self.scene().selectedItems()
            # このアイテムだけが選択されている状態でないなら、選択を更新する
            if len(selected_items) != 1 or selected_items[0] is not self:
                # いったん全ての選択を解除
                self.scene().clearSelection()
                # このアイテムだけを選択
                self.setSelected(True)
        
        # --- トランスフォーム処理（ロックされていなければ実行） ---
        if self.is_locked:
            event.accept()
            return

        if event.button() == QtCore.Qt.LeftButton:
            self.mode = 'move'
        elif event.button() == QtCore.Qt.RightButton:
            self.mode = 'rotate'
        elif event.button() == QtCore.Qt.MiddleButton:
            self.mode = 'scale'
        else:
            event.accept()
            return

        self.mouse_press_pos = event.scenePos()
        self.undo_command = TransformModuleCommand(self, "")
        event.accept()


    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if self.mode == 'none':
            super().mouseMoveEvent(event)
            return
        initial_props = self.undo_command.before_props
        if self.mode == 'move':
            delta = event.scenePos() - self.mouse_press_pos
            self.tx = initial_props['tx'] + delta.x()
            self.ty = initial_props['ty'] + delta.y()
        elif self.mode in ['rotate', 'scale']:
            center_in_scene = QtCore.QPointF(initial_props['tx'], initial_props['ty'])
            if self.mode == 'rotate':
                v_start = self.mouse_press_pos - center_in_scene
                v_end = event.scenePos() - center_in_scene
                angle_start = math.atan2(v_start.y(), v_start.x())
                angle_end = math.atan2(v_end.y(), v_end.x())
                angle_delta_deg = math.degrees(angle_end - angle_start)
                self.rotation = initial_props['rotation'] + angle_delta_deg
            elif self.mode == 'scale':
                v_start = self.mouse_press_pos - center_in_scene
                dist_start = math.hypot(v_start.x(), v_start.y())
                if dist_start > 0:
                    v_end = event.scenePos() - center_in_scene
                    dist_end = math.hypot(v_end.x(), v_end.y())
                    scale_factor = dist_end / dist_start
                    new_scale = initial_props['scale'] * scale_factor
                    self.scale = max(self.MIN_SCALE, min(self.MAX_SCALE, new_scale))
        self.update_transform_from_properties()
        self.clamp_to_scene()
        event.accept()

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if self.mode != 'none' and self.undo_command:
            self.mode = 'none'
            self.clamp_to_scene()
            self.undo_command.capture_after_state()
            self.editor.undo_stack.push(self.undo_command)
            self.undo_command = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QtWidgets.QGraphicsSceneWheelEvent):
        if self.is_locked:
            return
        cmd = TransformModuleCommand(self, "")
        delta = event.delta()
        if delta == 0: return
        scale_factor = 1.1 if delta > 0 else 1 / 1.1
        new_scale = self.scale * scale_factor
        if new_scale > self.MAX_SCALE or new_scale < self.MIN_SCALE:
            return
        self.scale = new_scale
        self.update_transform_from_properties()
        self.clamp_to_scene()
        cmd.capture_after_state()
        self.editor.undo_stack.push(cmd)
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

# ------------------------------------------------------------------------------
# UI連携機能を実装したメインウィンドウ（右クリックメニューを並び替え）
# ------------------------------------------------------------------------------
class GraphicsEditor(QtWidgets.QMainWindow):
    def __init__(self, parent=gui_base.maya_main_window):
        super().__init__(parent)
        self.pre_close()

        self.setWindowTitle(TITLE)
        self.setObjectName(f"YS_{TITLE}_Gui")
        
        self.active_modules = []
        self.module_to_tree_item_map = {}
        self._is_syncing_selection = False
        self.current_selections = []
        self.undo_stack = QUndoStack(self)
        self.view_size = 1000
        self.panel_width = 375
        self.setFixedSize(self.view_size + self.panel_width, self.view_size)
        self._create_menu()
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
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
        main_layout.addWidget(self.view)
        control_panel = QtWidgets.QWidget()
        control_panel.setFixedWidth(self.panel_width)
        control_panel.setStyleSheet("background-color: #2c3e50; color: #ecf0f1;")
        panel_layout = QtWidgets.QVBoxLayout(control_panel)
        panel_layout.setContentsMargins(5, 5, 5, 5)
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
        self._setup_transform_controls(panel_layout)
        main_layout.addWidget(control_panel)
        self.setCentralWidget(main_widget)
        self.modules_data = [mod1, mod2, mod3, mod4, mod5, mod6, mod7, mod8, 
                             mod9, mod10, mod11, mod12, mod13, mod14, mod15, mod16,
                             mod_asymmetric, mod17]
        for mod_data in self.modules_data:
            self.create_module_from_data(mod_data)
        self.populate_outliner()
        self.outliner.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.outliner.customContextMenuRequested.connect(self.on_outliner_context_menu)
        self.outliner.itemSelectionChanged.connect(self.on_outliner_selection_changed)
        self.scene.selectionChanged.connect(self.on_scene_selection_changed)
        self.outliner.itemChanged.connect(self.on_outliner_item_changed)
        self.update_transform_ui()

    def pre_close(self):
        for widget in QtWidgets.QApplication.allWidgets():
            if widget.objectName() == f"YS_{TITLE}_Gui":
                widget.close()
                widget.deleteLater()

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

    def _setup_transform_controls(self, parent_layout):
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
        for spin in [self.trans_x_spin, self.trans_y_spin, self.rot_spin]:
            spin.setRange(-9999, 9999)
            spin.setButtonSymbols(NO_BUTTONS)
            spin.setStyleSheet(spin_style)
        self.scale_spin.setRange(PickerModuleItem.MIN_SCALE, PickerModuleItem.MAX_SCALE)
        self.scale_spin.setButtonSymbols(NO_BUTTONS)
        self.scale_spin.setStyleSheet(spin_style)
        transform_layout.addRow("Translate X:", self.trans_x_spin)
        transform_layout.addRow("Translate Y:", self.trans_y_spin)
        transform_layout.addRow("Rotate:", self.rot_spin)
        transform_layout.addRow("Scale:", self.scale_spin)
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
        flip_layout.addWidget(self.flip_h_btn)
        flip_layout.addWidget(self.flip_v_btn)
        transform_layout.addRow("Local Flip:", flip_layout)
        world_flip_layout = QtWidgets.QHBoxLayout()
        self.world_flip_h_btn = QtWidgets.QPushButton("H")
        self.world_flip_v_btn = QtWidgets.QPushButton("V")
        for btn in [self.world_flip_h_btn, self.world_flip_v_btn]:
            btn.setStyleSheet(btn_style)
        world_flip_layout.addWidget(self.world_flip_h_btn)
        world_flip_layout.addWidget(self.world_flip_v_btn)
        transform_layout.addRow("World Flip:", world_flip_layout)
        parent_layout.addWidget(transform_group)
        parent_layout.addStretch()
        self.trans_x_spin.valueChanged.connect(lambda val: self.on_transform_value_changed('tx', val))
        self.trans_y_spin.valueChanged.connect(lambda val: self.on_transform_value_changed('ty', val))
        self.rot_spin.valueChanged.connect(lambda val: self.on_transform_value_changed('rotation', val))
        self.scale_spin.valueChanged.connect(lambda val: self.on_transform_value_changed('scale', val))
        self.flip_h_btn.clicked.connect(self.on_flip_h_clicked)
        self.flip_v_btn.clicked.connect(self.on_flip_v_clicked)
        self.world_flip_h_btn.clicked.connect(self.on_world_flip_h_clicked)
        self.world_flip_v_btn.clicked.connect(self.on_world_flip_v_clicked)
    
    def update_transform_ui(self):
        single_item_selected = len(self.current_selections) == 1
        is_enabled = single_item_selected and not self.current_selections[0].is_locked
        flip_buttons_enabled = bool(self.current_selections)
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

    def on_flip_h_clicked(self):
        if not self.current_selections: return
        self.undo_stack.beginMacro("Local Flip H")
        for item in self.current_selections:
            if not item.is_locked:
                cmd = TransformModuleCommand(item, "Local Flip H")
                item.flip_h = not item.flip_h
                item.update_transform_from_properties()
                cmd.capture_after_state()
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def on_flip_v_clicked(self):
        if not self.current_selections: return
        self.undo_stack.beginMacro("Local Flip V")
        for item in self.current_selections:
            if not item.is_locked:
                cmd = TransformModuleCommand(item, "Local Flip V")
                item.flip_v = not item.flip_v
                item.update_transform_from_properties()
                cmd.capture_after_state()
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def on_world_flip_h_clicked(self):
        if not self.current_selections: return
        self.undo_stack.beginMacro("World Flip H")
        for item in self.current_selections:
            if not item.is_locked:
                cmd = TransformModuleCommand(item, "World Flip H")
                item.world_flip_horizontal()
                cmd.capture_after_state()
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def on_world_flip_v_clicked(self):
        if not self.current_selections: return
        self.undo_stack.beginMacro("World Flip V")
        for item in self.current_selections:
            if not item.is_locked:
                cmd = TransformModuleCommand(item, "World Flip V")
                item.world_flip_vertical()
                cmd.capture_after_state()
                self.undo_stack.push(cmd)
        self.undo_stack.endMacro()

    def create_module_from_data(self, module_data: PickerModuleData):
        module_item = PickerModuleItem(module_data, self)
        for button_data in module_data.buttons:
            button_item = PickerButtonItem(button_data)
            button_item.setPos(button_data.position['x'], button_data.position['y'])
            module_item.add_button(button_item)
        module_item.update_transform_from_properties(update_ui=False)
        self.scene.addItem(module_item)
        self.active_modules.append(module_item)
    
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
    
    # ★★★★★★★★★★ 修正箇所 ★★★★★★★★★★
    def on_outliner_context_menu(self, point):
        menu = QtWidgets.QMenu(self.outliner)
        has_selection = bool(self.outliner.selectedItems())

        # --- Show Group ---
        show_selection_action = menu.addAction("Show Selection")
        show_selection_action.triggered.connect(self.show_selection)
        show_selection_action.setEnabled(has_selection)

        show_inverse_action = menu.addAction("Show Inverse Selection")
        show_inverse_action.triggered.connect(self.show_inverse_selection)
        show_inverse_action.setEnabled(has_selection)
        
        show_all_action = menu.addAction("Show All")
        show_all_action.triggered.connect(self.show_all_modules)

        menu.addSeparator()

        # --- Hide Group ---
        hide_selection_action = menu.addAction("Hide Selection")
        hide_selection_action.triggered.connect(self.hide_selection)
        hide_selection_action.setEnabled(has_selection)

        hide_inverse_action = menu.addAction("Hide Inverse Selection")
        hide_inverse_action.triggered.connect(self.hide_inverse_selection)
        hide_inverse_action.setEnabled(has_selection)

        hide_all_action = menu.addAction("Hide All")
        hide_all_action.triggered.connect(self.hide_all_modules)

        menu.addSeparator()

        # --- Lock Group ---
        lock_selection_action = menu.addAction("Lock Selection")
        lock_selection_action.triggered.connect(self.lock_selection)
        lock_selection_action.setEnabled(has_selection)

        lock_inverse_action = menu.addAction("Lock Inverse Selection")
        lock_inverse_action.triggered.connect(self.lock_inverse_selection)
        lock_inverse_action.setEnabled(has_selection)
        
        lock_all_action = menu.addAction("Lock All")
        lock_all_action.triggered.connect(self.lock_all_modules)

        menu.addSeparator()

        # --- Unlock Group ---
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
        """選択されていないモジュールのリストを返すヘルパーメソッド"""
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
        self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

# ------------------------------------------------------------------------------
# ユーザー提供のデータ（変更なし）
# ------------------------------------------------------------------------------
mod1 = PickerModuleData(name="sh_module_01", position={'x': -400, 'y': -150}, buttons=[ButtonData(name="s", shape_points=[{'pos': [0, 0]},{'pos': [40, 0]},{'pos': [40, 40]},{'pos': [0, 40]},{'pos': [0, 0]}], position={'x': 0, 'y': 0})])
mod2 = PickerModuleData(name="sh_module_02", position={'x': 100, 'y': 100}, buttons=[ButtonData(name="e", shape_points=[{'pos': [30, 0]},{'pos': [0, -30]},{'pos': [70, -30]},{'pos': [40, 0]},{'pos': [30, 0]}], position={'x': 0, 'y': 0})])
mod3 = PickerModuleData(name="sh_module_03", position={'x': -200, 'y': 250}, buttons=mod1.buttons)
mod4 = PickerModuleData(name="sh_module_04", position={'x': 200, 'y': -250}, buttons=mod2.buttons)
mod5 = PickerModuleData(name="sh_module_05", position={'x': -400, 'y': 150}, buttons=mod1.buttons)
mod6 = PickerModuleData(name="sh_module_06", position={'x': 100, 'y': -100}, buttons=mod2.buttons)
mod7 = PickerModuleData(name="sh_module_07", position={'x': -100, 'y': -300}, buttons=mod1.buttons)
mod8 = PickerModuleData(name="sh_module_08", position={'x': 300, 'y': 300}, buttons=mod2.buttons)
mod9 = PickerModuleData(name="sh_module_09", position={'x': 400, 'y': -350}, buttons=mod1.buttons)
mod10 = PickerModuleData(name="sh_module_10", position={'x': -100, 'y': 400}, buttons=mod2.buttons)
mod11 = PickerModuleData(name="sh_module_11", position={'x': -250, 'y': -250}, buttons=mod1.buttons)
mod12 = PickerModuleData(name="sh_module_12", position={'x': 250, 'y': 250}, buttons=mod2.buttons)
mod13 = PickerModuleData(name="sh_module_13", position={'x': -450, 'y': 0}, buttons=mod1.buttons)
mod14 = PickerModuleData(name="sh_module_14", position={'x': 0, 'y': -450}, buttons=mod2.buttons)
mod15 = PickerModuleData(name="sh_module_15", position={'x': 450, 'y': 0}, buttons=mod1.buttons)
mod16 = PickerModuleData(name="sh_module_16", position={'x': 0, 'y': 450}, buttons=mod2.buttons)
mod_asymmetric = PickerModuleData(name="asymmetric_module", position={'x': -60, 'y': -40}, buttons=[ButtonData(name="L_shape", shape_points=[{'pos': [0, 0]},{'pos': [80, 0]},{'pos': [80, 20]},{'pos': [20, 20]},{'pos': [20, 80]},{'pos': [0, 80]},{'pos': [0, 0]}], position={'x': 0, 'y': 0})])
mod17 = PickerModuleData(name="sh", position={'x': -400, 'y': -150}, buttons=[ButtonData(name="s", shape_points=[{'pos': [0, 0]},{'pos': [40, 0]},{'pos': [40, 40]},{'pos': [0, 40]},{'pos': [0, 0]}], position={'x': 0, 'y': 0}), ButtonData(name="u", shape_points=[{'pos': [0, 10]},{'pos': [60, 5]},{'pos': [60, 35]},{'pos': [0, 30]},{'pos': [0, 10]}], position={'x': 50, 'y': 0}), ButtonData(name="e", shape_points=[{'pos': [0, 0]},{'pos': [40, 0]},{'pos': [40, 40]},{'pos': [0, 40]},{'pos': [0, 0]}], position={'x': 120, 'y': 0}), ButtonData(name="b", shape_points=[{'pos': [0, 5]},{'pos': [60, 10]},{'pos': [60, 30]},{'pos': [0, 35]},{'pos': [0, 5]}], position={'x': 170, 'y': 0}), ButtonData(name="u", shape_points=[{'pos': [0, 10]},{'pos': [30, 0]},{'pos': [50, 0]},{'pos': [50, 40]},{'pos': [30, 40]},{'pos': [0, 30]},{'pos': [0, 10]}], position={'x': 240, 'y': 0})])

def main():
    editor_instance = GraphicsEditor()
    editor_instance.show()
    return editor_instance