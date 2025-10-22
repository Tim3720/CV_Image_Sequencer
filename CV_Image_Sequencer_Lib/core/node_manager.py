from PySide6.QtCore import QObject

from ..core.node import InPut, Node, OutPut


class NodeManager(QObject):
    """
    The NodeManager keeps track of all existing nodes and handles deleting and creating
    new nodes as well as making new connections and removing connections.
    """

    def __init__(self) -> None:
        super().__init__()

        self.nodes: list[Node] = []
        self.output_connections: dict[OutPut, list[InPut]] = {}

    def add_node(self, node: Node):
        self.nodes.append(node)

    def delete_node(self, node: Node):
        # check if node is in node_list:
        if not node in self.nodes:
            return

        for i in node.inputs:
            self.disconnect_input(i)

        to_remove = []
        for o in self.output_connections:
            inputs = self.output_connections[o].copy()
            for i in inputs:
                self.disconnect_input(i)
            if not self.output_connections[o]:
                to_remove.append(o)
        for o in to_remove:
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


