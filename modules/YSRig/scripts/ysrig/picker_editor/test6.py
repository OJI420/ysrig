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
# 任意の形状を描画できるように変更したボタンアイテム
# ------------------------------------------------------------------------------
class PickerButtonItem(QtWidgets.QGraphicsPathItem):
    """
    QGraphicsPathItemを継承し、ButtonDataのshape_pointsから任意の形状を生成する。
    """
    def __init__(self, button_data: ButtonData, parent=None):
        super().__init__(parent)
        
        # --- ButtonDataから形状(QPainterPath)を生成 ---
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

        # --- 表示色の設定（ホバー色を削除） ---
        self.color_default = QtGui.QColor("#3498db")
        self.color_selected = QtGui.QColor("#f1c40f")

        self.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        self.set_display_state('default')

    def set_display_state(self, state: str):
        # --- 表示状態の更新（ホバー関連を削除） ---
        if state == 'selected':
            self.setBrush(self.color_selected)
        else:
            self.setBrush(self.color_default)

# ------------------------------------------------------------------------------
# 回転・スケール機能を実装したモジュールアイテム
# ------------------------------------------------------------------------------
class PickerModuleItem(QtWidgets.QGraphicsItemGroup):
    """
    移動・回転・スケールのすべてをTransformで一元管理するモジュール。
    """
    MIN_SCALE = 0.1
    MAX_SCALE = 2.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.child_buttons = []

        self.mode = 'none'
        self.mouse_press_pos = None
        self.mouse_press_transform = None
        self.center_in_scene = None

        # --- ホバーイベントの受付を削除 ---
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False) 
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)

    def set_transform_origin_to_center(self):
        self.setTransformOriginPoint(self.boundingRect().center())

    def add_button(self, button: PickerButtonItem):
        self.child_buttons.append(button)
        self.addToGroup(button)

    def update_child_colors(self):
        # --- 色更新ロジックからホバー関連を削除 ---
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
            correction_transform = QtGui.QTransform()
            correction_transform.translate(dx, dy)
            self.setTransform(self.transform() * correction_transform)

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

    def wheelEvent(self, event: QtWidgets.QGraphicsSceneWheelEvent):
        delta = event.delta()
        if delta == 0:
            event.ignore()
            return
            
        scale_factor = 1.1 if delta > 0 else 1 / 1.1
        current_transform = self.transform()
        current_scale = math.hypot(current_transform.m11(), current_transform.m21())

        if (current_scale * scale_factor > self.MAX_SCALE and scale_factor > 1) or \
           (current_scale * scale_factor < self.MIN_SCALE and scale_factor < 1):
            return

        center = event.scenePos()
        t = QtGui.QTransform()
        t.translate(center.x(), center.y())
        t.scale(scale_factor, scale_factor)
        t.translate(-center.x(), -center.y())
        
        self.setTransform(current_transform * t)
        self.clamp_to_scene()
        event.accept()

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            QtCore.QTimer.singleShot(0, self.update_child_colors)
        return super().itemChange(change, value)

    def paint(self, painter: QtGui.QPainter, option, widget=None):
        # --- 透明ブラシを削除し、NoBrushに戻す ---
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
        self.setWindowTitle("Picker Editor - With Controls")
        
        # --- Window Size ---
        self.view_size = 1000
        self.panel_width = 250
        self.setFixedSize(self.view_size + self.panel_width, self.view_size)

        # --- Main Layout Setup ---
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Graphics View (Left) ---
        self.scene = QtWidgets.QGraphicsScene(self)
        self.scene.setSceneRect(-self.view_size / 2, -self.view_size / 2, self.view_size, self.view_size)
        
        background = QtWidgets.QGraphicsRectItem(self.scene.sceneRect())
        background.setBrush(QtGui.QColor(60, 60, 60))
        background.setZValue(-1)
        self.scene.addItem(background)

        guideline_pen = QtGui.QPen(QtGui.QColor(120, 120, 120), 1, QtCore.Qt.DashLine)
        vertical_line = QtWidgets.QGraphicsLineItem(0, -self.view_size / 2, 0, self.view_size / 2)
        vertical_line.setPen(guideline_pen)
        vertical_line.setZValue(-0.5)
        self.scene.addItem(vertical_line)
        horizontal_line = QtWidgets.QGraphicsLineItem(-self.view_size / 2, 0, self.view_size / 2, 0)
        horizontal_line.setPen(guideline_pen)
        horizontal_line.setZValue(-0.5)
        self.scene.addItem(horizontal_line)

        self.view = QtWidgets.QGraphicsView(self.scene, self)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        main_layout.addWidget(self.view)
        
        # --- Control Panel (Right) ---
        control_panel = QtWidgets.QWidget()
        control_panel.setFixedWidth(self.panel_width)
        control_panel.setStyleSheet("background-color: #2c3e50;") # Dark blue
        main_layout.addWidget(control_panel)
        
        # --- Finalize Layout ---
        self.setCentralWidget(main_widget)
        
        for mod in [mod1, mod2]:
            self.create_module_from_data(mod)

    def create_module_from_data(self, module_data: PickerModuleData):
        module_item = PickerModuleItem()

        for button_data in module_data.buttons:
            button_item = PickerButtonItem(button_data)
            button_item.setPos(button_data.position['x'], button_data.position['y'])
            module_item.add_button(button_item)

        module_item.set_transform_origin_to_center()

        initial_transform = QtGui.QTransform()
        initial_transform.translate(module_data.position['x'], module_data.position['y'])
        module_item.setTransform(initial_transform)
        
        self.scene.addItem(module_item)

    def showEvent(self, event: QtGui.QShowEvent):
        """ウィンドウが表示された直後に一度だけ呼ばれる"""
        super().showEvent(event)
        # シーン全体が常にビューに収まるように調整し、スクロールバーを不要にする
        self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)


