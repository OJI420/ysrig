from __future__ import annotations

import os
from typing import List, Dict, Optional
from maya import cmds
from ysrig import gui_base, picker_editor

# PySide 判定
if int(gui_base.ver) <= 2024:
    from PySide2 import QtWidgets, QtCore, QtGui
    IS_PYSIDE6 = False
elif int(gui_base.ver) >= 2025:
    from PySide6 import QtWidgets, QtCore, QtGui
    IS_PYSIDE6 = True

if IS_PYSIDE6:
    LEFT_BUTTON = QtCore.Qt.MouseButton.LeftButton
    RIGHT_BUTTON = QtCore.Qt.MouseButton.RightButton
    FRAMELESS_WINDOW_HINT = QtCore.Qt.WindowType.FramelessWindowHint
    WA_TRANSLUCENT_BACKGROUND = QtCore.Qt.WidgetAttribute.WA_TranslucentBackground
    SCROLLBAR_ALWAYS_OFF = QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    SHIFT_MOD = QtCore.Qt.KeyboardModifier.ShiftModifier
    CTRL_MOD = QtCore.Qt.KeyboardModifier.ControlModifier
    ITEM_IS_SELECTABLE = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    NO_DRAG = QtWidgets.QGraphicsView.DragMode.NoDrag

else:
    LEFT_BUTTON = QtCore.Qt.LeftButton
    RIGHT_BUTTON = QtCore.Qt.RightButton
    FRAMELESS_WINDOW_HINT = QtCore.Qt.FramelessWindowHint
    WA_TRANSLUCENT_BACKGROUND = QtCore.Qt.WA_TranslucentBackground
    SCROLLBAR_ALWAYS_OFF = QtCore.Qt.ScrollBarAlwaysOff
    SHIFT_MOD = QtCore.Qt.ShiftModifier
    CTRL_MOD = QtCore.Qt.ControlModifier
    ITEM_IS_SELECTABLE = QtWidgets.QGraphicsItem.ItemIsSelectable
    NO_DRAG = QtWidgets.QGraphicsView.NoDrag

THIS_FILE_PATH = os.path.abspath(__file__)
PREFS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "prefs"))
ICON_PATH = os.path.join(PREFS_PATH, "ysrig", "icons")
SIZE_GRIP_PATH = os.path.join(ICON_PATH, "YSSizeGrip.png")

# -------------------------
# Helper: flexible QColor construction
# -------------------------
def make_qcolor(color_input):
    if color_input is None:
        return None
    
    if isinstance(color_input, QtGui.QColor):
        return color_input

    # string hex
    if isinstance(color_input, str):
        s = color_input.strip()
        if not s.startswith("#"):
            s = "#" + s
        return QtGui.QColor(s)

    # dict with 0-1 floats or 0-255 ints
    if isinstance(color_input, dict):
        r = color_input.get("r", 0.0)
        g = color_input.get("g", 0.0)
        b = color_input.get("b", 0.0)
        if 0.0 <= r <= 1.0 and 0.0 <= g <= 1.0 and 0.0 <= b <= 1.0:
            return QtGui.QColor(int(r*255), int(g*255), int(b*255))
        else:
            return QtGui.QColor(int(r), int(g), int(b))

    # list / tuple
    if isinstance(color_input, (list, tuple)) and len(color_input) >= 3:
        vals = list(color_input)
        r, g, b = vals[0], vals[1], vals[2]
        if all(isinstance(v, float) and 0.0 <= v <= 1.0 for v in (r, g, b)):
            return QtGui.QColor(int(r*255), int(g*255), int(b*255))
        else:
            return QtGui.QColor(int(r), int(g), int(b))

    return QtGui.QColor(color_input)


