from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene, QGraphicsView, QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath

from ui.node_vis import NodeVis
from utils.node import Node
from utils.node_manager import NodeManager

class WorkflowWidget(QWidget):

    def __init__(self, node_manager: NodeManager, parent=None):
        super().__init__(parent)

        self.node_manager = node_manager

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)


        test_node = NodeVis(Node())

        self.scene.addItem(test_node)

        main_layout.addWidget(self.view)
        self.view.show()

