import sys
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
# 1. 表示状態だけを管理するシンプルなボタンアイテム
# ------------------------------------------------------------------------------
class PickerButtonItem(QtWidgets.QGraphicsRectItem):
    """
    自身の状態（通常、ホバー、選択）に応じて色を変えるだけのシンプルなボタン。
    イベント処理は親であるモジュールが一括して行う。
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # --- 色の定義 ---
        self.color_default = QtGui.QColor("#3498db")   # 通常時の青色
        self.color_hover = QtGui.QColor("#5dade2")     # マウスオーバー時の明るい青
        self.color_selected = QtGui.QColor("#f1c40f")  # 選択時の黄色

        self.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        self.set_display_state('default') # 初期色を設定

    def set_display_state(self, state: str):
        """親モジュールからの指示で色を更新する"""
        if state == 'selected':
            self.setBrush(self.color_selected)
        elif state == 'hover':
            self.setBrush(self.color_hover)
        else: # 'default'
            self.setBrush(self.color_default)

# ------------------------------------------------------------------------------
# 2. 複数のボタンを束ね、状態を一括管理するモジュールアイテム
# ------------------------------------------------------------------------------
class PickerModuleItem(QtWidgets.QGraphicsItemGroup):
    """
    QGraphicsItemGroupを使い、子ボタンのイベントと状態をまとめて管理する。
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.child_buttons = []

        # --- フラグとイベントの設定 ---
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        # グループ全体でマウスオーバーイベントを受け取る
        self.setAcceptHoverEvents(True)

    def add_button(self, button: PickerButtonItem):
        """子ボタンをリストとグループに追加する"""
        self.child_buttons.append(button)
        self.addToGroup(button) # QGraphicsItemGroupの機能でグループ化

    def update_child_colors(self):
        """自身の状態（選択/ホバー）をすべての子ボタンに反映させる"""
        state = 'default'
        if self.isSelected():
            state = 'selected'
        elif self.isUnderMouse():
            state = 'hover'
        
        for button in self.child_buttons:
            button.set_display_state(state)

    # --- イベントハンドラ ---
    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent):
        """グループの範囲にマウスが入ったら色を更新"""
        super().hoverEnterEvent(event)
        self.update_child_colors()

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent):
        """グループの範囲からマウスが出たら色を更新"""
        super().hoverLeaveEvent(event)
        self.update_child_colors()

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value):
        """選択状態が変化した時に呼ばれる"""
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            # 状態変化が完了した直後に色更新を実行
            QtCore.QTimer.singleShot(0, self.update_child_colors)
        return super().itemChange(change, value)

    def paint(self, painter: QtGui.QPainter, option, widget=None):
        """選択時に破線の枠線を描画する"""
        # QGraphicsItemGroupはデフォルトでは何も描画しないため、自前で描画処理を実装
        if self.isSelected():
            pen = QtGui.QPen(QtGui.QColor(200, 200, 200), 1, QtCore.Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            # boundingRect()はグループが自動計算する、子要素全体を囲む矩形
            painter.drawRect(self.boundingRect())

# ------------------------------------------------------------------------------
# メインのエディタウィンドウ
# ------------------------------------------------------------------------------
class GraphicsEditor(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Picker Editor - Module Controls")
        self.setGeometry(100, 100, 800, 600)

        # --- シーンとビューの基本設定 ---
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
        """データに基づいてモジュールを作成する"""
        test_module_data = PickerModuleData(
            name="arm_module",
            position={'x': 150, 'y': 100},
            buttons=[
                ButtonData(name="a", shape_points=[], position={'x': 20, 'y': 20}),
                ButtonData(name="b", shape_points=[], position={'x': 100, 'y': 60}),
            ]
        )

        # 1. まずモジュール（グループ）を作成
        module_item = PickerModuleItem()

        # 2. 子ボタンを作成し、モジュールに追加していく
        for button_data in test_module_data.buttons:
            # ボタンの位置はモジュール内での相対座標
            button_item = PickerButtonItem(0, 0, 80, 40)
            button_item.setPos(button_data.position['x'], button_data.position['y'])
            module_item.add_button(button_item)

        # 3. モジュール全体のシーン上の位置を設定
        module_item.setPos(test_module_data.position['x'], test_module_data.position['y'])

        # 4. 最後にモジュールをシーンに追加
        self.scene.addItem(module_item)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    editor = GraphicsEditor()
    editor.show()
    sys.exit(app.exec_())

