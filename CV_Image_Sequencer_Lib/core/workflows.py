from numpy import isin
from CV_Image_Sequencer_Lib.utils.type_base import Type
from .workflow_base import Workflow
from CV_Image_Sequencer_Lib.utils.video_manager import VideoManager
from typing import override
import cv2 as cv

from ..utils.types import Image3C, Image1C, ColorCode3C21C, Int, Float

class GetFrame(Workflow):
    def __init__(self, video_manager: VideoManager, n_frames: int) -> None:
        super().__init__(n_inputs=0)
        self.n_frames = n_frames
        self.video_manager = video_manager

    @override
    def function(self, inputs: list) -> list:
        frames = self.video_manager.get_next_n_frames(self.n_frames)
        if frames is None:
            raise ValueError(f"VideoManager could not read next {self.n_frames} frames.")
        output = []
        for i in range(len(frames)):
            output.append(Image3C(value=frames[i]))
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

