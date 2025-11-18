# picker.py
from __future__ import annotations

import sys
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from maya import cmds
from ysrig import gui_base, picker_editor

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
else:
    LEFT_BUTTON = QtCore.Qt.LeftButton
    RIGHT_BUTTON = QtCore.Qt.RightButton
    FRAMELESS_WINDOW_HINT = QtCore.Qt.FramelessWindowHint
    WA_TRANSLUCENT_BACKGROUND = QtCore.Qt.WA_TranslucentBackground
    SCROLLBAR_ALWAYS_OFF = QtCore.Qt.ScrollBarAlwaysOff
    SHIFT_MOD = QtCore.Qt.ShiftModifier
    CTRL_MOD = QtCore.Qt.ControlModifier
    ITEM_IS_SELECTABLE = QtWidgets.QGraphicsItem.ItemIsSelectable


class PickerButtonItem(QtWidgets.QGraphicsPathItem):
    DEFAULT_BRUSH_COLOR = QtGui.QColor(70, 130, 180)

    def __init__(self, button_data: picker_editor.gui.ButtonData, parent=None):
        super().__init__(parent)
        self.button_data = button_data
        self.setFlag(ITEM_IS_SELECTABLE, True)

        # (Req 3) ButtonData.color からデフォルト色とホバー色（明るい色）を定義
        self._default_color = QtGui.QColor(self.button_data.color) if self.button_data.color else self.DEFAULT_BRUSH_COLOR
        self._hover_color = self._default_color.lighter(130) # 130% の明るさ

        # (Req 3) 高速化のため、ペンと両方の状態のブラシをキャッシュ
        self._pen = QtGui.QPen(QtGui.QColor(10, 10, 10), 1)
        self._brush = QtGui.QBrush(self._default_color)
        self._hover_brush = QtGui.QBrush(self._hover_color)

        self._build_path(button_data.shape_points)
        
        # (Req 3) デフォルトのブラシとペンをセット
        self.setBrush(self._brush)
        self.setPen(self._pen)
        
        # (Req 3) ホバーイベントを有効化
        self.setAcceptHoverEvents(True)

    def _build_path(self, points: List[List[float]]):
        path = QtGui.QPainterPath()
        if points:
            start = points[0]
            path.moveTo(start[0], start[1])
            for p in points[1:]:
                if len(p) >= 2:
                    path.lineTo(p[0], p[1])
            if points[-1] != points[0]:
                path.closeSubpath()
        self.setPath(path)

    def setDefaultStyle(self):
        """デフォルトのブラシとペンを適用（現在は__init__でのみ使用）"""
        self.setBrush(self._brush)
        self.setPen(self._pen)

    def hoverEnterEvent(self, event):
        """(Req 3) マウスがアイテムに入ったときにホバー用のブラシを適用"""
        self.setBrush(self._hover_brush)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """(Req 3) マウスがアイテムから出たときにデフォルトのブラシに戻す"""
        self.setBrush(self._brush)
        super().hoverLeaveEvent(event)


class PickerModuleItem(QtWidgets.QGraphicsItemGroup):
    def __init__(self, module_data: picker_editor.gui.PickerModuleData, editor):
        super().__init__()
        self.module_data = module_data
        self.editor = editor
        self.buttons = []
        self.build_buttons()

    def build_buttons(self):
        for b in self.module_data.buttons:
            btn = PickerButtonItem(b)
            btn.setPos(b.position["x"], b.position["y"])
            self.addToGroup(btn)
            self.buttons.append(btn)

        self.apply_transform()

    def apply_transform(self):
        t = QtGui.QTransform()
        t.translate(self.module_data.position.get("x", 0), self.module_data.position.get("y", 0))
        t.rotate(self.module_data.rotation)
        sx = -self.module_data.scale if self.module_data.flip_h else self.module_data.scale
        sy = -self.module_data.scale if self.module_data.flip_v else self.module_data.scale
        t.scale(sx, sy)
        self.setTransform(t)


