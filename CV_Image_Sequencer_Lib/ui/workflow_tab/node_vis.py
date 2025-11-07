from typing import Any
from uuid import UUID
from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import (QWidget, QGraphicsRectItem, QHBoxLayout, QLabel,
                               QGraphicsItem, QGraphicsProxyWidget)
from PySide6.QtGui import QColor, QBrush, QPen

from .socket_vis import SocketVis
from ..styled_widgets import StyledButton, StyledLabel
from ...assets.styles.style import STYLE
from ...core.nodes import Node
from .help_dialog import HelpDialog

def create_proxy(parent: QGraphicsItem, widget: QWidget, x: float, y: float, w: float, h: float):
    proxy = QGraphicsProxyWidget(parent)
    proxy.setWidget(widget)
    proxy.setGeometry(x, y, w, h)
    return proxy

def create_proxy_no_position(parent: QGraphicsItem, widget: QWidget):
    proxy = QGraphicsProxyWidget(parent)
    proxy.setWidget(widget)
    return proxy


class NodeVis(QObject, QGraphicsRectItem):

    delete = Signal()
    double_clicked = Signal()
    node_vis_position_changed = Signal()

    def __init__(self, node: Node, width=120, height=60):
        QObject.__init__(self)
        QGraphicsRectItem.__init__(self, 0, 0, width, height)

        self.node: Node = node
        self.input_sockets: list[SocketVis] = []
        self.output_sockets: list[SocketVis] = []

        self.init_ui()

        self.node.new_inputs.connect(self.update_inputs)


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
        delete_button.clicked.connect(self.delete)

        top_bar_layout.addWidget(delete_button)
        proxy = create_proxy(self, top_bar, self.rect().left() + 10, self.rect().top() + 5, self.rect().width() - 20, 15)
        # top_bar.setStyleSheet("border: 1px solid red;")

        ########################
        ## Inputs/Outputs:
        ########################
        y = 47
        max_width = proxy.rect().width()
        for idx in range(len(self.node.result_template)):
            vis = SocketVis(self.node, idx, False, self)
            self.output_sockets.append(vis)

            if vis.rect().width() > max_width:
                max_width = vis.rect().width()

        for idx in range(len(self.node.parameter_template)):
            vis = SocketVis(self.node, idx, True, self)
            self.input_sockets.append(vis)

            if vis.rect().width() > max_width:
                max_width = vis.rect().width()

        max_width += 20
        for socket_vis in self.output_sockets:
            socket_vis.setPos(max_width, y)
            y += socket_vis.rect().height() + 22
        for socket_vis in self.input_sockets:
            socket_vis.setPos(0, y)
            y += socket_vis.rect().height() + 22
        self.setRect(self.rect().x(), self.rect().y(), max_width, y + 10)


        proxy.resize(max_width - 20, proxy.rect().height())

        name_rect = QGraphicsRectItem(1, 1, self.rect().width() - 2, 25, self)
        name_rect.setZValue(-1)
        name_rect.setBrush(QBrush(QColor(STYLE["top_bar"])))
        name_rect.setPen(QPen(self.border_default, 0))


        visibility_icon = StyledLabel("visibility.png", True)
        visibility_icon.setFixedSize(20, 20)
        self.inspect_proxy = create_proxy_no_position(self, visibility_icon)
        self.inspect_proxy.setPos(self.rect().width() - 22, self.rect().height() - 22)
        self.inspect_proxy.setVisible(False)

    @Slot(list)
    def update_inputs(self, data: list):
        for idx, socket_vis in enumerate(self.input_sockets):
            socket_vis.type_vis.new_input_data(data[idx])

    def set_inspect_icon(self, on: bool):
        self.inspect_proxy.setVisible(on)

    def show_help(self):
        dialog = HelpDialog(self.node.name + " Help", self.node.help_text)
        dialog.exec()

    def mouseDoubleClickEvent(self, event) -> None:
        self.double_clicked.emit()
        return super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
            self.node_vis_position_changed.emit()
        return super().itemChange(change, value)

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