# -------------------------
# Graphics Items
# -------------------------
class PickerButtonItem(QtWidgets.QGraphicsPathItem):
    DEFAULT_BRUSH_COLOR = QtGui.QColor(70, 130, 180)
    SELECTED_COLOR = QtGui.QColor(255, 255, 255) # 白
    LAST_SELECTED_COLOR = QtGui.QColor(0, 255, 0) # 緑
    DISABLED_COLOR = QtGui.QColor(60, 60, 60)    # グレー (無効時)

    def __init__(self, button_data: picker_editor.gui.ButtonData, scripts: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        self.button_data = button_data
        self.scripts = scripts or {} # スクリプト辞書を保持
        self.is_disabled = False
        self.setFlag(ITEM_IS_SELECTABLE, True)
        
        self.setAcceptHoverEvents(True)

        qcol = make_qcolor(self.button_data.color)
        self._default_color = qcol if qcol is not None else self.DEFAULT_BRUSH_COLOR
        
        self._current_base_color = self._default_color

        self._pen = QtGui.QPen(QtGui.QColor(10, 10, 10), 1)
        self._build_path(self.button_data.shape_points)

        self._update_brush()
        self.setPen(self._pen)

    def _build_path(self, points: List[List[float]]):
        path = QtGui.QPainterPath()
        if points:
            start = points[0]
            path.moveTo(float(start[0]), float(start[1]))
            for p in points[1:]:
                if len(p) >= 2:
                    path.lineTo(float(p[0]), float(p[1]))
            if points[-1] != points[0]:
                path.closeSubpath()
        self.setPath(path)

    def shape(self) -> QtGui.QPainterPath:
        return self.path()

    def _update_brush(self, is_hovering=False):
        color = self._current_base_color
        if is_hovering and not self.is_disabled:
            rgb_sum = color.red() + color.green() + color.blue()
            factor = max(120, 500 - rgb_sum)
            color = color.lighter(int(factor))

        self.setBrush(QtGui.QBrush(color))

    def set_selection_state(self, state: int):
        if self.is_disabled:
            return

        if state == 2:
            self._current_base_color = self.LAST_SELECTED_COLOR
        elif state == 1:
            self._current_base_color = self.SELECTED_COLOR
        else:
            self._current_base_color = self._default_color
        
        self._update_brush(is_hovering=False)

    def set_disabled(self, disabled: bool):
        """無効化状態を切り替え、見た目とフラグを更新する"""
        self.is_disabled = disabled
        if disabled:
            self.setFlag(ITEM_IS_SELECTABLE, False)
            self.setAcceptHoverEvents(False)
            self._current_base_color = self.DISABLED_COLOR
            self._update_brush(is_hovering=False)
        else:
            self.setFlag(ITEM_IS_SELECTABLE, True)
            self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        if not self.is_disabled:
            self._update_brush(is_hovering=True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.is_disabled:
            self._update_brush(is_hovering=False)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        # 右クリック かつ スクリプトが登録されている場合
        if event.button() == RIGHT_BUTTON and self.scripts:
            self.ungrabMouse()

            self._show_context_menu(event)
            event.accept()
            return

        super().mousePressEvent(event)

    def _show_context_menu(self, event):
        menu = QtWidgets.QMenu()
        for label, func in self.scripts.items():
            action = menu.addAction(label)
            
            def run_script_and_refresh(checked=False, f=func):
                f()
                YSPicker.refresh_all_pickers()
            
            action.triggered.connect(run_script_and_refresh)

        if IS_PYSIDE6:
            gp = event.screenPos()
            menu.exec(gp)
        else:
            gp = event.screenPos()
            menu.exec_(gp)


class PickerModuleItem(QtWidgets.QGraphicsItemGroup):
    """
    Module group: Applies position, rotation, flip, and scale (local axis).
    """
    def __init__(self, module_data: picker_editor.gui.PickerModuleData, editor):
        super().__init__()
        self.module_data = module_data
        self.editor = editor
        self.buttons: List[PickerButtonItem] = []
        
        self.setHandlesChildEvents(False)
        
        self.build_buttons()

    def build_buttons(self):
        # モジュールに設定されたスクリプトを取得 (存在しない場合は空辞書)
        scripts = getattr(self.module_data, "scripts", {})

        for b in self.module_data.buttons:
            # scriptsをボタンに渡す
            btn = PickerButtonItem(b, scripts=scripts)
            btn.setPos(float(b.position.get("x", 0.0)), float(b.position.get("y", 0.0)))
            self.addToGroup(btn)
            self.buttons.append(btn)
        self.apply_transform()

    def apply_transform(self):
        t = QtGui.QTransform()
        t.translate(self.module_data.position.get("x", 0), self.module_data.position.get("y", 0))
        t.rotate(self.module_data.rotation)
        
        scale_val = getattr(self.module_data, "scale", 1.0)
        sx = -scale_val if self.module_data.flip_h else scale_val
        sy = -scale_val if self.module_data.flip_v else scale_val
        
        t.scale(sx, sy)
        self.setTransform(t)


# -------------------------
# Drag Handle (Modified)
# -------------------------
class DragHandle(QtWidgets.QFrame):
    def __init__(self, parent_window, label="YSPicker"):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setFixedHeight(28)
        self._drag_offset = None

        self.setObjectName("DragHandle")
        self.setCursor(QtCore.Qt.OpenHandCursor)

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(6)

        label_widget = QtWidgets.QLabel(label)
        label_widget.setStyleSheet("color: white; font-size: 11px; background: rgba(0,0,0,0);")
        lay.addWidget(label_widget)

        lay.addStretch()

        # --- Lock Button Added ---
        self.lock_btn = QtWidgets.QPushButton("🔓")
        self.lock_btn.setCheckable(True)
        self.lock_btn.setFixedSize(24, 18)
        self.lock_btn.setToolTip("Lock Window Movement")
        
        self.lock_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(50,50,50,150);
                border: none;
                border-radius: 2px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(80,80,80,200);
            }
            QPushButton:checked {
                background: rgba(255, 100, 50, 200);
            }
            QPushButton:checked:hover {
                background: rgba(255, 120, 70, 230);
            }
        """)
        self.lock_btn.toggled.connect(self.on_lock_toggled)
        lay.addWidget(self.lock_btn)
        # -------------------------

        self.close_btn = QtWidgets.QPushButton("X")
        self.close_btn.setFixedSize(18, 18)
        self.close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(180,30,30,200);
                border: none;
                border-radius: 2px;
            }
            QPushButton:hover {
                background: rgba(200,60,60,230);
            }
        """)
        self.close_btn.clicked.connect(self.parent_window.close)
        lay.addWidget(self.close_btn)

        self.setStyleSheet("""
            QFrame#DragHandle { background: rgba(80,180,255,220); border-bottom: 1px solid rgba(255,255,255,60); }
        """)

    def on_lock_toggled(self, checked):
        if checked:
            self.lock_btn.setText("🔒")
            self.setCursor(QtCore.Qt.ArrowCursor)
        else:
            self.lock_btn.setText("🔓")
            self.setCursor(QtCore.Qt.OpenHandCursor)

    def mousePressEvent(self, event):
        if self.lock_btn.isChecked():
            return

        if event.button() == RIGHT_BUTTON:
            self.parent_window.cycle_display_mode()
            event.accept()
            return

        if event.button() == LEFT_BUTTON:
            if IS_PYSIDE6:
                gp = event.globalPosition().toPoint()
            else:
                gp = event.globalPos()
            self._drag_offset = gp - self.parent_window.frameGeometry().topLeft()
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        if self.lock_btn.isChecked():
            return

        if self._drag_offset is None:
            return
        if IS_PYSIDE6:
            gp = event.globalPosition().toPoint()
        else:
            gp = event.globalPos()
        self.parent_window.move(gp - self._drag_offset)
        event.accept()

    def mouseReleaseEvent(self, event):
        if self.lock_btn.isChecked():
            return

        self._drag_offset = None
        self.setCursor(QtCore.Qt.OpenHandCursor)


