from typing import Callable, Optional, override
from PySide6.QtCore import QObject, Slot, Signal

from CV_Image_Sequencer_Lib.utils.type_base import IOType


class Node(QObject):

    data_request_signal = Signal(object) # send sender for safety
    send_data_signal = Signal(object)   # (list[IOType], sender)

    def __init__(self, data_type: Optional[type[IOType]], name: str = "") -> None:
        super().__init__()
        self.input_node: Optional[Node] = None
        self.data_type = data_type
        self.output_nodes = [self]
        self.name = name

    def disconnect_node(self):
        if self.input_node is None:
            return

        self.data_request_signal.disconnect(self.input_node.request_data)
        # self.input_node.send_data_signal.disconnect(self.send_data)
        self.input_node = None

    def connect_node(self, other: "Node"):
        if not other.data_type is None and not self.data_type is None and other.data_type != self.data_type:
            raise ValueError("Can not connect nodes with different datatypes")
        if not self.input_node is None:
            self.disconnect_node()

        self.input_node = other
        self.data_request_signal.connect(self.input_node.request_data)

    @Slot()
    def request_data(self):
        if self.input_node is None:
            self.data_request_signal.emit(self)
        else:
            self.input_node.send_data_signal.connect(self.send_data)
            self.data_request_signal.emit(self)

    @Slot(object)
    def send_data(self, data: tuple[IOType, "Node"], disconnect: bool = True):
        value, sender = data
        if not self.data_type is None and not isinstance(value, self.data_type):
            raise ValueError(f"""Invalid type passed to send_data: Expected
            {self.data_type}, got {type(data)}""")
        # if self.input_node is None:
        #     return
        if disconnect and not self.input_node is None:
            self.input_node.send_data_signal.disconnect(self.send_data)
        self.send_data_signal.emit((value, self))

class DataNode(Node):
    def __init__(self, data_type: type[IOType], name: str = "") -> None:
        super().__init__(data_type, name)
        self.data_type: type[IOType] = data_type

class ComputationalNode(Node):

    get_data_signal = Signal(list[IOType])

    def __init__(self, input_nodes: list[DataNode], output_nodes: list[DataNode],
                 compute_function: Callable, name: str = "") -> None:
        super().__init__(None, name)

        # check if each source node given as input only has one output and one input
        for node in input_nodes:
            if isinstance(node, SourceNode):
                if len(node.input_nodes) > 1 or len(node.output_nodes) > 1:
                    raise ValueError("""SourceNodes used as inputs for ComputationalNodes
                    are only allowed to have one input and one output.""")

        self.input_nodes: list[DataNode] = input_nodes
        self.output_nodes: list[DataNode] = output_nodes
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
            result = self.compute_function(*self.input_data_buffer)
            self.send_data_signal.emit(([result[idx] for idx in self.requesting_node_indices], self))
            for i in self.requesting_node_indices:
                self.output_nodes[i].send_data((result[i], self), False)
            self.input_data_buffer = [None] * len(self.input_nodes)
            self.requesting_node_indices = []
        except Exception as e:
            print(f"Error on running compute_function in ComputeNode {self}: {e}")


    @override
    @Slot(object)
    def request_data(self, sender: Optional[DataNode] = None):
        if sender is None:  # request for all outputs
            self.requesting_node_indices = [i for i in range(len(self.output_nodes))]
        else:
            if not isinstance(sender, DataNode) or not sender in self.output_nodes:
                raise ValueError(f"Invalid sender tried requesting data: {sender}")
            self.requesting_node_indices.append(self.output_nodes.index(sender))
            self.send_data_signal.disconnect(sender.send_data)  # disconnect node to later
                                                                # call send_data of this node manually
        self.data_request_signal.emit(self)

    @override
    @Slot(object)
    def send_data(self, data: tuple[IOType, Node]):
        value, sender = data
        if not isinstance(sender, DataNode) or not sender in self.input_nodes:
            raise ValueError(f"Invalid sender tried to add data to the input buffer: {sender}")

        idx = self.input_nodes.index(sender)
        input_node = self.input_nodes[idx]
        if isinstance(input_node, SourceNode):
            input_node = input_node.output_nodes[0]
        if not isinstance(value, input_node.data_type):
            raise ValueError(f"""Invalid type passed to send_data: Expected
            {self.data_type}, got {type(data)}""")
        self.input_data_buffer[idx] = value
        self.compute_data()

    @override
    def connect_node(self, other: Node):
        self.data_request_signal.connect(other.request_data)
        other.send_data_signal.connect(self.send_data)


class SourceNode(ComputationalNode):
    def __init__(self, input_nodes: list[DataNode], output_nodes: list[DataNode], source_function, name: str = "") -> None:
        super().__init__(input_nodes, output_nodes, source_function, name)

        if not self.input_nodes:
            self.data_request_signal.connect(lambda: self.send_data(None))

    @override
    @Slot(object)
    def send_data(self, data: Optional[tuple[IOType, Node]] = None):
        if data is None:
            value = None
            sender = None
        else:
            value, sender = data
        if self.input_nodes:
            if sender is None:
                print("Sender is none")
                if len(self.output_nodes) > 1:
                    raise ValueError("Could not determine sender.")
                idx = 0
            else:
                if not isinstance(sender, DataNode) or not sender in self.input_nodes:
                    raise ValueError(f"Invalid sender tried to add data to the input buffer: {sender}")
                idx = self.input_nodes.index(sender)

            input_node = self.input_nodes[idx]
            # if isinstance(input_node, SourceNode):
            #     input_node = input_node.output_nodes[0]

            if not isinstance(value, input_node.data_type):
                raise ValueError(f"""Invalid type passed to send_data: Expected
                {self.data_type}, got {type(data)}""")
            self.input_data_buffer[idx] = value
        self.compute_data()

    # def compute_data(self):
    #     # check if buffer is filled:
    #     if None in self.input_data_buffer:
    #         return
    #     try:
    #         result = self.compute_function(*self.input_data_buffer)
    #         for i in self.requesting_node_indices:
    #             self.output_nodes[i].send_data(result[i])
    #
    #         self.input_data_buffer = [None] * len(self.input_nodes)
    #         self.requesting_node_indices = []
    #     except Exception as e:
    #         print(f"Error on running compute_function in ComputeNode {self}: {e}")


class BlackBoxNode(Node):
    def __init__(self, input_nodes: list[Node], output_nodes: list[Node], name: str = "") -> None:
        super().__init__(None, name)

        self.input_nodes: list[Node] = input_nodes
        self.output_nodes: list[Node] = output_nodes

