from typing import Callable, Optional, override
from uuid import uuid4, UUID
from PySide6.QtCore import QObject, Signal, Slot



class Node(QObject):

    data_request_signal = Signal(object) # send sender for safety
    send_data_signal = Signal(object)

    def __init__(self, name: str = "") -> None:
        super().__init__()
        self.input_node: Optional[Node] = None
        self.output_nodes: list[Node] = [self]
        self.name = name

    def disconnect_node(self):
        if self.input_node is None:
            return

        self.data_request_signal.disconnect(self.input_node.request_data)
        self.input_node.send_data_signal.disconnect(self.send_data)

        self.input_node = None

    def connect_node(self, other: "Node"):
        if not self.input_node is None:
            self.disconnect_node()

        self.input_node = other
        self.data_request_signal.connect(self.input_node.request_data)

    @Slot()
    def request_data(self):
        print(f"{self.name} requesting data")
        if self.input_node is None:
            return
        self.input_node.send_data_signal.connect(self.send_data)
        self.data_request_signal.emit(self)

    @Slot()
    def send_data(self, data: object, disconnect: bool = True):
        print(f"{self.name} sending data")
        if self.input_node is None:
            return
        if disconnect:
            self.input_node.send_data_signal.disconnect(self.send_data)
        self.send_data_signal.emit(data)



class ComputationalNode(Node):
    # inputs send data to the computation, which then sends the result to the outputs
    # outputs receive data requestes and distributed them to the inputs
    # store which outputs want to have data and only send the data to these outputs.
    # There are two ways to communicate with this node: 
    #   1. Via its input and output nodes (for sending data through the graph)
    #   2. Directly via its base node itself (for getting data from this node without
    #   sending the data to its outputs)

    def __init__(self, input_nodes: list[Node], output_nodes: list[Node],
                 compute_function: Callable, name: str = "") -> None:
        super().__init__(name)

        self.input_nodes: list[Node] = input_nodes
        self.output_nodes: list[Node] = output_nodes
        self.compute_function: Callable = compute_function

        self.requesting_node_indices: list[int] = []

        self.input_data_buffer: list[Optional[object]] = [None] * len(self.input_nodes)

        for node in self.input_nodes:
            self.connect_node(node)

        for output_node in self.output_nodes:
            output_node.connect_node(self)

    def compute_data(self):
        # check if buffer is filled:
        if None in self.input_data_buffer:
            return
        try:
            print("computing result")
            result = self.compute_function(*self.input_data_buffer)

            self.send_data_signal.emit([result[idx] for idx in
                                        self.requesting_node_indices])
            for i in self.requesting_node_indices:
                self.output_nodes[i].send_data(result[i], False)
            self.input_data_buffer = [None] * len(self.input_nodes)
            self.requesting_node_indices = []
        except Exception as e:
            print(f"Error on running compute_function in ComputeNode {self}: {e}")

    @override
    @Slot(object)
    def request_data(self, sender: Optional[Node] = None):
        print(f"{self.name} requesting data")
        if sender is None:  # request for all outputs
            self.requesting_node_indices = [i for i in range(len(self.output_nodes))]
            # for node in self.output_nodes:
            #     self.send_data_signal.connect(node.send_data)
        else:
            if not isinstance(sender, Node) or not sender in self.output_nodes:
                raise ValueError(f"Invalid sender tried requesting data: {sender}")
            self.requesting_node_indices.append(self.output_nodes.index(sender))
            self.send_data_signal.disconnect(sender.send_data)
        self.data_request_signal.emit(self)

    @override
    @Slot(object)
    def send_data(self, data: object):
        print(f"{self.name} sending data")
        sender = self.sender()
        if not isinstance(sender, Node) or not sender in self.input_nodes:
            raise ValueError(f"Invalid sender tried to add data to the input buffer: {sender}")

        idx = self.input_nodes.index(sender)
        self.input_data_buffer[idx] = data
        self.compute_data()

    @override
    def connect_node(self, other: "Node"):
        self.data_request_signal.connect(other.request_data)
        other.send_data_signal.connect(self.send_data)