# ------------------------------------------------------------------------------
# ユーザー提供のデータ（変更なし）
# ------------------------------------------------------------------------------
mod1 = PickerModuleData(
    name="sh",
    position={'x': -400, 'y': -150},
    buttons=[
        ButtonData(
            name="s", 
            shape_points=[
                {'pos': [0, 0]},
                {'pos': [40, 0]},
                {'pos': [40, 40]},
                {'pos': [0, 40]},
                {'pos': [0, 0]}
            ],
            position={'x': 0, 'y': 0}
        ),
        ButtonData(
            name="u", 
            shape_points=[
                {'pos': [0, 10]},
                {'pos': [60, 5]},
                {'pos': [60, 35]},
                {'pos': [0, 30]},
                {'pos': [0, 10]}
            ],
            position={'x': 50, 'y': 0}
        ),
        ButtonData(
            name="e", 
            shape_points=[
                {'pos': [0, 0]},
                {'pos': [40, 0]},
                {'pos': [40, 40]},
                {'pos': [0, 40]},
                {'pos': [0, 0]}
            ],
            position={'x': 120, 'y': 0}
        ),
        ButtonData(
            name="b", 
            shape_points=[
                {'pos': [0, 5]},
                {'pos': [60, 10]},
                {'pos': [60, 30]},
                {'pos': [0, 35]},
                {'pos': [0, 5]}
            ],
            position={'x': 170, 'y': 0}
        ),
        ButtonData(
            name="u", 
            shape_points=[
                {'pos': [0, 10]},
                {'pos': [30, 0]},
                {'pos': [50, 0]},
                {'pos': [50, 40]},
                {'pos': [30, 40]},
                {'pos': [0, 30]},
                {'pos': [0, 10]}
            ],
            position={'x': 240, 'y': 0}
        )
    ]
)

mod2 = PickerModuleData(
    name="sh",
    position={'x': 100, 'y': 100},
    buttons=[
        ButtonData(
            name="e", 
            shape_points=[
                {'pos': [30, 0]},
                {'pos': [0, -30]},
                {'pos': [70, -30]},
                {'pos': [40, 0]},
                {'pos': [30, 0]}
            ],
            position={'x': 0, 'y': 0}
        ),
        ButtonData(
            name="s", 
            shape_points=[
                {'pos': [0, 0]},
                {'pos': [5, -30]},
                {'pos': [65, -30]},
                {'pos': [70, 0]},
                {'pos': [0, 0]}
            ],
            position={'x': 0, 'y': -40}
        ),
        ButtonData(
            name="u", 
            shape_points=[
                {'pos': [5, 0]},
                {'pos': [0, -30]},
                {'pos': [70, -30]},
                {'pos': [65, 0]},
                {'pos': [5, 0]}
            ],
            position={'x': 0, 'y': -80}
        ),
        ButtonData(
            name="e", 
            shape_points=[
                {'pos': [0, 0]},
                {'pos': [20, -10]},
                {'pos': [30, -30]},
                {'pos': [40, -30]},
                {'pos': [50, -10]},
                {'pos': [70, 0]},
                {'pos': [0, 0]}
            ],
            position={'x': 0, 'y': -120}
        )
    ]
)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    editor = GraphicsEditor()
    editor.show()
    sys.exit(app.exec_())

