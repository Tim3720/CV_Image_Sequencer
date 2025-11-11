from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (QGraphicsEllipseItem, QGraphicsProxyWidget, QGraphicsSceneMouseEvent)
from PySide6.QtGui import QColor, QBrush, QMouseEvent, QPen, Qt


from .type_vis import TypeVis
from ...core.nodes import Node


class SocketVis(QObject, QGraphicsEllipseItem):

    clicked = Signal()

    def __init__(self, node: Node, idx: int, is_input: bool, parent):
        QObject.__init__(self)
        radius = 10
        QGraphicsEllipseItem.__init__(self, -radius/2, -radius/2, radius, radius, parent)

        self.node = node
        self.is_input = is_input
        self.idx = idx
        if self.is_input:
            self.name, self.dtype = self.node.parameter_template[self.idx]
        else:
            self.name, self.dtype = self.node.result_template[self.idx]

        self.color = QColor.fromRgb(*self.dtype.color)
        self.init_ui()

        self.setZValue(10)

    def init_ui(self):
        self.type_vis = TypeVis(self.node, self.idx, self.dtype, self.name, self.is_input)
        self.type_vis.setStyleSheet("background-color: transparent;")
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(self.type_vis)

        if self.is_input:
            proxy.setPos(self.rect().x() + self.rect().width() + 5,
                         self.rect().y() + (self.rect().height() - proxy.boundingRect().height()) / 2)
        else:
            proxy.setPos(self.rect().x() - proxy.boundingRect().width() - 5 ,
                     self.rect().y() + (self.rect().height() - proxy.boundingRect().height()) / 2)


        self.setBrush(QBrush(self.color))
        self.setPen(QPen(QColor("#222222"), 1))
        self.setZValue(2)
        # self.setPos(self.pos_x, self.pos_y)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        return super().mousePressEvent(event)

