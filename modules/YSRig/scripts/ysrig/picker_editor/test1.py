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
# メインのエディタウィンドウ
# ------------------------------------------------------------------------------
class TransparentPickerEditor(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transparent Picker Editor")
        self.setGeometry(200, 200, 500, 400) # 少し小さめに設定

        # --- ★★★ 1. ウィンドウを透明にするための設定 ★★★ ---
        # OSの標準フレームを削除する
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # 背景の透過を有効にする
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # ウィンドウをドラッグで移動するための変数を初期化
        self.drag_start_position = None

        # --- 2. シーンとビューの作成 ---
        self.scene = QtWidgets.QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 500, 400)
        
        self.view = QtWidgets.QGraphicsView(self.scene, self)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # --- ★★★ 3. ビューとシーンの背景も透明に設定 ★★★ ---
        self.view.setBackgroundBrush(QtCore.Qt.NoBrush)
        self.view.setFrameShape(QtWidgets.QFrame.NoFrame) # ビューの枠線を消す
        self.scene.setBackgroundBrush(QtCore.Qt.NoBrush)
        
        # --- ★★★ 追加の修正 ★★★ ---
        # ビューポート自体の自動背景塗りつぶしを無効にします。
        # これが透明化が機能しない場合の一般的な解決策です。
        self.view.viewport().setAutoFillBackground(False)
        
        self.setCentralWidget(self.view)

        # --- 4. モジュールを作成 ---
        self.create_module_from_data()

        # --- ★★★ 5. 閉じるボタンを自前で追加 ★★★ ---
        # フレームがないため、ウィンドウを閉じる手段が必要
        self.close_button = QtWidgets.QPushButton("X", self)
        self.close_button.setGeometry(self.width() - 32, 2, 30, 30)
        self.close_button.setStyleSheet("background-color: #555; color: white; border-radius: 15px; font-weight: bold;")
        self.close_button.clicked.connect(self.close)


    def create_module_from_data(self):
        """データに基づいてモジュールを作成"""
        test_module_data = PickerModuleData(
            name="arm_module",
            position={'x': 150, 'y': 100},
            buttons=[
                ButtonData(name="a", shape_points=[], position={'x': 20, 'y': 20}),
                ButtonData(name="b", shape_points=[], position={'x': 100, 'y': 60}),
            ]
        )

        parent_item = QtWidgets.QGraphicsRectItem(0, 0, 200, 120)
        parent_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        parent_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        parent_item.setBrush(QtGui.QColor(100, 100, 100, 150)) # 半透明のグレーで親の範囲を示す
        parent_item.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200), 1, QtCore.Qt.DashLine))
        parent_item.setPos(test_module_data.position['x'], test_module_data.position['y'])
        self.scene.addItem(parent_item)

        for button_data in test_module_data.buttons:
            child_item = QtWidgets.QGraphicsRectItem(0, 0, 80, 40, parent_item)
            child_item.setBrush(QtGui.QBrush(QtCore.Qt.cyan))
            child_item.setPen(QtGui.QPen(QtCore.Qt.black))
            child_item.setPos(button_data.position['x'], button_data.position['y'])

    # --- ★★★ 6. マウスイベントでウィンドウ移動を実装 ★★★ ---
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """マウスボタンが押された時の処理"""
        if event.button() == QtCore.Qt.LeftButton:
            # 現在のマウスカーソル位置を、ウィンドウの左上からの相対位置で記憶
            self.drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        """マウスがドラッグされた時の処理"""
        # drag_start_positionが設定されていれば（つまり左ボタンが押されていれば）
        if self.drag_start_position is not None:
            # 現在のカーソル位置から記憶した相対位置を引いて、ウィンドウの新しい左上位置を計算
            self.move(event.globalPosition().toPoint() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        """マウスボタンが離された時の処理"""
        self.drag_start_position = None
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    editor = TransparentPickerEditor()
    editor.show()
    sys.exit(app.exec_())

