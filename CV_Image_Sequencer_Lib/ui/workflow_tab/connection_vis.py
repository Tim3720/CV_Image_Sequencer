

from typing import Optional
from PySide6.QtCore import QObject, QPoint, QPointF, Signal
from PySide6.QtGui import QColor, QPainterPath, QPainterPathStroker, QPen, Qt
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsSceneMouseEvent

from .socket_vis import SocketVis


class ConnectionVis(QObject, QGraphicsPathItem):

    delete = Signal()

    def __init__(self):
        QObject.__init__(self)
        QGraphicsPathItem.__init__(self)

        self.input_socket: Optional[SocketVis] = None
        self.output_socket: Optional[SocketVis] = None

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent, True)
        self.setZValue(-1)


    def add_input_socket(self, socket_vis: SocketVis):
        self.input_socket = socket_vis
        self.setPen(QPen(QColor.fromRgb(*socket_vis.dtype.color), 2))

    def add_output_socket(self, socket_vis: SocketVis):
        self.output_socket = socket_vis
        self.setPen(QPen(QColor.fromRgb(*socket_vis.dtype.color), 2))

    def update_path(self, stop: Optional[QPointF] = None):
        if self.output_socket is None or self.input_socket is None:
            if not stop is None:
                if not self.output_socket is None:
                    start = self.output_socket.scenePos()
                    end = stop
                elif not self.input_socket is None:
                    start = self.input_socket.scenePos()
                    end = stop
                else:
                    return
            else:
                return
        else:
            start = self.output_socket.scenePos()
            end = self.input_socket.scenePos()

        path = QPainterPath()
        path.moveTo(start)
        dx = (end.x() - start.x()) * 0.5
        control1 = QPointF(start.x() + dx, start.y())
        control2 = QPointF(end.x() - dx, end.y())
        path.cubicTo(control1, control2, end)
        self.setPath(path)

    def shape(self):
        path = super().shape()
        stroker = QPainterPathStroker()
        stroker.setWidth(10)  # clickable area 10px wide
        return stroker.createStroke(path)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self.delete.emit()
        return super().mousePressEvent(event)
