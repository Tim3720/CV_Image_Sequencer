from .workflow_base import Workflow
from ..utils.source_manager import SourceManager
from typing import override
import cv2 as cv
import numpy as np

from ..utils.types import Image3C, Image1C, ColorCode3C21C, Float

class GetFrame(Workflow):
    def __init__(self, source_manager: SourceManager, n_frames: int) -> None:
        super().__init__(n_inputs=1)
        self.n_frames = n_frames
        self.source_manager = source_manager

    @override
    def function(self, inputs: list) -> list:
        frames = self.source_manager.get_next_n_frames(self.n_frames,
                                                       inputs[0].get_value(), False)
        if frames is None:
            return [Image3C(value=None) for _ in range(self.n_frames)]
        output = []
        for i in range(len(frames)):
            output.append(Image3C(value=frames[i]))
        return output

class GetFrameGray(Workflow):
    def __init__(self, source_manager: SourceManager, n_frames: int) -> None:
        super().__init__(n_inputs=1)
        self.n_frames = n_frames
        self.source_manager = source_manager

    @override
    def function(self, inputs: list) -> list:
        frames = self.source_manager.get_next_n_frames(self.n_frames,
                                                       inputs[0].get_value(), True)
        if frames is None:
            return [Image1C(value=None) for _ in range(self.n_frames)]
        output = []
        for i in range(len(frames)):
            output.append(Image1C(value=frames[i]))
        return output

class GrayScale(Workflow):
    def __init__(self) -> None:
        super().__init__(n_inputs=2)

    @override
    def function(self, inputs: list) -> list:
        color_code: ColorCode3C21C = inputs[1]
        color_code_key = color_code.value
        if type(color_code_key) != str:
            raise ValueError("Color code in workflow grayscale not set")
        color_code_value = color_code.value_dict[color_code_key]

        if color_code_value == 0:
            frame = cv.cvtColor(inputs[0].value, cv.COLOR_RGB2GRAY)
        elif color_code_value == 1:
            frame = inputs[0].value[:, :, 0]
        elif color_code_value == 2:
            frame = inputs[0].value[:, :, 1]
        elif color_code_value == 3:
            frame = inputs[0].value[:, :, 2]
        else:
            raise ValueError("Invalid color code")
        return [Image1C(value=frame)]


# class ChangeColor(Workflow):
#     def __init__(self) -> None:
#         super().__init__(n_inputs=2)
#
#     @override
#     def function(self, inputs: list) -> list:
#         return [Image3CType(value=cv.cvtColor(inputs[0], inputs[1].value))]


class Threshold(Workflow):
    def __init__(self) -> None:
        super().__init__(n_inputs=4)

    @override
    def function(self, inputs) -> list:
        t, img = cv.threshold(inputs[0].get_value(), inputs[1].get_value(),
                              inputs[2].get_value(), inputs[3].get_value())
        return [Float(value=t), Image1C(value=img)]


class ChannelSplit(Workflow):
    def __init__(self) -> None:
        super().__init__(n_inputs=1)

    @override
    def function(self, inputs) -> list:
        channels = cv.split(inputs[0].get_value())
        output = []
        if not channels:
            for _ in range(3):
                output.append(Image1C(value=None))
            return output
        for channel in channels:
            output.append(Image1C(value=channel))
        return output

class ABSDiff(Workflow):
    def __init__(self) -> None:
        super().__init__(n_inputs=2)

    @override
    def function(self, inputs) -> list:
        output = cv.absdiff(inputs[0].get_value(), inputs[1].get_value())
        return [Image1C(value=output)]


class ClampedDiff(Workflow):
    def __init__(self) -> None:
        super().__init__(n_inputs=3)

    @override
    def function(self, inputs) -> list:
        if inputs[0].get_value() is None or inputs[1].get_value() is None:
            return [Image1C(value=None)]
        res = inputs[0].get_value().astype(np.int32) - inputs[1].get_value().astype(np.int32)
        res[res < inputs[2].get_value()] = 0
        res = res.astype(np.uint8)
        return [Image1C(value=res)]



class Invert3C(Workflow):
    def __init__(self) -> None:
        super().__init__(n_inputs=1)

    @override
    def function(self, inputs) -> list:
        res = cv.bitwise_not(inputs[0].get_value())
        return [Image3C(value=res)]


class CWiseOp(Workflow):
    def __init__(self) -> None:
        super().__init__(n_inputs=3)

    @override
    def function(self, inputs) -> list:
        res = inputs[1].value_dict[inputs[1].get_value()](inputs[0].get_value())
        return [Image1C(value=res)]


class Min(Workflow):
    def __init__(self) -> None:
        super().__init__(n_inputs=2)

    @override
    def function(self, inputs) -> list:
        if inputs[0].get_value() is None or inputs[1].get_value() is None:
            return [Image1C(value=None)]
        res = np.min([inputs[0].get_value(), inputs[1].get_value()], axis=0)
        return [Image1C(value=res)]


class Max(Workflow):
    def __init__(self) -> None:
        super().__init__(n_inputs=2)

    @override
    def function(self, inputs) -> list:
        if inputs[0].get_value() is None or inputs[1].get_value() is None:
            return [Image1C(value=None)]
        res = np.max([inputs[0].get_value(), inputs[1].get_value()], axis=0)
        return [Image1C(value=res)]
