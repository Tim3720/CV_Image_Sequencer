from PySide6.QtWidgets import (QGraphicsItem, QGraphicsPathItem)
from PySide6.QtGui import QPainterPathStroker, QPen, QColor, QPainterPath
from PySide6.QtCore import QObject, QPointF, Qt, Signal

from .node_vis import IOPort

class Connection(QObject, QGraphicsPathItem):
    delete_connection_sigal = Signal(object)

    def __init__(self, start_port: IOPort):
        QObject.__init__(self)
        QGraphicsPathItem.__init__(self)
        self.start_port: IOPort = start_port
        self.end_port: IOPort | None = None
        self.setPen(QPen(QColor.fromRgb(*start_port.node.data_type.color), 2))
        self.update_temp_path(start_port.scenePos(), start_port.scenePos())
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent, True)

    def shape(self):
        path = super().shape()
        stroker = QPainterPathStroker()
        stroker.setWidth(10)  # clickable area 10px wide
        return stroker.createStroke(path)

    def update_temp_path(self, start, end):
        path = QPainterPath()
        path.moveTo(start)
        dx = (end.x() - start.x()) * 0.5
        control1 = QPointF(start.x() + dx, start.y())
        control2 = QPointF(end.x() - dx, end.y())
        path.cubicTo(control1, control2, end)
        self.setPath(path)

    def update_path(self):
        if self.end_port is None:
            return
        start = self.start_port.scenePos()
        end = self.end_port.scenePos()
        path = QPainterPath()
        path.moveTo(start)
        dx = (end.x() - start.x()) * 0.5
        control1 = QPointF(start.x() + dx, start.y())
        control2 = QPointF(end.x() - dx, end.y())
        path.cubicTo(control1, control2, end)
        self.setPath(path)

    def disconnect_path(self):
        if self.end_port is None:
            return
        self.end_port = None

    def connect_path(self, end_port: IOPort):
        self.end_port = end_port
        self.update_path()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.RightButton and self.end_port is not None:
            print("delete")
            self.delete_connection_sigal.emit(self)
        else:
            return super().mousePressEvent(event)
