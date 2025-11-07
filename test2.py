from typing import Any, Optional
from PySide6.QtCore import QObject, Signal, Slot
from typing import Any, override
import random
import numpy as np
import cv2 as cv
import os

from CV_Image_Sequencer_Lib.core.types import IOType, GrayScaleImage, Int



class Node(QObject):

    new_params = Signal()
    new_results = Signal()

    def __init__(self, graph: "Graph", parameter_template: dict[str, type[IOType]], result_template:
                 dict[str, type[IOType]]):
        super().__init__()

        self.graph = graph
        self.name: str = ""

        self.parameter_template: dict[str, type[IOType]] = parameter_template
        self.result_template: dict[str, type[IOType]] = result_template
        self.results = [None for _ in self.result_template]


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

    def compute(self):
        # get inputs:
        inputs = self.graph.get_params(self)
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

    def connect_nodes(self, param_node: Node, param_idx: int, result_node: Node,
                      result_idx: int):
        if not param_node in self.nodes or not result_node in self.nodes:
            raise ValueError("At least one of the provided nodes is unknown to the graph")
        # TODO: check for types etc.
        self.connections[param_node][param_idx] = (result_node, result_idx)
        result_node.new_params.connect(param_node.on_new_data)

    def disconnect_nodes(self, param_node: Node, param_idx: int):
        if not param_node in self.connections:
            return
        connected = self.connections[param_node][param_idx] 
        if not connected is None:
            connected[0].new_params.disconnect(param_node.on_new_data)
            self.connections[param_node][param_idx] = None

    def get_params(self, node: Node):
        if node in self.connections:
            inputs = []
            for connection in self.connections[node]:
                if connection is None:
                    inputs.append(None)
                else:
                    connected_node, connected_idx = connection
                    inputs.append(connected_node.get_result(connected_idx))
        else:
            inputs = [None for _ in node.parameter_template]
        return inputs



class IDXNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, {}, {"Idx": Int})

    @override
    def compute_function(self, inputs):
        idx = random.randint(0, 100)
        print(idx)
        return [idx]

    @override
    def get_result(self, idx: int):
        print("get_result IDX")
        return super().get_result(idx)


class SourceNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, {"Idx": Int}, {"Image": GrayScaleImage})

        self.path = "/home/tim/Documents/Arbeit/HDF5Test/SO298_298-10-1_PISCO2_20230422-2334_Results/Images/"
        self.files = list(os.listdir(self.path))

    @override
    def compute_function(self, inputs):
        print(inputs)
        if inputs[0] is None:
            file = random.choice(self.files)
        else:
            file = self.files[inputs[0]]
        img = cv.imread(os.path.join(self.path, file), cv.IMREAD_GRAYSCALE)
        return [img]

    @override
    def get_result(self, idx: int):
        return super().get_result(idx)

class ABSDiffNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, {"Image 1": GrayScaleImage, "Image 2": GrayScaleImage},
                         {"Result Image": GrayScaleImage})

    @override
    def compute_function(self, inputs: list[np.ndarray]):
        img1 = inputs[0]
        img2 = inputs[1]
        if img1 is None or img2 is None:
            return [None]
        img = cv.absdiff(img1, img2)
        return [img]

    @override
    def get_result(self, idx: int):
        print("get_result ABSDiff")
        return super().get_result(idx)



if __name__ == "__main__":
    graph = Graph()

    i1 = IDXNode(graph)
    s1 = SourceNode(graph)
    s2 = SourceNode(graph)
    n1 = ABSDiffNode(graph)

    graph.add_node(i1)
    graph.add_node(s1)
    graph.add_node(s2)
    graph.add_node(n1)

    graph.connect_nodes(s1, 0, i1, 0)
    graph.connect_nodes(n1, 0, s1, 0)
    graph.connect_nodes(n1, 1, s2, 0)


    cv.imshow("img", n1.get_result(0))
    cv.waitKey(0)
    print()

    i1.new_params.emit()
    i1.compute()

    cv.imshow("img", n1.get_result(0))
    cv.waitKey(0)

