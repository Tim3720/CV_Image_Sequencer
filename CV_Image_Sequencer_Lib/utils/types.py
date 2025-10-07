from typing import Generic, TypeVar, override
import cv2 as cv
from enum import Enum
from cv2.gapi import BGR2RGB
import numpy as np

from pydantic import BaseModel, field_validator

T = TypeVar("T")
class TypeBaseModel(BaseModel, Generic[T]):
    value: T | None

    model_config = {
        "arbitrary_types_allowed": True
    }

    def get_model_type(self) -> type:
        return type(T)

    def get_default_value(self) -> T | None:
        return None

    def from_string(self, value: str) -> object:
        return None


class ColorCode3C23C(Enum):
    """Color codes for conversion from a 3 channel image to a 3 channel image."""
    BGR2RGB = cv.COLOR_BGR2RGB


class ColorCode3C21C(Enum):
    """Color codes for conversion from a 3 channel image to a 1 channel image."""
    BGR2GRAY = 0
    B2GRAY = 1
    G2GRAY = 2
    R2GRAY = 3

class ColorCode1C23C(Enum):
    """Color codes for conversion from a 1 channel image to a 3 channel image."""
    GRAY2BGR = cv.COLOR_GRAY2BGR


class ColorCodeType3C23C(TypeBaseModel[ColorCode3C23C]):
    value: ColorCode3C23C | None = None

    @override
    def get_default_value(self) -> ColorCode3C23C | None:
        return ColorCode3C23C.BGR2RGB

    def get_model_type(self) -> type:
        return ColorCode3C23C

class ColorCodeType3C21C(TypeBaseModel[ColorCode3C21C]):
    value: ColorCode3C21C | None = None

    @override
    def get_default_value(self) -> ColorCode3C21C | None:
        return ColorCode3C21C.BGR2GRAY

    def get_model_type(self) -> type:
        return ColorCode3C21C

    @override
    def from_string(self, value: str):
        return ColorCodeType3C21C(value=ColorCode3C21C[value])


class Image3CType(TypeBaseModel[np.ndarray]):
    value: np.ndarray | None = None

    @field_validator("value")
    def check_channels(cls, arr):
        if arr.ndim != 3 or arr.shape[2] != 3:
            raise ValueError("Expected an image with 3 channels")
        return arr

    def get_model_type(self) -> type:
        return np.ndarray


class GrayScaleImageType(TypeBaseModel[np.ndarray]):
    value: np.ndarray | None = None

    @field_validator("value")
    def check_channels(cls, arr):
        if arr.ndim == 3 and arr.shape[2] != 1:
            raise ValueError("Expected an Grayscale image with 1 channel")
        return arr

    def get_model_type(self) -> type:
        return np.ndarray
