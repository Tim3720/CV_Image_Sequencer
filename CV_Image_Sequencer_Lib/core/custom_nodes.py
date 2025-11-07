from typing import Any, Optional, override
import random
import numpy as np
import cv2 as cv
import os

from .types import Float, GrayScaleImage, Int, ThresholdType

from .nodes import Node, Graph

class IDXNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [], [("Idx", Int)])

    @override
    def compute_function(self, inputs):
        idx = random.randint(0, 100)
        print(idx)
        return [idx]


class SourceNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Idx", Int)], [("Image", GrayScaleImage)])

        self.path = "/home/tim/Documents/Arbeit/HDF5Test/SO298_298-10-1_PISCO2_20230422-2334_Results/Images/"
        self.files = list(os.listdir(self.path))
        self.name = "SourceNode"

        self.min_values = [Int(value=0)]
        self.max_values = [Int(value=len(self.files) - 1)]
        self.default_values = [Int(value=1)]



    @override
    def compute_function(self, inputs):
        if inputs[0] is None:
            file = random.choice(self.files)
        else:
            file = self.files[inputs[0].value]
        img = cv.imread(os.path.join(self.path, file), cv.IMREAD_GRAYSCALE)
        return [GrayScaleImage(value=img)]

class ABSDiffNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image 1", GrayScaleImage), ("Image 2", GrayScaleImage)],
                         [("Result Image", GrayScaleImage)])
        self.name = "AbsDiffNode"

    @override
    def compute_function(self, inputs: list[Optional[GrayScaleImage]]):
        if inputs[0] is None or inputs[1] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        img2 = inputs[1].value
        if img1 is None or img2 is None:
            return [GrayScaleImage(value=None)]
        img = cv.absdiff(img1, img2)
        return [GrayScaleImage(value=img)]

class ThresholdNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image 1", GrayScaleImage), ("Threshold value", Float),
                                 ("New value", Int), ("Threshold type", ThresholdType)],
                         [("Result Image", GrayScaleImage), ("Threshold value", Float)])
        self.name = "ThresholdNode"

        self.min_values[1] = Float(value=0)
        self.min_values[2] = Int(value=0)
        self.max_values[1] = Float(value=255)
        self.max_values[2] = Int(value=255)

        self.default_values[1] = Float(value=10)
        self.default_values[2] = Int(value=255)
        self.default_values[3] = ThresholdType(value="Thresh Binary")

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        if img1 is None:
            return [GrayScaleImage(value=None)]

        t, img = cv.threshold(img1, inputs[1].value, inputs[2].value, ThresholdType.options[inputs[3].value])
        return [GrayScaleImage(value=img), Float(value=t)]




# class BlackBoxOuterNode(Node):
#     def __init__(self, graph: Graph, parameter_template: list[type], result_template: list[type]):
#         super().__init__(graph, parameter_template, result_template)
#
#     @override
#     def compute_function(self, inputs: list[Any]):
#         return inputs
#
#     @override
#     def get_result(self, idx: int):
#         print("get_result Blackbox outer")
#         return super().get_result(idx)
#
#
# class BlackBox:
#     def __init__(self, graph: Graph):
#         # super().__init__(graph, [int, int], [np.ndarray])
#         self.sub_graph = Graph()
#         self.outer_node1 = BlackBoxOuterNode(graph, [int, int], [int, int])
#         self.outer_node2 = BlackBoxOuterNode(self.sub_graph, [np.ndarray], [np.ndarray])
#         graph.add_node(self.outer_node1)
#         graph.add_node(self.outer_node2)
#
#         s1 = SourceNode(self.sub_graph)
#         s2 = SourceNode(self.sub_graph)
#         self.n1 = ABSDiffNode(self.sub_graph)
#
#         self.sub_graph.add_node(s1)
#         self.sub_graph.add_node(s2)
#         self.sub_graph.add_node(self.n1)
#         self.sub_graph.add_node(self.outer_node1)
#         self.sub_graph.add_node(self.outer_node2)
#
#         self.sub_graph.connect_nodes(self.n1, 0, s1, 0)
#         self.sub_graph.connect_nodes(self.n1, 1, s2, 0)
#
#         self.sub_graph.connect_nodes(s1, 0, self.outer_node1, 0)
#         self.sub_graph.connect_nodes(s2, 0, self.outer_node1, 1)
#
#         self.sub_graph.connect_nodes(self.outer_node2, 0, self.n1, 0)
#
#     def get_result(self, idx: int):
#         return self.outer_node2.get_result(idx)
