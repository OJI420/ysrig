import sys
import math
from dataclasses import dataclass, field
from typing import List, Dict

from PySide6 import QtWidgets, QtCore, QtGui

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
# 表示状態だけを管理するシンプルなボタンアイテム（変更なし）
# ------------------------------------------------------------------------------
class PickerButtonItem(QtWidgets.QGraphicsRectItem):
    """
    自身の状態（通常、ホバー、選択）に応じて色を変えるだけのシンプルなボタン。
    イベント処理は親であるモジュールが一括して行う。
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.color_default = QtGui.QColor("#3498db")
        self.color_hover = QtGui.QColor("#5dade2")
        self.color_selected = QtGui.QColor("#f1c40f")

        self.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        self.set_display_state('default')

    def set_display_state(self, state: str):
        if state == 'selected':
            self.setBrush(self.color_selected)
        elif state == 'hover':
            self.setBrush(self.color_hover)
        else:
            self.setBrush(self.color_default)

# ------------------------------------------------------------------------------
# 回転・スケール機能を実装したモジュールアイテム
# ------------------------------------------------------------------------------
class PickerModuleItem(QtWidgets.QGraphicsItemGroup):
    """
    移動・回転・スケールのすべてをTransformで一元管理するモジュール。
    """
    # スケールの最小値と最大値をクラス定数として定義
    MIN_SCALE = 0.1
    MAX_SCALE = 2.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.child_buttons = []

        # --- Transformation state variables ---
        self.mode = 'none'  # 'move', 'rotate', 'scale'
        self.mouse_press_pos = None
        self.mouse_press_transform = None
        self.center_in_scene = None

        # --- Flags and events ---
        # デフォルトの移動は無効化し、すべて自前で処理する
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False) 
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

    def set_transform_origin_to_center(self):
        """
        変形の中心点を、グループのバウンディングボックスの中心に設定する。
        すべての子アイテムが追加された後に呼び出す必要がある。
        """
        self.setTransformOriginPoint(self.boundingRect().center())

    def add_button(self, button: PickerButtonItem):
        self.child_buttons.append(button)
        self.addToGroup(button)

    def update_child_colors(self):
        state = 'default'
        if self.isSelected():
            state = 'selected'
        elif self.isUnderMouse():
            state = 'hover'
        
        for button in self.child_buttons:
            button.set_display_state(state)
            
    def clamp_to_scene(self):
        """アイテムがシーンの境界からはみ出さないように位置を補正する"""
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
            correction_transform = QtGui.QTransform()
            correction_transform.translate(dx, dy)
            self.setTransform(self.transform() * correction_transform)

    # --- Mouse Event Handlers for All Transformations ---
    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        super().mousePressEvent(event)

        if event.button() == QtCore.Qt.LeftButton:
            self.mode = 'move'
        elif event.button() == QtCore.Qt.RightButton:
            self.mode = 'rotate'
        elif event.button() == QtCore.Qt.MiddleButton:
            self.mode = 'scale'
        else:
            return

        self.mouse_press_pos = event.scenePos()
        self.mouse_press_transform = self.transform()
        if self.mode in ['rotate', 'scale']:
            self.center_in_scene = self.mapToScene(self.transformOriginPoint())
        
        event.accept()

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        t = QtGui.QTransform()
        
        if self.mode == 'move':
            delta = event.scenePos() - self.mouse_press_pos
            t.translate(delta.x(), delta.y())
            
        elif self.mode == 'rotate':
            v_start = self.mouse_press_pos - self.center_in_scene
            v_end = event.scenePos() - self.center_in_scene
            
            angle_start = math.atan2(v_start.y(), v_start.x())
            angle_end = math.atan2(v_end.y(), v_end.x())
            angle_delta_deg = math.degrees(angle_end - angle_start)
            
            t.translate(self.center_in_scene.x(), self.center_in_scene.y())
            t.rotate(angle_delta_deg)
            t.translate(-self.center_in_scene.x(), -self.center_in_scene.y())

        elif self.mode == 'scale':
            v_start = self.mouse_press_pos - self.center_in_scene
            v_end = event.scenePos() - self.center_in_scene
            
            dist_start = math.hypot(v_start.x(), v_start.y())
            if dist_start > 0:
                dist_end = math.hypot(v_end.x(), v_end.y())
                scale_factor = dist_end / dist_start
                
                initial_scale = math.hypot(self.mouse_press_transform.m11(), self.mouse_press_transform.m21())
                
                if initial_scale * scale_factor > self.MAX_SCALE:
                    scale_factor = self.MAX_SCALE / initial_scale
                elif initial_scale * scale_factor < self.MIN_SCALE:
                    scale_factor = self.MIN_SCALE / initial_scale

                t.translate(self.center_in_scene.x(), self.center_in_scene.y())
                t.scale(scale_factor, scale_factor)
                t.translate(-self.center_in_scene.x(), -self.center_in_scene.y())
        
        if self.mode != 'none':
            self.setTransform(self.mouse_press_transform * t)
            self.clamp_to_scene()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if self.mode in ['move', 'rotate', 'scale']:
            self.mode = 'none'
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # --- Other Event Handlers ---
    def wheelEvent(self, event: QtWidgets.QGraphicsSceneWheelEvent):
        """マウスホイールでのスケール処理"""
        # ★★★ ここを event.delta() に修正 ★★★
        delta = event.delta()
        if delta == 0:
            event.ignore()
            return
            
        # スクロール量に応じてスケールファクターを決定
        scale_factor = 1.1 if delta > 0 else 1 / 1.1

        # 現在のスケール値を取得
        current_transform = self.transform()
        current_scale = math.hypot(current_transform.m11(), current_transform.m21())

        # スケール制限をチェック
        if (current_scale * scale_factor > self.MAX_SCALE and scale_factor > 1) or \
           (current_scale * scale_factor < self.MIN_SCALE and scale_factor < 1):
            return

        # マウスカーソル位置を中心としてスケール
        center = event.scenePos()
        t = QtGui.QTransform()
        t.translate(center.x(), center.y())
        t.scale(scale_factor, scale_factor)
        t.translate(-center.x(), -center.y())
        
        self.setTransform(current_transform * t)
        self.clamp_to_scene()
        event.accept()

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent):
        super().hoverEnterEvent(event)
        self.update_child_colors()

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent):
        super().hoverLeaveEvent(event)
        self.update_child_colors()

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
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
# メインのエディタウィンドウ
# ------------------------------------------------------------------------------
class GraphicsEditor(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Picker Editor - Transforms")
        self.setGeometry(100, 100, 800, 600)

        self.scene = QtWidgets.QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 780, 580)
        
        background = QtWidgets.QGraphicsRectItem(self.scene.sceneRect())
        background.setBrush(QtGui.QColor(60, 60, 60))
        background.setZValue(-1)
        self.scene.addItem(background)

        self.view = QtWidgets.QGraphicsView(self.scene, self)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setCentralWidget(self.view)
        
        self.create_module_from_data()

    def create_module_from_data(self):
        test_module_data = PickerModuleData(
            name="arm_module",
            position={'x': 250, 'y': 200},
            buttons=[
                ButtonData(name="a", shape_points=[], position={'x': 20, 'y': 20}),
                ButtonData(name="b", shape_points=[], position={'x': 100, 'y': 60}),
            ]
        )

        module_item = PickerModuleItem()

        for button_data in test_module_data.buttons:
            button_item = PickerButtonItem(0, 0, 80, 40)
            button_item.setPos(button_data.position['x'], button_data.position['y'])
            module_item.add_button(button_item)

        module_item.set_transform_origin_to_center()

        initial_transform = QtGui.QTransform()
        initial_transform.translate(test_module_data.position['x'], test_module_data.position['y'])
        module_item.setTransform(initial_transform)
        
        self.scene.addItem(module_item)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    editor = GraphicsEditor()
    editor.show()
    sys.exit(app.exec_())

