from collections import defaultdict
from typing import Any
from PySide6.QtCore import QObject, Signal
from uuid import UUID

from .nodes import Node, InputSocket, OutputSocket


class Graph(QObject):
    """Manages nodes and connections."""

    node_added = Signal(UUID)
    connection_added = Signal(object) # tuple[UUID, UUID, UUID, UUID]

    def __init__(self):
        super().__init__()
        self.nodes: dict[UUID, Node] = {}

        # {(input_node_uuid, input_socket_uuid): [(output_node_uuid, output_socket_uuid)]}
        self.connections: dict[tuple[UUID, UUID], list[tuple[UUID, UUID]]] = defaultdict(list[tuple[UUID, UUID]])

    def add_node(self, node: Node):
        self.nodes[node.uuid] = node
        self.node_added.emit(node.uuid)

    def connect_sockets(self, out_socket: OutputSocket, in_socket: InputSocket):
        in_socket.connect_output(out_socket)
        self.connections[(in_socket.node.uuid, in_socket.uuid)].append((out_socket.node.uuid, out_socket.uuid))
        self.connection_added.emit((in_socket.node.uuid, in_socket.uuid, out_socket.node.uuid, out_socket.uuid))

    def connect_sockets_by_idx(self, node_out: Node, idx_out: int, node_in: Node, idx_in: int):
        try:
            out_socket = node_out.outputs[node_out.output_uuids[idx_out]]
            in_socket = node_in.inputs[node_in.input_uuids[idx_in]]
            self.connect_sockets(out_socket, in_socket)
            self.connections[(in_socket.node.uuid, in_socket.uuid)].append((out_socket.node.uuid, out_socket.uuid))
            self.connection_added.emit((in_socket.node.uuid, in_socket.uuid, out_socket.node.uuid, out_socket.uuid))
        except KeyError or IndexError:
            ...

    def evaluate(self, node: Node, output_uuid: UUID) -> Any:
        return node.outputs[output_uuid].get_value()
