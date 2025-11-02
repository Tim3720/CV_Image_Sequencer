from uuid import UUID
from PySide6.QtWidgets import (QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem,
                               QGraphicsRectItem, QGraphicsTextItem, QLabel, QHBoxLayout, QWidget, QGraphicsProxyWidget)
from PySide6.QtGui import QPainterPathStroker, QPen, QBrush, QColor, QPainterPath
from PySide6.QtCore import QObject, QPointF, Qt, Signal

from ...assets.styles.style import STYLE
from ...ui.styled_widgets import StyledButton
from .help_dialog import HelpDialog

from .type_vis import (BoolVis, EnumVisInput, EnumVisOutput, ScalarVisInput, ScalarVisOutput)
from ...core.node_base import Node, DataNode, ComputationalNode, SourceNode
from ...utils.types import Bool, DictType, Scalar


def create_proxy(parent: QGraphicsItem, widget: QWidget, x: float, y: float, w: float, h: float):
    proxy = QGraphicsProxyWidget(parent)
    proxy.setWidget(widget)
    proxy.setGeometry(x, y, w, h)
    return proxy

def create_proxy_no_position(parent: QGraphicsItem, widget: QWidget):
    proxy = QGraphicsProxyWidget(parent)
    proxy.setWidget(widget)
    return proxy



class IOPort(QObject, QGraphicsEllipseItem):

    port_press_signal = Signal(object) # tuple(parent_uuid, port_idx, is_input)
    data_changed_signal = Signal()

    def __init__(self, node: DataNode, is_input: bool, x, y, parent: "NodeVis",
                 parent_node_uuid: UUID, index: int) -> None:
        QObject.__init__(self)
        radius = 10
        QGraphicsEllipseItem.__init__(self, -radius/2, -radius/2, radius, radius, parent)

        self.parent_node_vis = parent
        self.node = node
        self.is_input = is_input
        self.parent_node_uuid = parent_node_uuid
        self.index = index
        self.pos_x = x
        self.pos_y = y

        if isinstance(self.node, SourceNode):
            self.data_type = self.node.output_nodes[0].data_type
        else:
            self.data_type = self.node.data_type
        
        self.color = QColor.fromRgb(*self.data_type.color)
        self.init_ui()

    def init_ui(self):
        self.data_widget = None
        if issubclass(self.data_type, DictType): # enum like
            if self.is_input:
                self.data_widget = EnumVisInput(self.node)
                self.data_widget.data_changed_signal.connect(self.data_changed_signal.emit)
            else:
                self.data_widget = EnumVisOutput(self.node)
            proxy = create_proxy_no_position(self, self.data_widget)

        elif issubclass(self.data_type, Scalar):
            if self.is_input:
                self.data_widget = ScalarVisInput(self.node)
            else:
                self.data_widget = ScalarVisOutput(self.node)
            proxy = create_proxy_no_position(self, self.data_widget)

        elif self.node.data_type == Bool:
            self.data_widget = BoolVis(self.node)
            proxy = create_proxy_no_position(self, self.data_widget)

        else:
            proxy = QGraphicsTextItem(self.node.name)
            proxy.setDefaultTextColor(QColor(STYLE["textcolor"]))
            proxy.setParentItem(self)

        if self.is_input:
            proxy.setPos(self.rect().x() + self.rect().width() + 5,
                         self.rect().y() + (self.rect().height() - proxy.boundingRect().height()) / 2)
        else:
            proxy.setPos(self.rect().x() - proxy.boundingRect().width() - 5 ,
                         self.rect().y() + (self.rect().height() - proxy.boundingRect().height()) / 2)

        self.setBrush(QBrush(self.color))
        self.setPen(QPen(QColor("#222222"), 1))
        self.setZValue(2)
        self.setPos(self.pos_x, self.pos_y)

        self.width = proxy.boundingRect().width()


    def mousePressEvent(self, event) -> None:
        self.port_press_signal.emit((self.parent_node_vis.node_uuid, self.index,
                                     self.is_input))
        return super().mousePressEvent(event)


class NodeVis(QObject, QGraphicsRectItem):

    node_position_changed_signal = Signal()
    double_clicked_signal = Signal(UUID)
    delete_signal = Signal(object)
    data_changed_signal = Signal()

    def __init__(self, node: ComputationalNode, node_uuid: UUID, width=120, height=60):
        QObject.__init__(self)
        QGraphicsRectItem.__init__(self, 0, 0, width, height)

        self.node: ComputationalNode = node
        self.node_uuid = node_uuid
        self.input_nodes: list[IOPort] = []
        self.output_nodes: list[IOPort] = []

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
        top_bar.setStyleSheet("background: transparent; border: none;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(8)

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
        proxy = create_proxy(self, top_bar, self.rect().left() + 10, self.rect().top() + 5, self.rect().width() - 20, 15)

        ########################
        ## Inputs/Outputs:
        ########################
        y = 37
        max_width = proxy.rect().width()
        for idx, node in enumerate(self.node.output_nodes):
            output_port = IOPort(node, False, self.rect().width(), y, self, self.node_uuid, idx)

            self.output_nodes.append(output_port)
            y += output_port.rect().height() + 12
            if output_port.width > max_width:
                max_width = output_port.width

        for idx, node in enumerate(self.node.input_nodes):
            input_port = IOPort(node, True, 0, y, self, self.node_uuid, idx)
            input_port.data_changed_signal.connect(self.data_changed_signal.emit)
            self.input_nodes.append(input_port)
            y += input_port.rect().height() + 12
            if input_port.width > max_width:
                max_width = input_port.width


        self.setRect(self.rect().x(), self.rect().y(), max_width + 20, y + 10)

        proxy.resize(max_width, proxy.rect().height())

        name_rect = QGraphicsRectItem(1, 1, self.rect().width() - 2, 25, self)
        name_rect.setZValue(-1)
        name_rect.setBrush(QBrush(QColor(STYLE["top_bar"])))
        name_rect.setPen(QPen(self.border_default, 0))

        for node in self.output_nodes:
            node.setPos(self.rect().width(), node.pos().y())

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
        self.double_clicked_signal.emit(self.node_uuid)
        return super().mouseDoubleClickEvent(event)

    def lock_movement(self):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

    def unlock_movement(self):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        # Notify scene to grow if necessary
        if self.scene() and hasattr(self.scene(), "itemMoved"):
            getattr(self.scene(), "itemMoved")(self)



