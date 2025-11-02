from typing import Optional, Tuple
from uuid import UUID
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout
)




from ...core.nodes import ABSDiffNode, GrayScaleNode, ImageSourceNode, MinNode, SourceNode, ThresholdNode
from ...core.graph_manager import GraphManager
from ...core.node_base import Node, ComputationalNode
from ...utils.type_base import IOType
from ...utils.source_manager import SourceManager
from .node_vis import NodeVis

class WorkflowManager(QWidget):

    node_added_signal = Signal(object) # tuple(UUID, x, y)
    node_deleted_signal = Signal(UUID) 

    connection_added_signal = Signal(object) # tuple(UUID, idx)
    connection_deleted_signal = Signal(object) # tuple(UUID, idx)

    node_double_clicked_signal = Signal(int) # n_outputs
    data_signal = Signal(object)    # list[IOType]

    def __init__(self, source_manager: SourceManager):
        super().__init__()
        
        self.source_manager = source_manager
        self.graph_manager = GraphManager()

        self.node_visulisations: dict[UUID, NodeVis] = {}

        # self.selected_node: UUID | None = None
        self.selected_node: Optional[Node] = None 

    def test(self):
        # Example:
        source_node1 = ImageSourceNode(lambda: self.source_manager.get_next_n_frames(1, 0))
        s1 = self.add_node(source_node1, 200, 200)
        source_node2 = ImageSourceNode(lambda: self.source_manager.get_next_n_frames(1, 1))
        s2 = self.add_node(source_node2, 200, 300)

        gray_node1 = GrayScaleNode()
        g1 = self.add_node(gray_node1, 400, 200)

        gray_node2 = GrayScaleNode()
        g2 = self.add_node(gray_node2, 400, 300)
        
        # node = ABSDiffNode()
        # m = self.add_node(node, 800, 250)

        node = ThresholdNode()
        m = self.add_node(node, 600, 250)

        self.connect_nodes(g1, 0, s1, 0)
        self.connect_nodes(g2, 0, s2, 0)
        # self.connect_nodes(m, 1, g2, 0)

        self.connect_nodes(m, 0, g1, 0)


    def add_node(self, node: ComputationalNode, x=0, y=0):
        node_uuid = self.graph_manager.add_node(node)
        node_vis = NodeVis(node, node_uuid)
        node_vis.double_clicked_signal.connect(self.on_node_double_click)
        self.node_visulisations[node_uuid] = node_vis
        self.node_added_signal.emit((node_uuid, x, y))
        return node_uuid

    @Slot(UUID)
    def on_node_double_click(self, node_uuid: UUID):
        if not self.selected_node is None:
            self.selected_node.send_data_signal.disconnect(self.show_data)

        self.selected_node = self.graph_manager.get_node(node_uuid)
        self.selected_node.send_data_signal.connect(self.show_data)
        self.selected_node.request_data()
        # self.node_double_clicked_signal.emit(node.n_outputs)
        # node.request_data()
        # for o in node.output_ports:
        #     o.data_signal.connect(self.show_data)

    @Slot(IOType)
    def show_data(self, data_package: tuple[list[IOType], Node]):
        data, sender = data_package
        self.data_signal.emit((data, None))

    def connect_nodes(self, input_node_uuid: UUID, input_port_idx: int, output_node_uuid:
                      UUID, output_port_idx: int):
        self.graph_manager.connect_nodes(input_node_uuid, input_port_idx, output_node_uuid, output_port_idx)
        self.connection_added_signal.emit((input_node_uuid, input_port_idx))
