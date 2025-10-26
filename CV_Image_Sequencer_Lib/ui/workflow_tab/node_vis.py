from PySide6.QtWidgets import (QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem,
                               QGraphicsRectItem, QGraphicsTextItem, QLabel, QHBoxLayout, QPushButton, QWidget)
from PySide6.QtGui import QIcon, QPainterPathStroker, QPen, QBrush, QColor, QPainterPath
from PySide6.QtCore import QObject, QPointF, Qt, Signal

from CV_Image_Sequencer_Lib.assets.styles.style import STYLE
from CV_Image_Sequencer_Lib.ui.styled_widgets import StyledButton
from .help_dialog import HelpDialog

from .type_vis import (BoolVis, EnumVisInput, EnumVisOutput, ScalarVisInput, ScalarVisOutput, create_proxy_no_position, create_proxy)
from CV_Image_Sequencer_Lib.core.node_base import Node, OutPut, InPut
from CV_Image_Sequencer_Lib.utils.types import Bool, DictType, Scalar


class IOPort(QObject, QGraphicsEllipseItem):
    port_press_signal = Signal()

    def __init__(self, port: OutPut | InPut, x, y, parent, parent_node: Node) -> None:
        QObject.__init__(self)
        radius = 10
        QGraphicsEllipseItem.__init__(self, -radius/2, -radius/2, radius, radius, parent)

        self.parent = parent
        self.parent_node = parent_node
        self.port = port

        self.color = QColor.fromRgb(*port.data.color)

        self.data_widget = None
        if issubclass(type(port.data), DictType): # enum like
            if isinstance(port, OutPut):
                self.data_widget = EnumVisOutput(port)
            else:
                self.data_widget = EnumVisInput(port)
            proxy = create_proxy_no_position(self, self.data_widget)
        elif issubclass(type(port.data), Scalar):
            if isinstance(port, OutPut):
                self.data_widget = ScalarVisOutput(port)
            else:
                self.data_widget = ScalarVisInput(port)
            proxy = create_proxy_no_position(self, self.data_widget)
        elif isinstance(port.data, Bool):
            self.data_widget = BoolVis(port)
            proxy = create_proxy_no_position(self, self.data_widget)
        else:
            proxy = QGraphicsTextItem(port.label)
            proxy.setDefaultTextColor(QColor(STYLE["textcolor"]))
            proxy.setParentItem(self)

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
    delete_signal = Signal(object)

    def __init__(self, node: Node, width=120, height=60):
        QObject.__init__(self)
        QGraphicsRectItem.__init__(self, 0, 0, width, height)

        self.node = node
        self.input_ports: list[IOPort] = []
        self.output_ports: list[IOPort] = []

        self.init_ui()


    def init_ui(self):
        self.bg_default = QColor(STYLE["bg_default"])
        self.bg_selected = QColor(STYLE["bg_selected"])
        self.border_default = QColor(STYLE["border_default"])
        self.border_selected = QColor(STYLE["border_selected"])

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
        top_bar = QWidget()
        top_bar.setStyleSheet("background: transparent;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(0)

        self.help_button = StyledButton("", ["help.png"])
        self.help_button.setFixedSize(15, 15)
        self.help_button.clicked.connect(self.show_help)
        top_bar_layout.addWidget(self.help_button)

        self.name_label = QLabel(self.node.name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 13px;
                border: none;
            }
        """)
        top_bar_layout.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignCenter)
        delete_button = StyledButton("", ["close_small.png"])
        delete_button.setFixedSize(15, 15)
        delete_button.clicked.connect(lambda: self.delete_signal.emit(self))
        top_bar_layout.addWidget(delete_button)

        ########################
        ## Inputs/Outputs:
        ########################
        y = 37
        max_width = self.rect().width()
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


        self.setRect(self.rect().x(), self.rect().y(), max_width + 20, y + 10)

        rect = self.rect()
        name_rect = QGraphicsRectItem(1, 1, rect.width() - 2, 25, self)
        name_rect.setBrush(QBrush(QColor(STYLE["top_bar"])))
        name_rect.setPen(QPen(self.border_default, 0))
        create_proxy(self, top_bar, self.rect().left() + 10, name_rect.rect().top() + 5,
                     self.rect().width() - 20, 15)

        for o in self.output_ports:
            o.setPos(self.rect().width(), o.pos().y())

    def show_help(self):
        dialog = HelpDialog(self.node.name + " Help", self.node.help_text)
        dialog.exec()

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
    delete_connection_sigal = Signal(object)

    def __init__(self, start_port: IOPort):
        QObject.__init__(self)
        QGraphicsPathItem.__init__(self)
        self.start_port: IOPort = start_port
        self.end_port: IOPort | None = None
        self.setPen(QPen(QColor.fromRgb(*start_port.port.data.color), 2))
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
            self.delete_connection_sigal.emit(self)
        else:
            return super().mousePressEvent(event)
