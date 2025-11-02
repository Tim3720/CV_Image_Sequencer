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
        self.nodes_to_connections: dict[Node, list[Connection]] = {}
        self.connections_to_nodes: dict[Connection, tuple[Node, Node]] = {}

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
        for i in node_vis.input_ports:
            i.port_press_signal.connect(self.on_port_clicked)
        for o in node_vis.output_ports:
            o.port_press_signal.connect(self.on_port_clicked)

    @Slot(object)
    def connect_nodes(self, connection_info: tuple[UUID, int]):
        input_node_uuid, input_port_idx = connection_info
        print(input_port_idx)
        output_node_uuid, output_port_idx = self.workflow_manager.graph_manager.get_connection(input_node_uuid, input_port_idx)
        input_port = self.workflow_manager.node_visulisations[input_node_uuid].input_ports[input_port_idx]
        output_port = self.workflow_manager.node_visulisations[output_node_uuid].output_ports[output_port_idx]

        connection = Connection(input_port)
        self.addItem(connection)
        connection.connect_path(output_port)
        self.connections.append(connection)
        
    def update_connections(self):
        for connection in self.connections:
            connection.update_path()

    @Slot(object)
    def on_port_clicked(self, port_data: tuple[UUID, int]):
        print(port_data)