# -------------------------
# PickerView
# -------------------------
class PickerView(QtWidgets.QGraphicsView):
    def __init__(self, scene, parent_window):
        super().__init__(scene, parent_window)
        self.parent_window :YSPicker = parent_window

        self.setDragMode(NO_DRAG)
        
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(SCROLLBAR_ALWAYS_OFF)
        self.setVerticalScrollBarPolicy(SCROLLBAR_ALWAYS_OFF)
        self.setFrameStyle(QtWidgets.QFrame.NoFrame)

        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

        self.setAutoFillBackground(False)
        self.viewport().setAutoFillBackground(False)

        self._transparent_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 1))
        self._opaque_brush = QtGui.QBrush(QtGui.QColor(100, 110, 110))
        self._alpha5_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, int(255 * 0.05)))
        self.update_background_brush()

        self._drag_start_pos = QtCore.QPoint()
        self._is_dragging = False
        
        self._rubber_band: Optional[QtWidgets.QGraphicsRectItem] = None

    def update_background_brush(self):
        mode = getattr(self.parent_window, "display_mode", 0)
        if mode == self.parent_window.MODE_BACKGROUND:
            self.setBackgroundBrush(self._opaque_brush)
        elif mode == self.parent_window.MODE_TRANSPARENT_5:
            self.setBackgroundBrush(self._alpha5_brush)
        else:
            self.setBackgroundBrush(self._transparent_brush)

    def mousePressEvent(self, event):
        # 左クリック
        if event.button() == LEFT_BUTTON:
            self._drag_start_pos = event.pos()
            self._is_dragging = False
        
        # 右クリック
        elif event.button() == RIGHT_BUTTON:
            # クリックした位置にアイテムがあるか確認
            item = self.itemAt(event.pos())
            
            # アイテムがない場合のみ、メニューを表示
            if item is None:
                self._show_background_menu(event)
                event.accept()
                return

        super().mousePressEvent(event)

    def _show_background_menu(self, event):
        def get_ctrls(mod):
            ctrls = []
            buttons = mod.buttons
            for button in buttons:
                name = button.name
                if "@" in name:
                    if button.child_modules:
                        for m in button.child_modules:
                            cs = get_ctrls(m)
                            if cs:
                                ctrls += cs

                else:
                    ctrls += [name]

            return ctrls

        def select():
            ctrls = []
            for mod in self.parent_window.modules_data:
                ctrls += get_ctrls(mod)

            ctrls = [f"Ctrl_{c}" for c in ctrls]
            ctrls = ctrls[1:] + ctrls[:1]
            cmds.select(ctrls)

            YSPicker.refresh_all_pickers()

        def deselect():
            cmds.select(cl=True)
            YSPicker.refresh_all_pickers()

        def reset_transform():
            cmds.undoInfo(ock=True)
            sel = cmds.ls(sl=True)
            attrs = {"tx":0, "ty":0, "tz":0, "rx":0, "ry":0, "rz":0, "sx":1, "sy":1, "sz":1}
            for s in sel:
                for attr in attrs:
                    if not cmds.getAttr(f"{s}.{attr}", l=True):
                        cmds.setAttr(f"{s}.{attr}", attrs[attr])

            cmds.undoInfo(cck=True)

        menu = QtWidgets.QMenu()

        action_select = menu.addAction("All Select")
        action_select.triggered.connect(select)

        action_deselect = menu.addAction("All Deselect")
        action_deselect.triggered.connect(deselect)

        action_reset = menu.addAction("Reset Selection Transform")
        action_reset.triggered.connect(reset_transform)

        gp = event.screenPos().toPoint()
        if IS_PYSIDE6:
            menu.exec(gp)
        else:
            menu.exec_(gp)

    def mouseMoveEvent(self, event):
        if event.buttons() & LEFT_BUTTON:
            if not self._is_dragging:
                if (event.pos() - self._drag_start_pos).manhattanLength() > QtWidgets.QApplication.startDragDistance():
                    self._is_dragging = True
                    self._start_rubber_band()
            
            if self._is_dragging:
                self._update_rubber_band(event.pos())

        super().mouseMoveEvent(event)

    def _start_rubber_band(self):
        if self._rubber_band is None:
            self._rubber_band = QtWidgets.QGraphicsRectItem()
            self._rubber_band.setPen(QtGui.QPen(QtCore.Qt.white, 1, QtCore.Qt.DashLine))
            self._rubber_band.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 255, 40)))
            self._rubber_band.setZValue(10000)
            self.scene().addItem(self._rubber_band)

    def _update_rubber_band(self, current_pos):
        if self._rubber_band:
            start_scene = self.mapToScene(self._drag_start_pos)
            end_scene = self.mapToScene(current_pos)
            rect = QtCore.QRectF(start_scene, end_scene).normalized()
            self._rubber_band.setRect(rect)

    def _remove_rubber_band(self):
        if self._rubber_band:
            if self._rubber_band.scene():
                self.scene().removeItem(self._rubber_band)
            self._rubber_band = None

    def mouseReleaseEvent(self, event):
        self._remove_rubber_band()

        if event.button() == LEFT_BUTTON:
            mods = event.modifiers()
            
            start_item = self.itemAt(self._drag_start_pos)
            is_button_start = isinstance(start_item, PickerButtonItem)
            if is_button_start and start_item.is_disabled:
                is_button_start = False

            if self._is_dragging:
                # --- ドラッグ操作 ---
                start_scene_pt = self.mapToScene(self._drag_start_pos)
                end_scene_pt = self.mapToScene(event.pos())
                rectf = QtCore.QRectF(start_scene_pt, end_scene_pt).normalized()

                touched_items = self.scene().items(rectf, QtCore.Qt.IntersectsItemShape)
                
                buttons = [
                    it.button_data for it in touched_items 
                    if isinstance(it, PickerButtonItem) and not it.is_disabled
                ]

                if is_button_start:
                    if mods == SHIFT_MOD:
                        self.parent_window.on_button_shift_drag(buttons)
                    elif mods == CTRL_MOD:
                        self.parent_window.on_button_ctrl_drag(buttons)
                    else:
                        self.parent_window.on_button_drag(buttons)
                else:
                    if mods == SHIFT_MOD:
                        self.parent_window.on_background_shift_drag(buttons)
                    elif mods == CTRL_MOD:
                        self.parent_window.on_background_ctrl_drag(buttons)
                    else:
                        self.parent_window.on_background_drag(buttons)
            else:
                # --- クリック操作 (ドラッグなし) ---
                current_item = self.itemAt(event.pos())
                
                if isinstance(current_item, PickerButtonItem) and not current_item.is_disabled:
                    if mods == SHIFT_MOD:
                        self.parent_window.on_button_shift_clicked([current_item.button_data])
                    elif mods == CTRL_MOD:
                        self.parent_window.on_button_ctrl_clicked([current_item.button_data])
                    else:
                        self.parent_window.on_button_clicked([current_item.button_data])
                else:
                    if mods == SHIFT_MOD or mods == CTRL_MOD:
                        pass
                    else:
                        self.parent_window.on_background_clicked()

            self.scene().clearSelection()
            self._is_dragging = False

        super().mouseReleaseEvent(event)


