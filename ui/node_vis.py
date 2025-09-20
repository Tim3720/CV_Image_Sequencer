from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView, QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath
from PySide6.QtCore import Qt, Signal

from utils.node import Node



class IOVis(QGraphicsEllipseItem):

    clicked_signal = Signal()

    def __init__(self, parent, x, y, radius=10, is_output=False):
        super().__init__(-radius/2, -radius/2, radius, radius, parent)  

        self.is_output = is_output
        self.is_selected = False

        self.default_color = QColor("#aaaaaa")
        self.selected_color = QColor("#ffcc00")
        self.hover_color = QColor("#5d85c7")
        self.setBrush(QBrush(self.default_color))
        self.setPen(QPen(QColor("#222222"), 1))
        self.setPos(x, y)

        self.setAcceptHoverEvents(True)


    def hoverEnterEvent(self, event):
        if not self.is_selected:
            self.setBrush(QBrush(QColor("#5d85c7")))  # blue highlight
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.is_selected:
            self.setBrush(QBrush(QColor("#aaaaaa")))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        # Toggle selection
        self.is_selected = not self.is_selected
        if self.is_selected:
            self.setBrush(QBrush(self.selected_color))
        else:
            self.setBrush(QBrush(self.default_color))
        super().mousePressEvent(event)


class NodeVis(QGraphicsRectItem):

    def __init__(self, node: Node, width=120, height=60):
        super().__init__(0, 0, width, height)
        self.node = node
        self.inputs: list[IOVis] = []
        self.outputs: list[IOVis] = []

        self.bg_default = QColor("#3d3d3d")
        self.bg_selected = QColor("#2b2b2b")
        self.border_default = QColor("#5d5d5d")
        self.border_selected = QColor("#5d85c7")

        self.setBrush(QBrush(self.bg_default))
        self.setPen(QPen(self.border_default, 2))
        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        for _ in self.node.inputs:
            self.input_port = IOVis(self, 0, height / 2, is_output=False)
        for _ in self.node.outputs:
            self.output_port = IOVis(self, width, height / 2, is_output=True)


    def paint(self, painter, option, widget=None):
        # Change style if selected
        if self.isSelected():
            brush = QBrush(self.bg_selected)
            pen = QPen(self.border_selected, 2)
        else:
            brush = QBrush(self.bg_default)
            pen = QPen(self.border_default, 2)
        
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRect(self.rect())

