from typing import Any, Optional, override
import random
import numpy as np
import cv2 as cv
import os

from ..utils.source_manager import SourceManager
from .types import ColorImage, Float, GrayScaleImage, Int, ThresholdType
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
    def __init__(self, graph: Graph, source_manager: SourceManager, n_frames: int = 1,
                 grayscale_mode: bool = False):

        if grayscale_mode:
            super().__init__(graph, [("Offset", Int)], [*[("Image", GrayScaleImage) for _ in
                                                 range(n_frames)]])
        else:
            super().__init__(graph, [("Offset", Int)], [*[("Image", ColorImage) for _ in
                                                 range(n_frames)]])

        self.n_frames = n_frames
        self.grayscale_mode = grayscale_mode
        self.source_manager = source_manager

        self.name = "SourceNode"

        self.min_values = [Int(value=0)]
        self.max_values = [Int(value=self.source_manager.get_number_of_frames())]
        self.default_values = [Int(value=0)]

    @override
    def compute_function(self, inputs):
        offset = inputs[0].value
        frames = self.source_manager.get_next_n_frames(self.n_frames, offset, self.grayscale_mode)
        if frames is None:
            if self.grayscale_mode:
                frames = [GrayScaleImage(None) for _ in range(self.n_frames)]
            else:
                frames = [ColorImage(None) for _ in range(self.n_frames)]
        # frames.append(offset)
        return frames

    @override
    def to_dict(self):
        d = super().to_dict()
        d["params"] = {"n_frames": self.n_frames, "grayscale_mode": self.grayscale_mode}
        return d


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
                                 ("New value", Int), ("Type", ThresholdType)],
                         [("Result Image", GrayScaleImage), ("Threshold value", Float), ("Type", ThresholdType)])
        self.name = "ThresholdNode"

        self.min_values[1] = Float(value=0)
        self.min_values[2] = Int(value=0)
        self.max_values[1] = Float(value=255)
        self.max_values[2] = Int(value=255)

        self.default_values[1] = Float(value=10)
        self.default_values[2] = Int(value=255)
        self.default_values[3] = ThresholdType(value="Binary")

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None:
            return [GrayScaleImage(value=None), Float(value=0), inputs[3]]
        img1 = inputs[0].value
        if img1 is None:
            return [GrayScaleImage(value=None), Float(value=0), inputs[3]]

        t, img = cv.threshold(img1, inputs[1].value, inputs[2].value, ThresholdType.options[inputs[3].value])
        return [GrayScaleImage(value=img), Float(value=t), inputs[3]]


class InvertNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image 1", GrayScaleImage)],
                         [("Result Image", GrayScaleImage)])
        self.name = "InvertNode"

    @override
    def compute_function(self, inputs: list[Optional[GrayScaleImage]]):
        if inputs[0] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        if img1 is None:
            return [GrayScaleImage(value=None)]
        img = cv.bitwise_not(img1)
        return [GrayScaleImage(value=img)]

class MinNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image 1", GrayScaleImage), ("Image 2", GrayScaleImage)],
                         [("Result Image", GrayScaleImage)])
        self.name = "MinNode"

    @override
    def compute_function(self, inputs: list[Optional[GrayScaleImage]]):
        if inputs[0] is None or inputs[1] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        img2 = inputs[1].value
        if img1 is None or img2 is None:
            return [GrayScaleImage(value=None)]
        img = np.min([img1, img2], axis=0)
        return [GrayScaleImage(value=img)]


class MaxNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image 1", GrayScaleImage), ("Image 2", GrayScaleImage)],
                         [("Result Image", GrayScaleImage)])
        self.name = "MaxNode"

    @override
    def compute_function(self, inputs: list[Optional[GrayScaleImage]]):
        if inputs[0] is None or inputs[1] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        img2 = inputs[1].value
        if img1 is None or img2 is None:
            return [GrayScaleImage(value=None)]
        img = np.max([img1, img2], axis=0)
        return [GrayScaleImage(value=img)]


class ClampedDiffNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph,
                         parameter_template=[
                             ("Image 1", GrayScaleImage),
                             ("Image 2", GrayScaleImage),
                             ("Cutoff", Int)
                         ],
                         result_template=[
                             ("Result Image", GrayScaleImage)
                         ])

        self.min_values[2] = Int(0)
        self.max_values[2] = Int(255)
        self.default_values[2] = Int(0)

        self.name = "ClampedDiff"

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None or inputs[1] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        img2 = inputs[1].value
        if img1 is None or img2 is None:
            return [GrayScaleImage(value=None)]
        res = img1.astype(np.int32) - img2.astype(np.int32)
        res[res < inputs[2].value] = 0
        res = res.astype(np.uint8)
        return [GrayScaleImage(value=res)]


class SplitChannelNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image", ColorImage)],
                         [("Channel 1", GrayScaleImage), ("Channel 2", GrayScaleImage),
                          ("Channel 3", GrayScaleImage)])
        self.name = "SplitChannelsNode"

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None:
            return [GrayScaleImage(value=None), GrayScaleImage(value=None), GrayScaleImage(value=None)]
        img1 = inputs[0].value
        if img1 is None:
            return [GrayScaleImage(value=None), GrayScaleImage(value=None), GrayScaleImage(value=None)]

        ch1, ch2, ch3 = cv.split(img1)
        return [GrayScaleImage(value=ch1), GrayScaleImage(ch2), GrayScaleImage(ch3)]





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
