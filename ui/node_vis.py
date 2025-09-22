from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsProxyWidget, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView, QLineEdit, QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPainterPathStroker, QPen, QBrush, QColor, QPainterPath
from PySide6.QtCore import QObject, QPointF, Qt, Signal

from core.node import Node, OutPut, InPut



class IOVis(QGraphicsEllipseItem):

    def __init__(self, port: OutPut | InPut, x, y, radius=10, parent=None):
        super().__init__(-radius/2, -radius/2, radius, radius, parent)  

        self.port = port
        self.is_output = isinstance(self.port, OutPut)
        self.has_connection = False
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

        return super().mousePressEvent(event)


class NodeVis(QObject, QGraphicsRectItem):
    node_changed_signal = Signal()

    def __init__(self, node: Node, width=120, height=60):
        QObject.__init__(self)
        QGraphicsRectItem.__init__(self, 0, 0, width, height)
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

        self.name_edit = QLineEdit(self.node.type_name)
        self.name_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: #f0f0f0;
                border: none;
                font-size: 13px;
            }
        """)
        self.proxy = QGraphicsProxyWidget(self)
        self.proxy.setWidget(self.name_edit)
        rect = self.rect()
        self.proxy.setGeometry(
            rect.left() + 5,
            rect.top() + rect.height()/2 - 12,  # vertical centering
            rect.width() - 10,
            24
        )

        for i in self.node.inputs:
            self.input_port = IOVis(i, 0, height / 2, parent=self)
        for o in self.node.outputs:
            self.output_port = IOVis(o, width, height / 2, parent=self)


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

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
            self.node_changed_signal.emit()
        return super().itemChange(change, value)


class Connection(QGraphicsPathItem):
    def __init__(self, start_port):
        super().__init__()
        self.start_port: IOVis = start_port
        self.end_port: IOVis | None = None
        self.setPen(QPen(QColor("#f0f0f0"), 2))
        self.update_temp_path(start_port.scenePos(), start_port.scenePos())

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

    def disconnect(self):
        if self.end_port is None:
            return

        self.end_port.has_connection = False
        self.end_port = None

    def connect(self, end_port: IOVis):
        end_port.has_connection = True
        self.end_port = end_port
        self.update_path()
