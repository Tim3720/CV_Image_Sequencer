from typing import Any
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import (QGraphicsEllipseItem, QWidget, QGraphicsRectItem, QHBoxLayout, QLabel,
                               QGraphicsItem, QGraphicsProxyWidget)
from PySide6.QtGui import QColor, QBrush, QPen

from .type_vis import TypeVis
from ..styled_widgets import StyledButton
from ...assets.styles.style import STYLE
from ...core.nodes import InputSocket, Socket


class SocketVis(QObject, QGraphicsEllipseItem):

    def __init__(self, socket: Socket, parent):
        QObject.__init__(self)
        radius = 10
        QGraphicsEllipseItem.__init__(self, -radius/2, -radius/2, radius, radius, parent)

        self.socket = socket

        self.color = QColor.fromRgb(*self.socket.dtype.color)
        self.init_ui()

        self.setZValue(2)

    def init_ui(self):
        self.widget = TypeVis(self.socket)

        type_vis = TypeVis(self.socket)
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(type_vis)

        if isinstance(self.socket, InputSocket):
            proxy.setPos(self.rect().x() + self.rect().width() + 5,
                         self.rect().y() + (self.rect().height() - proxy.boundingRect().height()) / 2)
        else:
            proxy.setPos(self.rect().x() - proxy.boundingRect().width() - 5 ,
                     self.rect().y() + (self.rect().height() - proxy.boundingRect().height()) / 2)


        self.setBrush(QBrush(self.color))
        self.setPen(QPen(QColor("#222222"), 1))
        self.setZValue(2)
        # self.setPos(self.pos_x, self.pos_y)

