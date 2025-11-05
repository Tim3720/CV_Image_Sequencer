from .nodes import Node, InputSocket, OutputSocket
from .types import GrayScaleImage, Int

import cv2 as cv
from uuid import UUID
from typing import Any


class ImageInputNode(Node):
    """Provides a fixed grayscale image."""
    def __init__(self, image: GrayScaleImage, x: float = 0, y: float = 0):
        super().__init__("ImageInputNode", x, y)
        self.image = image
        self.add_output("image", GrayScaleImage)

    def compute(self, inputs: dict[UUID, Any]) -> dict[UUID, Any]:
        return {self.output_uuids[0]: self.image}

class ABSDiffNode(Node):
    """Adds brightness to an image based on manual or connected value."""
    def __init__(self, x: float = 0, y: float = 0):
        super().__init__("AbsDiffNode", x, y)
        self.add_input("image 1", GrayScaleImage)
        self.add_input("image 2", GrayScaleImage)
        int_in = self.add_input("test int", Int)
        self.add_output("result", GrayScaleImage)

        int_in.set_manual_value(Int(value=0))

    def compute(self, inputs: dict[UUID, Any]) -> dict[UUID, Any]:
        img1: GrayScaleImage = inputs[self.input_uuids[0]]
        img2: GrayScaleImage = inputs[self.input_uuids[1]]
        if img1.value is None or img2.value is None:
            return {self.output_uuids[0]: None}

        res = cv.absdiff(img1.value, img2.value)
        result = GrayScaleImage(res)
        return {self.output_uuids[0]: result}

class InvertNode(Node):
    """Adds brightness to an image based on manual or connected value."""
    def __init__(self, x: float = 0, y: float = 0):
        super().__init__("InvertNode", x, y)
        self.add_input("image 1", GrayScaleImage)
        self.add_output("result", GrayScaleImage)

    def compute(self, inputs: dict[UUID, Any]) -> dict[UUID, Any]:
        img1: GrayScaleImage = inputs[self.input_uuids[0]]
        if img1.value is None:
            return {self.output_uuids[0]: None}

        res = cv.bitwise_not(img1.value)
        result = GrayScaleImage(res)
        return {self.output_uuids[0]: result}

