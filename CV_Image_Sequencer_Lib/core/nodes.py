from typing import IO, Any, Optional
from PySide6.QtCore import QObject, Signal, Slot
from .types import IOType


class Node(QObject):

    new_params = Signal()
    new_results = Signal()
    new_inputs = Signal(object)

    def __init__(self, graph: "Graph", parameter_template: list[tuple[str, type[IOType]]], result_template:
                 list[tuple[str, type[IOType]]]):
        super().__init__()

        self.graph = graph
        self.name: str = ""
        self.help_text: str = ""

        self.parameter_template: list[tuple[str, type[IOType]]] = parameter_template
        self.result_template: list[tuple[str, type[IOType]]] = result_template
        self.results = [None for _ in self.result_template]
        self.external_inputs: list[Optional[IOType]] = [None for _ in self.parameter_template]
        self.default_values: list[Optional[IOType]] = [None for _ in self.parameter_template]
        self.min_values: list[Optional[IOType]] = [None for _ in self.parameter_template]
        self.max_values: list[Optional[IOType]] = [None for _ in self.parameter_template]


    def compute_function(self, inputs: list[Any]) -> list[Any]:
        return self.results

    @Slot()
    def on_new_data(self):
        self.results = [None for _ in self.result_template]
        self.new_params.emit()

    def get_result(self, idx: int):
        for elem in self.results:
            if elem is None:
                self.compute()
                break
        return self.results[idx]

    def get_results(self):
        for elem in self.results:
            if elem is None:
                self.compute()
                break
        return self.results

    def compute(self):
        # get inputs:
        inputs = self.graph.get_params(self)
        for i in range(len(inputs)):
            if inputs[i] is None:
                inputs[i] = self.external_inputs[i]
            if inputs[i] is None:
                inputs[i] = self.default_values[i]

        self.new_inputs.emit(inputs)
        self.results = self.compute_function(inputs)
        # self.new_params.emit()
        self.new_results.emit()

class Graph(QObject):

    def __init__(self):
        super().__init__()

        self.nodes: list[Node] = []
        self.connections: dict[Node, list[Optional[tuple[Node, int]]]] = {} # Node: [(Node, idx), (Node, idx), ...]

    def add_node(self, node: Node):
        self.nodes.append(node)
        self.connections[node] = [None for _ in node.parameter_template]

    def remove_node(self, node: Node):
        self.nodes.remove(node)
        self.connections.pop(node)

    def connect_nodes(self, param_node: Node, param_idx: int, result_node: Node, result_idx: int):
        if not param_node in self.nodes or not result_node in self.nodes:
            raise ValueError("At least one of the provided nodes is unknown to the graph")
        # TODO: check for types etc.
        self.connections[param_node][param_idx] = (result_node, result_idx)
        result_node.new_params.connect(param_node.on_new_data)
        result_node.compute()
        result_node.new_params.emit()

    def disconnect_nodes(self, param_node: Node, param_idx: int):
        if not param_node in self.connections:
            return
        connected = self.connections[param_node][param_idx] 
        if not connected is None:
            connected[0].new_params.disconnect(param_node.on_new_data)
            self.connections[param_node][param_idx] = None
            param_node.compute()
            param_node.new_params.emit()

    def get_params(self, node: Node) -> list[Optional[IOType]]:
        inputs: list[Optional[IOType]] = []
        if node in self.connections:
            for connection in self.connections[node]:
                if connection is None:
                    inputs.append(None)
                else:
                    connected_node, connected_idx = connection
                    inputs.append(connected_node.get_result(connected_idx))
        else:
            for _ in node.parameter_template:
                inputs.append(None)
        return inputs

