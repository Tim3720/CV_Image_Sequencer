from uuid import UUID
from PySide6.QtCore import QRectF, Slot, Signal
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
)

from ...core.node_base import Node
from .workflow_manager import WorkflowManager
from .node_vis import IOPort
from .connection_vis import Connection

class WorkflowScene(QGraphicsScene):

    request_node_menu_signal = Signal(QGraphicsSceneMouseEvent)

    def __init__(self, workflow_manager: WorkflowManager):
        super().__init__()

        self.workflow_manager = workflow_manager

        self.temp_connection: Connection | None = None
        self.start_port: IOPort | None = None


        self.margin = 10

        self.connections: list[Connection] = []

        self.workflow_manager.node_added_signal.connect(self.add_node)
        self.workflow_manager.connection_added_signal.connect(self.connect_nodes)


    @Slot(object)
    def add_node(self, node_info: tuple[UUID, float, float]):
        node_uuid, x, y = node_info
        node_vis = self.workflow_manager.node_visulisations[node_uuid]
        self.addItem(node_vis)
        node_vis.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        node_vis.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

        c_x = x - node_vis.rect().width() / 2
        c_y = y - node_vis.rect().height() / 2
        node_vis.setPos(c_x, c_y)

        node_vis.node_position_changed_signal.connect(self.update_connections)

        # connect port signals:
        for i in node_vis.input_nodes:
            i.port_press_signal.connect(self.on_port_clicked)
        for o in node_vis.output_nodes:
            o.port_press_signal.connect(self.on_port_clicked)

    @Slot(object)
    def connect_nodes(self, connection_info: tuple[UUID, int]):
        input_node_uuid, input_port_idx = connection_info
        output_node_uuid, output_port_idx = self.workflow_manager.graph_manager.get_connection(input_node_uuid, input_port_idx)
        input_port = self.workflow_manager.node_visulisations[input_node_uuid].input_nodes[input_port_idx]
        output_port = self.workflow_manager.node_visulisations[output_node_uuid].output_nodes[output_port_idx]

        if not self.temp_connection is None:
            connection = self.temp_connection
            if self.temp_connection.start_port.is_input:
                self.temp_connection.connect_path(output_port)
            else:
                self.temp_connection.connect_path(input_port)
        else:
            connection = Connection(input_port)
            self.addItem(connection)
            connection.connect_path(output_port)
        self.connections.append(connection)
        connection.delete_connection_sigal.connect(self.delete_connection)

    
    @Slot(Connection)
    def delete_connection(self, connection: Connection):
        print("delete connection")
        if not isinstance(connection, Connection) or connection.end_port is None:
            return
        connection.delete_connection_sigal.disconnect(self.delete_connection)
        self.connections.remove(connection)
        if connection.start_port.is_input:
            uuid = connection.start_port.parent_node_uuid
            idx = connection.start_port.index
        else:
            uuid = connection.end_port.parent_node_uuid
            idx = connection.end_port.index
        
        self.workflow_manager.graph_manager.disconnect_node(uuid, idx)
        self.removeItem(connection)
        
    def update_connections(self):
        for connection in self.connections:
            connection.update_path()

    @Slot(object)
    def on_port_clicked(self, node_data: tuple[UUID, int, bool]):
        sender = self.sender()
        if not isinstance(sender, IOPort):
            raise ValueError("Invalid object called on_port_clicked method.")

        uuid, idx, is_input = node_data
        if is_input and self.workflow_manager.graph_manager.has_connection(uuid, idx):
            raise ValueError("Clicked node is an input and already has a connection")

        if self.temp_connection is None or self.start_port is None:
            self.start_port = sender
            self.temp_connection = Connection(self.start_port)
            self.addItem(self.temp_connection)
        else:
            if is_input == self.start_port.is_input:
                return
            if is_input and self.start_port:
                input_node_uuid = uuid
                input_node_idx = idx
                output_node_uuid = self.start_port.parent_node_uuid
                output_node_idx = self.start_port.index
            else:
                input_node_uuid = self.start_port.parent_node_uuid
                input_node_idx = self.start_port.index
                output_node_uuid = uuid
                output_node_idx = idx
            if (self.workflow_manager.graph_manager.connection_possible(input_node_uuid,
                                                                        input_node_idx,
                                                                        output_node_uuid,
                                                                        output_node_idx)):
                # self.temp_connection.connect_path(sender)
                # self.connections.append(self.temp_connection)
                self.workflow_manager.connect_nodes(input_node_uuid, input_node_idx,
                                                    output_node_uuid, output_node_idx)
                # self.removeItem(self.temp_connection)
                self.temp_connection = None
                self.start_port = None

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