# -------------------------
# TransparentPickerEditor
# -------------------------
class YSPicker(QtWidgets.QMainWindow):
    MODE_BACKGROUND = 0
    MODE_TRANSPARENT_5 = 1
    MODE_TRANSPARENT_FRAME = 2
    MODE_FULL_TRANSPARENT = 3

    def __init__(self, modules_data, label="YSPicker", parent=None, obj_name=None):
        super().__init__(parent)

        self.ysrig_window = True
        self.setObjectName(obj_name)

        self.modules_data = modules_data
        self.display_mode = self.MODE_BACKGROUND
        self._initial_scale_done = False

        self.setWindowFlags(self.windowFlags() | FRAMELESS_WINDOW_HINT)
        self.setAttribute(WA_TRANSLUCENT_BACKGROUND, True)

        self.base_window_size = 1100
        self.resize(self.base_window_size, self.base_window_size)
        self.current_scale_ratio = 1.0

        self.main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.handle = DragHandle(self, label=label)
        main_layout.addWidget(self.handle)

        self.scene = QtWidgets.QGraphicsScene(self)
        half = self.base_window_size / 2
        self.scene.setSceneRect(-half, -half, self.base_window_size, self.base_window_size)

        self.view = PickerView(self.scene, self)
        main_layout.addWidget(self.view)

        self.setCentralWidget(self.main_widget)

        self.status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.size_grip = QtWidgets.QSizeGrip(self.status_bar)
        self.status_bar.addPermanentWidget(self.size_grip)
        
        self.size_grip.setVisible(self.display_mode == self.MODE_BACKGROUND)
        self.status_bar.setVisible(self.display_mode == self.MODE_BACKGROUND)

        self._lock_resize = False

        self.load_modules()
        self.apply_style()
        
        # 初回の選択状態更新
        self.update_selection_visuals()

        self._app = QtWidgets.QApplication.instance()
        self._app.aboutToQuit.connect(self.save_window_settings_registry)
        self.load_window_settings_registry()

    def load_modules(self):
        for m in self.modules_data:
            if m.visibility:
                item = PickerModuleItem(m, self)
                self.scene.addItem(item)

    def apply_style(self):
        if self.display_mode == self.MODE_BACKGROUND:
            css_icon_path = SIZE_GRIP_PATH.replace("\\", "/")
            
            self.setStyleSheet(f"""
                QSizeGrip {{
                    image: url({css_icon_path});
                    width: 24px;
                    height: 24px;
                    background-color: transparent;
                }}
            """)
            self.main_widget.setStyleSheet("QWidget { background: rgb(50,50,50); }")
            self.status_bar.setVisible(True)
            self.size_grip.setVisible(True)
            self.main_widget.setProperty("hasFrameBorder", False)
            self.main_widget.style().unpolish(self.main_widget)
            self.main_widget.style().polish(self.main_widget)
        elif self.display_mode == self.MODE_TRANSPARENT_5:
            self.main_widget.setStyleSheet("QWidget { background: rgba(0,0,0,13); }")
            self.status_bar.setVisible(False)
            self.size_grip.setVisible(False)
        elif self.display_mode == self.MODE_TRANSPARENT_FRAME:
            self.main_widget.setStyleSheet("""
                QWidget {
                    background: transparent;
                    border: 1px solid rgba(255,255,255,255);
                }
            """)
            self.status_bar.setVisible(False)
            self.size_grip.setVisible(False)
        elif self.display_mode == self.MODE_FULL_TRANSPARENT:
            self.main_widget.setStyleSheet("QWidget { background: transparent; border: none; }")
            self.status_bar.setVisible(False)
            self.size_grip.setVisible(False)
        else:
            self.main_widget.setStyleSheet("QWidget { background: transparent; }")
            self.status_bar.setVisible(False)
            self.size_grip.setVisible(False)

        if hasattr(self, "view"):
            self.view.update_background_brush()

    def cycle_display_mode(self):
        self.display_mode = (self.display_mode + 1) % 4
        self.apply_style()

    def toggle_transparency(self):
        if self.display_mode == self.MODE_BACKGROUND:
            self.display_mode = self.MODE_FULL_TRANSPARENT
        else:
            self.display_mode = self.MODE_BACKGROUND
        self.apply_style()

    # --- Class Method to Update ALL Pickers ---
    @classmethod
    def refresh_all_pickers(cls):
        """現在開いている全てのYSPickerインスタンスの選択表示を更新する"""
        # アプリケーション内の全ウィジェットからYSPickerを探す
        for widget in QtWidgets.QApplication.allWidgets():
            if isinstance(widget, YSPicker):
                widget.update_selection_visuals()

    def keyPressEvent(self, event):
        if IS_PYSIDE6:
            k_z = QtCore.Qt.Key.Key_Z
            k_y = QtCore.Qt.Key.Key_Y
            mod_ctrl = QtCore.Qt.KeyboardModifier.ControlModifier
            mod_none = QtCore.Qt.KeyboardModifier.NoModifier
        else:
            k_z = QtCore.Qt.Key_Z
            k_y = QtCore.Qt.Key_Y
            mod_ctrl = QtCore.Qt.ControlModifier
            mod_none = QtCore.Qt.NoModifier

        key = event.key()
        mods = event.modifiers()

        # Undo: z (Modifiersなし)
        if key == k_z and mods == mod_none:
            try:
                cmds.undo()
            except RuntimeError:
                pass
            self.refresh_all_pickers()
            event.accept()
            return

        # Redo: Ctrl + z
        if key == k_z and (mods == mod_ctrl):
            try:
                cmds.undo()
            except RuntimeError:
                pass
            self.refresh_all_pickers()
            event.accept()
            return

        # Redo: Ctrl + y
        if key == k_y and (mods == mod_ctrl):
            try:
                cmds.redo()
            except RuntimeError:
                pass
            self.refresh_all_pickers()
            event.accept()
            return

        super().keyPressEvent(event)

    # --- Event Handlers for Window State ---
    def changeEvent(self, event):
        """ウィンドウのアクティブ化時に更新"""
        if event.type() == QtCore.QEvent.ActivationChange:
            if self.isActiveWindow():
                self.refresh_all_pickers()
        super().changeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._initial_scale_done:
            self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
            self._initial_scale_done = True
        self.update_selection_visuals()

    def resizeEvent(self, event):
        if getattr(self, "_lock_resize", False):
            super().resizeEvent(event)
            return

        w = event.size().width()
        h = event.size().height()
        size = max(w, h)

        if w == size and h == size:
            self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
            super().resizeEvent(event)
            return

        self._lock_resize = True
        self.resize(size, size)
        self._lock_resize = False

        self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        super().resizeEvent(event)