class DragHandle(QtWidgets.QFrame):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setFixedHeight(28)
        self._drag_offset = None

        self.setObjectName("DragHandle")
        self.setCursor(QtCore.Qt.OpenHandCursor)

        # Layout
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(6)

        label = QtWidgets.QLabel("Picker")
        label.setStyleSheet("color: white; font-size: 11px;")
        lay.addWidget(label)

        lay.addStretch()

        # Close Button
        self.close_btn = QtWidgets.QPushButton("x")
        self.close_btn.setFixedSize(18, 18)
        self.close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(150,50,50,160);
                border: none;
                border-radius: 2px;
            }
            QPushButton:hover {
                background: rgba(200,60,60,200);
            }
        """)
        self.close_btn.clicked.connect(self.parent_window.close)
        lay.addWidget(self.close_btn)

    def mousePressEvent(self, event):
        if event.button() == RIGHT_BUTTON:
            self.parent_window.toggle_transparency()
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
        if self._drag_offset is None:
            return
        
        if IS_PYSIDE6:
            gp = event.globalPosition().toPoint()
        else:
            gp = event.globalPos()
        self.parent_window.move(gp - self._drag_offset)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        self.setCursor(QtCore.Qt.OpenHandCursor)


class PickerView(QtWidgets.QGraphicsView):
    """
    クリック/ドラッグ選択イベントを処理するためのカスタムQGraphicsView。
    """
    def __init__(self, scene, parent_window):
        super().__init__(scene, parent_window)
        self.parent_window = parent_window
        
        # (Req 4) ドラッグモードをラバーバンド（矩形）選択に設定
        # これにより、ドラッグで矩形が表示され、範囲内のアイテムが自動で選択状態になる
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(SCROLLBAR_ALWAYS_OFF)
        self.setVerticalScrollBarPolicy(SCROLLBAR_ALWAYS_OFF)
        self.setFrameStyle(QtWidgets.QFrame.NoFrame)

        self.setAutoFillBackground(False)
        self.viewport().setAutoFillBackground(False)

        self._transparent_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 1))
        self._opaque_brush = QtGui.QBrush(QtGui.QColor(40, 40, 40))

        self.update_background_brush() 

        self._drag_start_pos = QtCore.QPoint()
        self._is_dragging = False

    def update_background_brush(self):
        """親ウィンドウの透過状態に基づいて背景ブラシを設定"""
        if self.parent_window.is_transparent:
            self.setBackgroundBrush(self._transparent_brush)
        else:
            self.setBackgroundBrush(self._opaque_brush)

    def mousePressEvent(self, event):
        """クリック/ドラッグ開始を検知"""
        if event.button() == LEFT_BUTTON:
            self._drag_start_pos = event.pos()
            self._is_dragging = False
            
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """ドラッグ状態かを判定"""
        if (not self._is_dragging and 
            (event.pos() - self._drag_start_pos).manhattanLength() > QtWidgets.QApplication.startDragDistance()):
            self._is_dragging = True
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """(Req 4) クリック/ドラッグ終了を検知し、処理を振り分ける"""
        
        if event.button() == LEFT_BUTTON:
            mods = event.modifiers()
            
            # (Req 4) イベントを親クラスに渡す前に、ラバーバンドで選択されたアイテムを取得
            # setDragMode(RubberBandDrag) のおかげで、sceneが選択アイテムを自動で管理している
            selected_items = self.scene().selectedItems() 
            
            start_item = self.itemAt(self._drag_start_pos)
            
            # (Req 4) 選択アイテムからボタンデータ（ButtonData）を抽出するヘルパー
            def get_selected_buttons(items):
                return [
                    item.button_data for item in items
                    if isinstance(item, PickerButtonItem)
                ]

            if self._is_dragging:
                # --- (Req 4) ドラッグ操作の場合 ---
                # (Req 4) ラバーバンドに触れた（含まれた）ボタンのデータを取得
                buttons = get_selected_buttons(selected_items)
                
                if start_item is None:
                    # 背景からのドラッグ
                    if mods == SHIFT_MOD:
                        self.parent_window.on_background_shift_drag(buttons)
                    elif mods == CTRL_MOD:
                        self.parent_window.on_background_ctrl_drag(buttons)
                    else:
                        self.parent_window.on_background_drag(buttons)
                else:
                    # アイテムからのドラッグ
                    self.parent_window.on_button_drag_selected(buttons)
                
            else:
                # --- (Req 4) クリック操作の場合 ---
                if isinstance(start_item, PickerButtonItem):
                    # ボタンクリック
                    if mods == SHIFT_MOD:
                        self.parent_window.on_button_shift_clicked([start_item.button_data])
                    elif mods == CTRL_MOD:
                        self.parent_window.on_button_ctrl_clicked([start_item.button_data])
                    else:
                        self.parent_window.on_button_clicked([start_item.button_data])
                
                elif start_item is None:
                    # 背景クリック
                    self.parent_window.on_background_clicked()

            # (Req 4) 処理後、シーンの選択状態をクリア
            self.scene().clearSelection()
            self._is_dragging = False
        
        # (Req 4) 最後にスーパークラスの処理（ドラッグモードの解除など）を実行
        super().mouseReleaseEvent(event)


class TransparentPickerEditor(QtWidgets.QMainWindow):
    def __init__(self, modules_data, parent=None):
        super().__init__(parent)

        self.modules_data = modules_data
        self.is_transparent = True
        self._initial_scale_done = False

        self.setWindowFlags(self.windowFlags() | FRAMELESS_WINDOW_HINT)
        self.setAttribute(WA_TRANSLUCENT_BACKGROUND, True)

        self.resize(1100, 1100)

        # Layout
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Handle（左上）
        self.handle = DragHandle(self)
        main_layout.addWidget(self.handle)

        # Scene / View
        self.scene = QtWidgets.QGraphicsScene(self)
        self.scene.setSceneRect(-500, -500, 1000, 1000)

        self.view = PickerView(self.scene, self)
        main_layout.addWidget(self.view)

        self.setCentralWidget(main_widget)
        
        # リサイズ
        self.status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.size_grip = QtWidgets.QSizeGrip(self.status_bar)
        self.status_bar.addPermanentWidget(self.size_grip)

        self.apply_style()
        self.load_modules()

    def apply_style(self):
        if self.is_transparent:
            self.setStyleSheet(f"""
                QMainWindow {{ background: transparent; }}
                QFrame#DragHandle {{ background: rgba(60,60,60,180); }}
                QStatusBar {{ background: transparent; border: 0px; }}
                QSizeGrip {{ width: 16px; height: 16px; background: transparent; }}
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background: rgb(50,50,50); }
                QFrame#DragHandle { background: rgb(70,70,70); }
                QStatusBar { background: rgb(50,50,50); border: 0px; }
            """)
        
        if hasattr(self, 'view'):
            self.view.update_background_brush()

    def toggle_transparency(self):
        self.is_transparent = not self.is_transparent
        self.apply_style()

    def load_modules(self):
        for m in self.modules_data:
            item = PickerModuleItem(m, self)
            self.scene.addItem(item)

    # --- クリック/選択ハンドラ関数 ---

    def on_background_clicked(self):
        """背景がクリックされたときに呼び出されます"""
        print("Background Clicked")
        pass

    def on_button_clicked(self, buttons: List[picker_editor.gui.ButtonData]):
        """ボタンが通常クリックされたときに呼び出されます"""
        print(f"Clicked: {[b.name for b in buttons]}")
        pass

    def on_button_shift_clicked(self, buttons: List[picker_editor.gui.ButtonData]):
        """ボタンがShift + クリックされたときに呼び出されます"""
        print(f"Shift-Clicked: {[b.name for b in buttons]}")
        pass

    def on_button_ctrl_clicked(self, buttons: List[picker_editor.gui.ButtonData]):
        """ボタンがCtrl + クリックされたときに呼び出されます"""
        print(f"Ctrl-Clicked: {[b.name for b in buttons]}")
        pass

    def on_button_drag_selected(self, buttons: List[picker_editor.gui.ButtonData]):
        """ボタンがドラッグで選択されたときに呼び出されます（アイテムからドラッグ開始）"""
        print(f"Button-Drag-Selected: {[b.name for b in buttons]}")
        pass

    def on_background_drag(self, buttons: List[picker_editor.gui.ButtonData]):
        """背景から通常ドラッグされたときに呼び出されます"""
        print(f"Background-Drag: {[b.name for b in buttons]}")
        pass

    def on_background_shift_drag(self, buttons: List[picker_editor.gui.ButtonData]):
        """背景からShift + ドラッグされたときに呼び出されます"""
        print(f"Background-Shift-Drag: {[b.name for b in buttons]}")
        pass

    def on_background_ctrl_drag(self, buttons: List[picker_editor.gui.ButtonData]):
        """背景からCtrl + ドラッグされたときに呼び出されます"""
        print(f"Background-Ctrl-Drag: {[b.name for b in buttons]}")
        pass

    # --- ここまで ---

    def showEvent(self, event):
        """ウィンドウが初めて表示されるときに呼び出される"""
        super().showEvent(event)
        if not self._initial_scale_done:
            QtCore.QTimer.singleShot(0, self.scale_view)
            self._initial_scale_done = True


    def scale_view(self):
        """現在のViewのサイズに合わせてSceneをフィットさせる"""
        if not self.view or not self.scene:
            return

        self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)


    def resizeEvent(self, event):
        """ウィンドウの縦横比を常に 1:1（正方形）に保つ"""
        
        if getattr(self, "_lock_resize", False):
            super().resizeEvent(event)
            self.scale_view()
            return

        w = event.size().width()
        h = event.size().height()
        
        old_w = event.oldSize().width()
        old_h = event.oldSize().height()
        if old_w < 0 or old_h < 0:
            super().resizeEvent(event)
            return

        size = max(w, h)

        if w == size and h == size:
            super().resizeEvent(event)
            self.scale_view()
            return

        self._lock_resize = True
        self.resize(size, size)
        self._lock_resize = False
        event.accept()
        return


PICKER_OBJ_NAME = "YSPicker" 

def main(modules_data: List[picker_editor.gui.PickerModuleData]) -> Optional[TransparentPickerEditor]:
    """
    既に同名ウィンドウがあればそれを使い、なければ新規作成して表示します。
    """

    for widget in QtWidgets.QApplication.allWidgets():
        if widget.objectName() == PICKER_OBJ_NAME:
            widget.close()
            widget.deleteLater()

    window = TransparentPickerEditor(modules_data, parent=gui_base.maya_main_window)
    window.setObjectName(PICKER_OBJ_NAME) 
    window.show()
    window.activateWindow()
    return window