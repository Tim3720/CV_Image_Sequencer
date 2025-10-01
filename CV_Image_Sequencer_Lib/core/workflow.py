from typing import Callable, Generic, TypeVar, override
import cv2 as cv
from pydantic import BaseModel

from CV_Image_Sequencer_Lib.utils.types import ColorCode3C21C, ColorCodeType3C21C, GrayScaleImageType, Image3CType
from CV_Image_Sequencer_Lib.utils.video_manager import VideoManager


T = TypeVar("T")
class Setting(BaseModel, Generic[T]):
    name: str
    setting_value: T

class Workflow:
    def __init__(self, n_inputs: int) -> None:
        self.n_inputs = n_inputs
        self.name: str = ""

    def function(self, inputs: list) -> list:
        """ Override this function to add the correct functionality of the workflow and
        ensure the correct order of parameters. All inputs given to the workflow are
        available and the arguments set by the __init__ override can be used with
        'self.args'."""
        return inputs

    def run(self, inputs: list) -> list:
        """ This function will be executed when the workflow is applied to an input. It
        has to handle the correct order of arguments in the corresponding function
        call. All parameters are included in the settings."""
        if len(inputs) != self.n_inputs:
            raise ValueError(f"Number of inputs does not match the expected number: {len(inputs)} != {self.n_inputs}")
        res = inputs.copy()
        res = self.function(res)
        return res


class GetFrame(Workflow):
    def __init__(self, video_manager: VideoManager) -> None:
        super().__init__(n_inputs=0)
        self.name = "GetFrame"
        self.video_manager = video_manager

    @override
    def function(self, inputs: list) -> list:
        frame = self.video_manager.get_current_frame()
        return [Image3CType(value=frame)]

class GrayScale(Workflow):
    def __init__(self) -> None:
        super().__init__(n_inputs=2)
        self.name = "To GrayScale"

    @override
    def function(self, inputs: list) -> list:
        if inputs[1] == ColorCode3C21C.BGR2GRAY:
            frame = cv.cvtColor(inputs[0], cv.COLOR_RGB2GRAY)
        elif inputs[1] == ColorCode3C21C.B2GRAY:
            frame = inputs[0][:, :, 0]
        elif inputs[1] == ColorCode3C21C.G2GRAY:
            frame = inputs[0][:, :, 1]
        elif inputs[1] == ColorCode3C21C.R2GRAY:
            frame = inputs[0][:, :, 2]
        else:
            raise ValueError("Invalid color code")
        return [GrayScaleImageType(value=frame)]


class ChangeColor(Workflow):
    def __init__(self) -> None:
        super().__init__(1)

    @override
    def function(self, inputs: list) -> list:
        return [cv.cvtColor(*inputs)]
