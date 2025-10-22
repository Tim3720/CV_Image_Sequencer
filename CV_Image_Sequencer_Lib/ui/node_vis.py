from enum import Enum
from PySide6.QtWidgets import (QFrame, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem,
                               QGraphicsProxyWidget, QGraphicsRectItem, QGraphicsScene,
                               QGraphicsTextItem, QGraphicsView, QHBoxLayout, QLineEdit,
                               QPushButton, QSpinBox, QWidget, QLabel, QVBoxLayout, QComboBox)
from PySide6.QtGui import QFont, QPainterPathStroker, QPen, QBrush, QColor, QPainterPath, qRgba
from PySide6.QtCore import QObject, QPointF, Qt, Signal

from CV_Image_Sequencer_Lib.ui.settings_vis import SettingsVis
from ..core.node import Node, OutPut, InPut
from ..utils.types import DictType, Scalar

def port_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("font-size: 11px; border: none;")
    return label

def port_dropdown(port: InPut | OutPut) -> QFrame: 
        if not issubclass(port.data_type, DictType): # enum like
            raise ValueError("Wrong type passed to port_dropdown")

        widget = QFrame()
        widget.setStyleSheet("background-color: transparent; border: none;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)


        label = port_label(port.label)

        dropdown = QComboBox()
        for option in port.data_type.value_dict.keys():
            dropdown.addItem(option, option)

        if port.data_type.value is not None:
            dropdown.setCurrentText(port.data_type.value)
        else:
            default = port.data_type.default_value
            if default is not None:
                dropdown.setCurrentText(default)

        dropdown.setStyleSheet("""
                QComboBox {
                    font-size: 11px;
                    color: white;
                    border: 2px solid #333;
                }
                QComboBox QAbstractItemView {
                    font-size: 11px;  /* font size for the drop-down items */
                    background: #2b2b2b;
                    color: white;
                }
        """)

        if isinstance(port, InPut):
            dropdown.currentTextChanged.connect(lambda x:
                                                port.data_update(port.data.set_value(x)))
        else:
            dropdown.setEditable(False)

        layout.addWidget(label)
        layout.addWidget(dropdown)
        return widget

def port_line_edit(port: InPut | OutPut) -> QFrame:
    if not issubclass(port.data_type, Scalar): # enum like
        raise ValueError("Wrong type passed to port_line_edit")
    widget = QFrame()
    widget.setStyleSheet("background-color: transparent; border: none;")
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    label = port_label(port.label)

    edit = QLineEdit()
    edit.setFixedWidth(50)

    edit.setStyleSheet("""
            QLineEdit {
                font-size: 11px;
                color: white;
                border: 2px solid #333;
            }
    """)

    if isinstance(port, InPut):
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(edit, alignment=Qt.AlignmentFlag.AlignRight)
        edit.textChanged.connect(lambda x: port.data_update(port.data.set_value_from_string(x)))
        if port.data.value is not None:
            edit.setText(str(port.data.value))
    else:
        edit.setReadOnly(True)
        layout.addWidget(edit, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignRight)
        port.computation_finished_signal.connect(lambda x: edit.setText(str(x.value)))
    return widget

def create_proxy(parent: QGraphicsItem, widget: QWidget, x: float, y: float, w: float, h: float):
    proxy = QGraphicsProxyWidget(parent)
    proxy.setWidget(widget)
    proxy.setGeometry(x, y, w, h)

def create_proxy_no_position(parent: QGraphicsItem, widget: QWidget):
    proxy = QGraphicsProxyWidget(parent)
    proxy.setWidget(widget)
    return proxy


class IOPort(QObject, QGraphicsEllipseItem):
    port_press_signal = Signal()

    def __init__(self, port: OutPut | InPut, x, y, parent, parent_node: Node) -> None:
        QObject.__init__(self)
        radius = 10
        QGraphicsEllipseItem.__init__(self, -radius/2, -radius/2, radius, radius, parent)

        self.parent = parent
        self.parent_node = parent_node
        self.port = port

        self.color = QColor("#aaaaaa")

        if issubclass(port.data_type, DictType): # enum like
            widget = port_dropdown(port)
            proxy = create_proxy_no_position(self, widget)
        elif issubclass(port.data_type, Scalar):
            widget = port_line_edit(port)
            proxy = create_proxy_no_position(self, widget)
        else:
            proxy = QGraphicsTextItem(port.label)
            proxy.setDefaultTextColor(Qt.GlobalColor.white)
            proxy.setParentItem(self)

        # bg_rect = QGraphicsRectItem(proxy.boundingRect(), proxy)
        # bg_rect.setPen(QPen(Qt.GlobalColor.red, 1))

        if isinstance(port, OutPut):
            proxy.setPos(self.rect().x() - proxy.boundingRect().width() - 5 ,
                         self.rect().y() + (self.rect().height() - proxy.boundingRect().height()) / 2)
        else:
            proxy.setPos(self.rect().x() + self.rect().width() + 5,
                         self.rect().y() + (self.rect().height() - proxy.boundingRect().height()) / 2)

        self.setBrush(QBrush(self.color))
        self.setPen(QPen(QColor("#222222"), 1))
        self.setZValue(2)
        self.setPos(x, y)

        self.width = proxy.boundingRect().width()


    def mousePressEvent(self, event) -> None:
        self.port_press_signal.emit()
        return super().mousePressEvent(event)


class NodeVis(QObject, QGraphicsRectItem):
    node_position_changed_signal = Signal()
    double_clicked_signal = Signal(object)

    def __init__(self, node: Node, width=120, height=60):
        QObject.__init__(self)
        QGraphicsRectItem.__init__(self, 0, 0, width, height)

        self.node = node
        self.input_ports: list[IOPort] = []
        self.output_ports: list[IOPort] = []

        self.init_ui()


    def init_ui(self):
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

        ########################
        ## Label:
        ########################
        rect = self.rect()
        name_rect = QGraphicsRectItem(0, 0, rect.width() - 2, 25, self)
        name_rect.setBrush(QBrush(QColor("#5d5d5d")))
        name_rect.setPen(QPen(self.border_default, 0))

        self.name_label = QLabel(self.node.name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #f0f0f0;
                border: none;
                font-size: 13px;
            }
        """)
        create_proxy(self, self.name_label, rect.left() + 5, rect.top() + 5, rect.width()
                     - 10, 15)

        ########################
        ## Inputs/Outputs:
        ########################
        y = name_rect.rect().y() + name_rect.rect().height() + 12
        max_width = name_rect.rect().width()
        for o in self.node.outputs:
            output_port = IOPort(o, self.rect().width(), y,
                                 parent=self, parent_node=self.node)
            self.output_ports.append(output_port)
            y += output_port.rect().height() + 12
            if output_port.width > max_width:
                max_width = output_port.width

        for i in self.node.inputs:
            input_port = IOPort(i, 0, y, parent=self,
                                parent_node=self.node)
            self.input_ports.append(input_port)
            y += input_port.rect().height() + 12
            if input_port.width > max_width:
                max_width = input_port.width


        name_rect.setRect(name_rect.rect().x() + 1, name_rect.rect().y() + 1, max_width + 18, name_rect.rect().height())
        self.setRect(self.rect().x(), self.rect().y(), max_width + 20, y + 10)
        for o in self.output_ports:
            o.setPos(self.rect().width(), o.pos().y())


    def paint(self, painter, option, widget=None):
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
            self.node_position_changed_signal.emit()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event) -> None:
        self.double_clicked_signal.emit(self.node)
        return super().mouseDoubleClickEvent(event)

    def lock_movement(self):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

    def unlock_movement(self):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)


class Connection(QObject, QGraphicsPathItem):
    delete_connection_sigal = Signal()

    def __init__(self, start_port):
        QObject.__init__(self)
        QGraphicsPathItem.__init__(self)
        self.start_port: IOPort = start_port
        self.end_port: IOPort | None = None
        self.setPen(QPen(QColor("#f0f0f0"), 2))
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
            self.delete_connection_sigal.emit()
        else:
            return super().mousePressEvent(event)
