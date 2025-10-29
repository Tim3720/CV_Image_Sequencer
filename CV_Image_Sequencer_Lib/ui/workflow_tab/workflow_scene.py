from PySide6.QtCore import QRectF, Slot, Signal
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
)

from ...core.node_base import InPut, OutPut, Node
from ...core.node_manager import NodeManager
from ...utils.source_manager import SourceManager
from .node_vis import Connection, IOPort, NodeVis

class WorkflowScene(QGraphicsScene):

    request_node_menu_signal = Signal(QGraphicsSceneMouseEvent)

    def __init__(self, source_manager: SourceManager, node_manager: NodeManager):
        super().__init__()

        self.temp_connection: Connection | None = None
        self.start_port: IOPort | None = None

        self.margin = 10

        self.source_manager = source_manager
        self.node_manager = node_manager
        # self.node_visulisations: list[NodeVis] = []
        self.connections: list[Connection] = []
        self.nodes_to_connections: dict[Node, list[Connection]] = {}
        self.connections_to_nodes: dict[Connection, tuple[Node, Node]] = {}

    def add_node(self, node_vis: NodeVis, x: float = 0, y: float = 0):
        self.addItem(node_vis)
        node_vis.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        node_vis.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

        c_x = x - node_vis.rect().width() / 2
        c_y = y - node_vis.rect().height() / 2
        node_vis.setPos(c_x, c_y)

        node_vis.node_position_changed_signal.connect(self.update_connections)

        # connect to ports:
        for i in node_vis.input_ports:
            i.port_press_signal.connect(self.port_clicked)
        for o in node_vis.output_ports:
            o.port_press_signal.connect(self.port_clicked)

    def delete_node(self, node_vis: NodeVis):
        if node_vis.node in self.nodes_to_connections:
            # remove connections
            connections = self.nodes_to_connections[node_vis.node].copy()
            for connection in connections:
                self.delete_connection(connection)

            self.nodes_to_connections.pop(node_vis.node)
        self.removeItem(node_vis)
        node_vis.deleteLater()

    @Slot()
    def port_clicked(self):
        port = self.sender()
        if not isinstance(port, IOPort):
            return

        # start new temporary connection
        if self.start_port is None and (
            isinstance(port.port, OutPut) or port.port.connected_output is None
        ):
            self.start_port = port
            self.temp_connection = Connection(self.start_port)
            self.addItem(self.temp_connection)
            return

        # try to finish connection
        if (
            self.temp_connection is not None
            and self.start_port is not None
            and self.start_port.parent_node != port.parent_node
            and type(self.start_port.port.data) == type(port.port.data)
        ):
            success = self.connect_nodes(self.start_port, port, self.temp_connection)
            if success:
                self.temp_connection = None
                self.start_port = None

    def create_connections(self, start: IOPort, stop: IOPort):
        connection = Connection(start)
        self.addItem(connection)

        if not start.parent_node in self.nodes_to_connections:
            self.nodes_to_connections[start.parent_node] = []
        if not stop.parent_node in self.nodes_to_connections:
            self.nodes_to_connections[stop.parent_node] = []

        self.nodes_to_connections[start.parent_node].append(connection)
        self.nodes_to_connections[stop.parent_node].append(connection)
        self.connections_to_nodes[connection] = (start.parent_node, stop.parent_node)

        connection.connect_path(stop)
        self.connections.append(connection)
        connection.delete_connection_sigal.connect(self.delete_connection)

    def connect_nodes(self, start: IOPort, stop: IOPort, connection: Connection | None =
                      None, run_data_update: bool = True) -> bool:
        if (
            isinstance(stop.port, InPut)
            and isinstance(start.port, OutPut)
            and stop.port.connected_output is None
        ):
            self.node_manager.connect_nodes(start.port, stop.port, run_data_update)
        elif (
            isinstance(stop.port, OutPut)
            and isinstance(start.port, InPut)
            and start.port.connected_output is None
        ):
            self.node_manager.connect_nodes(stop.port, start.port, run_data_update)
        else:
            return False

        if connection is None:
            connection = Connection(start)
            self.addItem(connection)

        if not start.parent_node in self.nodes_to_connections:
            self.nodes_to_connections[start.parent_node] = []
        if not stop.parent_node in self.nodes_to_connections:
            self.nodes_to_connections[stop.parent_node] = []

        self.nodes_to_connections[start.parent_node].append(connection)
        self.nodes_to_connections[stop.parent_node].append(connection)
        self.connections_to_nodes[connection] = (start.parent_node, stop.parent_node)

        connection.connect_path(stop)
        self.connections.append(connection)
        connection.delete_connection_sigal.connect(self.delete_connection)

        return True

    @Slot(Connection)
    def delete_connection(self, connection: Connection):
        if not isinstance(connection, Connection) or connection.end_port is None:
            return
        connection.delete_connection_sigal.disconnect(self.delete_connection)
        self.connections.remove(connection)
        if isinstance(connection.start_port.port, InPut):
            self.node_manager.disconnect_input(connection.start_port.port)
        elif isinstance(connection.end_port.port, InPut):
            self.node_manager.disconnect_input(connection.end_port.port)
        else:
            return

        for node in self.connections_to_nodes[connection]:
            self.nodes_to_connections[node].remove(connection)
        self.removeItem(connection)

    def update_connections(self):
        for connection in self.connections:
            connection.update_path()

    def itemMoved(self, item):
        """
        Call this whenever an item moves.
        Expands the sceneRect if item is out of bounds.
        """
        rect = self.sceneRect()
        pos = item.sceneBoundingRect()
        
        left = min(rect.left(), pos.left() - self.margin)
        top = min(rect.top(), pos.top() - self.margin)
        right = max(rect.right(), pos.right() + self.margin)
        bottom = max(rect.bottom(), pos.bottom() + self.margin)
        
        new_rect = QRectF(left, top, right-left, bottom-top)
        if new_rect != rect:
            self.setSceneRect(new_rect)

    def mouseMoveEvent(self, event):
        if self.temp_connection and self.start_port:
            self.temp_connection.update_temp_path(
                self.start_port.scenePos(), event.scenePos()
            )

        super().mouseMoveEvent(event)


    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            items_under_mouse = self.items(event.scenePos())
            if not items_under_mouse or Connection in [type(item) for item in items_under_mouse]: 
                if self.temp_connection is not None: # stop making connection 
                    self.start_port = None
                    self.removeItem(self.temp_connection)
                    self.temp_connection = None
            if not items_under_mouse and self.temp_connection is None: 
                self.request_node_menu_signal.emit(event)
        return super().mousePressEvent(event)