class SourceNode(ComputationalNode):
    def __init__(self, input_nodes: list[Node], output_nodes: list[Node], source_function, name: str = "") -> None:
        super().__init__(input_nodes, output_nodes, source_function, name)

        if not self.input_nodes:
            self.data_request_signal.connect(self.send_data)

    @override
    @Slot(object)
    def send_data(self, data: object = None):
        print(f"{self.name} sending data")

        if self.input_nodes:
            sender = self.sender()
            if not isinstance(sender, Node) or not sender in self.input_nodes:
                raise ValueError(f"Invalid sender tried to add data to the input buffer: {sender}")

            idx = self.input_nodes.index(sender)
            self.input_data_buffer[idx] = data
        self.compute_data()


class BlackBoxNode(Node):
    def __init__(self, input_nodes: list[Node], output_nodes: list[Node], name: str = "") -> None:
        super().__init__(name)

        self.input_nodes: list[Node] = input_nodes
        self.output_nodes: list[Node] = output_nodes

        self.requesting_node_idx: Optional[int] = None
        self.input_data_buffer: list[Optional[object]] = [None] * len(self.input_nodes)


class Graph:

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
        if input_node_idx < 0 or input_node_idx <= len(self._node_connections[input_node_uuid]):
            raise ValueError(f"Invalid index")
        if self._node_connections[input_node_uuid][input_node_idx] is None:
            return False
        return True

    def get_connection(self, input_node_uuid: UUID, input_node_idx: int) -> tuple[UUID, int]:
        if not input_node_uuid in self._uuid_to_nodes:
            raise ValueError(f"Input node not in graph: {input_node_uuid}.")
        if not input_node_uuid in self._node_connections:
            raise ValueError(f"No connection to the given node.")
        if input_node_idx < 0 or input_node_idx <= len(self._node_connections[input_node_uuid]):
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

        #     input_node.output_nodes[0].connect_node(output_node)
        self._node_connections[input_node_uuid][input_node_idx] = (output_node_uuid, output_node_idx)

    def disconnect_node(self, input_node_uuid: UUID, input_node_idx: int):
        if not input_node_uuid in self._uuid_to_nodes:
            raise ValueError(f"Input node not in graph: {input_node_uuid}.")
        if not input_node_uuid in self._node_connections:
            raise ValueError(f"No connection to the given node.")
        if input_node_idx < 0 or input_node_idx <= len(self._node_connections[input_node_uuid]):
            raise ValueError(f"No connection to the given node.")

        self._node_connections[input_node_uuid][input_node_idx] = None


if __name__ == "__main__":
    def source_func():
        return [1]

    def source_func2():
        return [2]

    def comp1(arg):
        return [arg + 1]

    def comp2(arg):
        return [arg - 1]

    def comp3(arg1, arg2):
        return [arg1 + arg2, arg1 - arg2]

    # a = SourceNode(source_func, "a")
    # b = SourceNode(source_func2, "b")
    a_node = Node("a_node")
    b_node = Node("b_node")
    a = SourceNode([], [a_node], source_func, "a")
    b = SourceNode([], [b_node], source_func2, "b")

    c0 = Node("c0")
    c1 = Node("c1")
    c2 = Node("c2")
    c3 = Node("c3")
    C = ComputationalNode([c0, c1], [c2, c3], comp3, "C")

    graph = Graph()

    a_id = graph.add_node(a)
    b_id = graph.add_node(b)
    C_id = graph.add_node(C)
    print(a_id)
    print(b_id)
    print(C_id)

    graph.connect_nodes(C_id, 0, a_id, 0)
    graph.connect_nodes(C_id, 1, b_id, 0)

    # c2.request_data()
    # c2.send_data_signal.connect(lambda x: print(x))
    # c3.send_data_signal.connect(lambda x: print(x))
    # C.request_data()
    # C.request_data()

    a.send_data_signal.connect(lambda x: print(x))
    a.request_data()
    a.request_data()

