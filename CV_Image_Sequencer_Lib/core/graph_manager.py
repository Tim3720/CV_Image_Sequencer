from typing import Optional
from uuid import uuid4, UUID

from .node_base import Node, ComputationalNode

class GraphManager:

    def __init__(self) -> None:
        self._uuid_to_nodes: dict[UUID, Node] = {}

        # Connection layout: {NodeUUID: [(OutputNodeUUID, OutPutNodeIndex)]}
        self._node_connections: dict[UUID, list[Optional[tuple[UUID, int]]]] = {}

    def get_node(self, node_uuid: UUID) -> Node:
        if not node_uuid in self._uuid_to_nodes:
            raise ValueError(f"Input node not in graph: {node_uuid}")
        return self._uuid_to_nodes[node_uuid]

    def has_connection(self, input_node_uuid: UUID, input_node_idx: int) -> bool:
        if not input_node_uuid in self._uuid_to_nodes:
            raise ValueError(f"Input node not in graph: {input_node_uuid}.")
        if not input_node_uuid in self._node_connections:
            return False
        if input_node_idx < 0 or input_node_idx >= len(self._node_connections[input_node_uuid]):
            raise ValueError(f"Invalid index")
        if self._node_connections[input_node_uuid][input_node_idx] is None:
            return False
        return True

    def get_connection(self, input_node_uuid: UUID, input_node_idx: int) -> tuple[UUID, int]:
        if not input_node_uuid in self._uuid_to_nodes:
            raise ValueError(f"Input node not in graph: {input_node_uuid}.")
        if not input_node_uuid in self._node_connections:
            raise ValueError(f"No connection to the given node.")
        if input_node_idx < 0 or input_node_idx >= len(self._node_connections[input_node_uuid]):
            raise ValueError(f"Invalid index")
        connection = self._node_connections[input_node_uuid][input_node_idx]
        if connection is None:
            raise ValueError(f"No connection to the given node.")
        return connection

    def add_node(self, node: Node) -> UUID:
        uuid = uuid4()
        self._uuid_to_nodes[uuid] = node
        return uuid

    def remove_node(self, node_uuid: UUID):
        ...

    def connect_nodes(self, input_node_uuid: UUID, input_node_idx: int,
                      output_node_uuid: UUID, output_node_idx: int):
        """Connect two nodes. If the nodes are computational nodes, the specific Nodes
        which should be connected are defined by the index. Other nodes should not have
        any sub-nodes and thus the index must be 0."""

        if input_node_uuid == output_node_uuid:
            raise ValueError(f"Can not connect a node to itself.")
        if not input_node_uuid in self._uuid_to_nodes:
            raise ValueError(f"Input node not in graph: {input_node_uuid}")
        if not output_node_uuid in self._uuid_to_nodes:
            raise ValueError(f"Output node not in graph: {input_node_uuid}")
        if output_node_idx < 0 or input_node_idx < 0:
            raise ValueError("Input or output index smaller 0")

        input_node = self._uuid_to_nodes[input_node_uuid]
        if not input_node_uuid in self._node_connections or not self._node_connections[input_node_uuid]:
            if isinstance(input_node, ComputationalNode):
                self._node_connections[input_node_uuid] = [None] * len(input_node.input_nodes)
            else:
                self._node_connections[input_node_uuid] = [None]

        if len(self._node_connections[input_node_uuid]) <= input_node_idx:
            raise ValueError("Input index out of bounds")

        output_node = self._uuid_to_nodes[output_node_uuid]
        if (isinstance(output_node, ComputationalNode) and output_node_idx >= len(output_node.output_nodes)) or output_node_idx > 0:
            raise ValueError("Input index out of bounds")

        # check if connection already exists?

        if isinstance(input_node, ComputationalNode):
            input_node.input_nodes[input_node_idx].connect_node(output_node.output_nodes[output_node_idx])
        else:
            input_node.connect_node(output_node.output_nodes[output_node_idx])

        self._node_connections[input_node_uuid][input_node_idx] = (output_node_uuid, output_node_idx)

    def disconnect_node(self, input_node_uuid: UUID, input_node_idx: int):
        if not input_node_uuid in self._uuid_to_nodes:
            raise ValueError(f"Input node not in graph: {input_node_uuid}.")
        if not input_node_uuid in self._node_connections:
            raise ValueError(f"No connection to the given node.")
        if input_node_idx < 0 or input_node_idx <= len(self._node_connections[input_node_uuid]):
            raise ValueError(f"No connection to the given node.")

        self._node_connections[input_node_uuid][input_node_idx] = None