# --- Selection Update Logic ---
    def update_selection_visuals(self):
        """Mayaの現在の選択状態を取得し、ボタンの色と表示状態を更新する"""
        sel = cmds.ls(sl=True, l=False) or []
        last_selected = sel[-1] if sel else None
        
        all_items = []
        for item in self.scene.items():
            if isinstance(item, PickerButtonItem):
                all_items.append(item)
            elif isinstance(item, PickerModuleItem):
                all_items.extend(item.buttons)
        
        items_to_deselect = [] # 選択解除を行うコントローラーのリスト

        for btn in all_items:
            if "@Silhouette" in btn.button_data.name:
                btn.setVisible(True)
                btn.set_disabled(True)
                continue

            ctrl_name = f"Ctrl_{btn.button_data.name}"
            should_hide_action = False
            
            if hasattr(btn.button_data, "hide_attr") and btn.button_data.hide_attr:
                hide_attr_dict = btn.button_data.hide_attr
                
                for attr_name, trigger_val in hide_attr_dict.items():
                    full_attr = f"{ctrl_name}.{attr_name}"
                    if cmds.objExists(full_attr):
                        try:
                            current_val = cmds.getAttr(full_attr)
                            # 値が一致したらHideアクション有効
                            if current_val == trigger_val:
                                should_hide_action = True
                                break 
                        except Exception:
                            pass

            if should_hide_action:
                hide_type = getattr(btn.button_data, "hide_type", 0)
                
                if hide_type == 0:
                    # タイプ0: 完全非表示
                    btn.setVisible(False)
                    continue 
                
                elif hide_type == 1:
                    # タイプ1: グレーアウト & 選択不可
                    btn.setVisible(True)
                    btn.set_disabled(True)
                    
                    if ctrl_name in sel:
                        items_to_deselect.append(ctrl_name)

                    continue 

            # 通常状態
            btn.setVisible(True)
            btn.set_disabled(False)

            # --- Selection Color Logic ---
            is_selected = ctrl_name in sel
            is_last = (ctrl_name == last_selected)
            
            if is_last:
                btn.set_selection_state(2)
            elif is_selected:
                btn.set_selection_state(1)
            else:
                btn.set_selection_state(0)

        # 対象のコントローラーを一括で選択解除
        if items_to_deselect:
            cmds.select(items_to_deselect, d=True)

    # --- Handlers: Click (Updated to use refresh_all_pickers) ---
    def on_button_clicked(self, buttons: List[picker_editor.gui.ButtonData]):
        if not buttons:
            self.refresh_all_pickers()
            return

        button_data = buttons[0]
        button_name = button_data.name
        ctrl_name = f"Ctrl_{button_name}"

        if "@Pointer" in button_name:
            show_picker(button_data.child_modules, label=button_name.replace("@Pointer", ""))
        elif not "@" in button_name:
            cmds.select(ctrl_name)
        
        self.refresh_all_pickers()

    def on_button_shift_clicked(self, buttons: List[picker_editor.gui.ButtonData]):
        if not buttons:
            self.refresh_all_pickers()
            return

        button_data = buttons[0]
        button_name = button_data.name
        ctrl_name = f"Ctrl_{button_name}"

        if "@Pointer" in button_name:
            show_picker(button_data.child_modules, label=button_name.replace("@Pointer", ""))
        elif not "@" in button_name:
            cmds.select(ctrl_name, tgl=True)
        
        self.refresh_all_pickers()

    def on_button_ctrl_clicked(self, buttons: List[picker_editor.gui.ButtonData]):
        if not buttons:
            self.refresh_all_pickers()
            return

        button_data = buttons[0]
        button_name = button_data.name
        ctrl_name = f"Ctrl_{button_name}"

        if "@Pointer" in button_name:
            show_picker(button_data.child_modules, label=button_name.replace("@Pointer", ""))
        elif not "@" in button_name:
            cmds.select(ctrl_name, d=True)
        
        self.refresh_all_pickers()

    def on_background_clicked(self):
        cmds.select(cl=True)
        self.refresh_all_pickers()

    # --- Handlers: Background Drag (Updated to use refresh_all_pickers) ---
    def on_background_drag(self, buttons: List[picker_editor.gui.ButtonData]):
        cmds.select([f"Ctrl_{b.name}" for b in buttons if not "@" in b.name])
        self.refresh_all_pickers()

    def on_background_shift_drag(self, buttons: List[picker_editor.gui.ButtonData]):
        if not buttons:
            return

        cmds.select([f"Ctrl_{b.name}" for b in buttons if not "@" in b.name], tgl=True)
        self.refresh_all_pickers()

    def on_background_ctrl_drag(self, buttons: List[picker_editor.gui.ButtonData]):
        if not buttons:
            return
        cmds.select([f"Ctrl_{b.name}" for b in buttons if not "@" in b.name], d=True)
        self.refresh_all_pickers()

    # --- Handlers: Button Drag (Updated to use refresh_all_pickers) ---
    def on_button_drag(self, buttons: List[picker_editor.gui.ButtonData]):
        cmds.select([f"Ctrl_{b.name}" for b in buttons if not "@" in b.name])
        self.refresh_all_pickers()

    def on_button_shift_drag(self, buttons: List[picker_editor.gui.ButtonData]):
        cmds.select([f"Ctrl_{b.name}" for b in buttons if not "@" in b.name], tgl=True)
        self.refresh_all_pickers()

    def on_button_ctrl_drag(self, buttons: List[picker_editor.gui.ButtonData]):
        cmds.select([f"Ctrl_{b.name}" for b in buttons if not "@" in b.name], d=True)
        self.refresh_all_pickers()

    def save_window_settings_registry(self):
        """レジストリにウィンドウ状態(位置・サイズ・背景モード・ロック)を保存"""
        settings = QtCore.QSettings("YSRigSystem", self.objectName())
        
        # 1. ジオメトリ (位置・サイズ)
        settings.setValue("geometry", self.saveGeometry())
        
        # 2. 背景モード (int)
        settings.setValue("display_mode", self.display_mode)
        
        # 3. ロック状態 (bool)
        is_locked = self.handle.lock_btn.isChecked()
        settings.setValue("locked", is_locked)

    def load_window_settings_registry(self):
        """レジストリからウィンドウ状態を復元"""
        settings = QtCore.QSettings("YSRigSystem", self.objectName())
        
        # 1. ジオメトリ
        geometry_data = settings.value("geometry")
        if geometry_data:
            self.restoreGeometry(geometry_data)
            
        # 2. 背景モード
        # デフォルトは MODE_BACKGROUND
        val_mode = settings.value("display_mode", self.MODE_BACKGROUND)
        if val_mode is not None:
            self.display_mode = int(val_mode)
            self.apply_style() # スタイルを適用して見た目を更新
            
        # 3. ロック状態
        # デフォルトは False
        val_locked = settings.value("locked", False)
        
        # QSettingsの返り値が文字列("true"/"false")の場合の対策
        if isinstance(val_locked, str):
            val_locked = (val_locked.lower() == 'true')

        self.handle.lock_btn.setChecked(bool(val_locked))

    def closeEvent(self, event):
        try:
            self._app.aboutToQuit.disconnect(self.save_window_settings_registry)
        except (RuntimeError, TypeError):
            pass
        super().closeEvent(event)
        self.save_window_settings_registry()


PICKER_OBJ_NAME = "YSPicker"

def show_picker(modules_data: List[picker_editor.gui.PickerModuleData], label="YSPicker") -> Optional[YSPicker]:
    if label != "YSPicker":
        obj_name = f"{PICKER_OBJ_NAME}_{label.replace(' ', '_').replace('@Pointer', '')}"
    else:
        obj_name = PICKER_OBJ_NAME

    for widget in QtWidgets.QApplication.allWidgets():
        if widget.objectName() == obj_name:
            widget.close()
            widget.deleteLater()
    
    window = YSPicker(modules_data, label=label, parent=gui_base.maya_main_window, obj_name=obj_name)
    window.show()
    window.activateWindow()
    return window

# -------------------------
# main
# -------------------------

def main():
    show_picker(picker_editor.gui.get_shape_data())