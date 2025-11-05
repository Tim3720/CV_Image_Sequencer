import re
from typing import Callable
import numpy as np

from CV_Image_Sequencer_Lib.core.graph_manager import GraphManager

from ..utils.source_manager import SourceManager
from ..utils.types import Image1C, Image3C, Int, ThresholdTypes
from .node_base import DataNode, SourceNode, ComputationalNode, BlackBoxNode
import cv2 as cv

class ImageSourceNode(SourceNode):

    def __init__(self, image_source_function: Callable):
        output_node = DataNode(Image3C, "Image Out")
        self.image_source_function = image_source_function
        super().__init__([], [output_node], self.image_source_function, name="SourceNode")

    def get_data(self):
        data = self.image_source_function()
        return [data]

class GrayScaleNode(ComputationalNode):
    def __init__(self):
        input_node = DataNode(Image3C, name="Image In")
        output_node = DataNode(Image1C, name="Grayscale Image")
        super().__init__([input_node], [output_node], self.convert_to_gray, name="GrayScaleNode")

    def convert_to_gray(self, img: Image3C):
        if img.value is None:
            return Image1C(value=None)
        gray = cv.cvtColor(img.value, cv.COLOR_BGR2GRAY)
        return [Image1C(value=gray)]

class MinNode(ComputationalNode):
    def __init__(self):
        input_nodes = [
                DataNode(Image1C, name="Image 1"),
                DataNode(Image1C, name="Image 2"),
                ]
        output_node = DataNode(Image1C, name="Grayscale Image")

        super().__init__(input_nodes, [output_node], self.function, name=self.__class__.__name__)

    def function(self, image1: Image1C, image2: Image1C):
        if image1.value is None and image2.value is None:
            return Image1C(value=None)
        elif image1.value is None:
            return image2
        elif image2.value is None:
            return image1

        res = np.min([image1.value, image2.value], axis=0)
        return [Image1C(value=res)]


class ABSDiffNode(ComputationalNode):
    def __init__(self):
        input_nodes = [
                DataNode(Image1C, name="Image 1"),
                DataNode(Image1C, name="Image 2"),
                ]
        output_node = DataNode(Image1C, name="Diff Image")

        super().__init__(input_nodes, [output_node], self.function, name=self.__class__.__name__)

    def function(self, image1: Image1C, image2: Image1C):
        if image1.value is None and image2.value is None:
            return Image1C(value=None)
        elif image1.value is None:
            return image2
        elif image2.value is None:
            return image1

        res = cv.absdiff(image1.value, image2.value)
        return [Image1C(value=res)]

class ThresholdNode(SourceNode):
    def __init__(self):
        image_input = DataNode(Image1C, name="Image 1")
        self.threshold_val_input = DataNode(Int, name="Threshold value")
        self.threshold_new_val_input = DataNode(Int, name="New value")
        self.threshold_type_input = DataNode(ThresholdTypes, name="Threshold type")

        output_node = DataNode(Image1C, name="Threshold Image")

        super().__init__([image_input, self.threshold_val_input, self.threshold_new_val_input, self.threshold_type_input], [output_node], self.function, name=self.__class__.__name__)

        # self.source_node_input.data_request_signal.connect(self.on_unconnected_request)

    def on_unconnected_request(self):
        if self.threshold_type_input.input_node is None:
            t = ThresholdTypes()
            self.threshold_type_input.send_data((t.get_default_value(), None), False)
        if self.threshold_val_input.input_node is None:
            t = Int(value=50)
            self.threshold_val_input.send_data((t, None), False)
        if self.threshold_new_val_input.input_node is None:
            t = Int(value=255)
            self.threshold_new_val_input.send_data((t, None), False)

    def function(self, image1: Image1C, threshold_val: Int, threshold_new_val: Int, threshold_type: ThresholdTypes):
        print("Threshold type:", threshold_type.get_value)
        if image1.value is None:
            return [Image1C(value=None)]

        res = cv.threshold(image1.value, threshold_val.get_value(), threshold_new_val.get_value(), threshold_type.get_value())[1]
        return [Image1C(value=res)]

