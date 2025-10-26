from PySide6.QtCore import QObject, Signal

from ..utils.source_manager import SourceManager

from ..core.node_base import InPut, Node, OutPut
from ..core.nodes import GrayScaleSourceNode, SourceNode


class NodeManager(QObject):
    """
    The NodeManager keeps track of all existing nodes and handles deleting and creating
    new nodes as well as making new connections and removing connections.
    """

    def __init__(self, source_manager: SourceManager) -> None:
        super().__init__()

        self.source_manager = source_manager
        self.nodes: list[Node] = []
        self.output_connections: dict[OutPut, list[InPut]] = {}

    def add_node(self, node_type: type, **kwargs) -> Node:
        id = kwargs["id"] if "id" in kwargs else ""
        if node_type == SourceNode or node_type == GrayScaleSourceNode:
            n_frames = kwargs["n_frames"] if "n_frames" in kwargs else 3
            node = node_type(self.source_manager, n_frames, id=id)
        else:
            node = node_type(id=id)
        self.nodes.append(node)
        return node

    def delete_node(self, node: Node):
        # check if node is in node_list:
        if not node in self.nodes:
            return

        for i in node.inputs:
            self.disconnect_input(i)

        for o in node.outputs:
            if not o in self.output_connections:
                continue
            for i in self.output_connections[o]:
                self.disconnect_input(i)
            self.output_connections.pop(o)

        self.nodes.remove(node)

    def connect_nodes(self, o: OutPut, i: InPut, run_data_update: bool = True):
        i.connect_output(o)
        if o in self.output_connections:
            self.output_connections[o].append(i)
        else:
            self.output_connections[o] = [i]

        if run_data_update:
            i.data_update(recompute_data=True)

    def disconnect_input(self, i: InPut):
        o = i.connected_output
        if o is None:
            return

        i.disconnect_output()
        if o in self.output_connections:
            self.output_connections[o].remove(i)


