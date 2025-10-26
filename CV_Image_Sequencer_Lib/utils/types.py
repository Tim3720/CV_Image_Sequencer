from typing import Any, override
import cv2 as cv
import numpy as np
from dataclasses import dataclass

from .type_base import IOType, DictType

@dataclass
class ColorCode3C21C(DictType):
    """Color codes for conversion from a 3 channel image to a 1 channel image."""
    value_dict = {
                "BGR2GRAY": 0,
                "B2GRAY": 1,
                "G2GRAY": 2,
                "R2GRAY": 3,
                }
    value: str | None = None
    default_value = "BGR2GRAY"

    def get_default_value(self):
        return ColorCode3C21C(value=self.default_value)


@dataclass
class ThresholdTypes(DictType):
    value_dict = {
                "Binary": cv.THRESH_BINARY,
                "Triangle": cv.THRESH_TRIANGLE,
                "Otsu": cv.THRESH_OTSU,
                }
    value: str | None = None
    default_value = "Binary"

    def get_default_value(self):
        return ThresholdTypes(value=self.default_value)

@dataclass
class BitWiseOperations(DictType):
    value_dict = {
                "And": cv.bitwise_and,
                "Or": cv.bitwise_or,
                "XOr": cv.bitwise_xor,
                }
    value: str | None = None
    default_value = "And"

    def get_default_value(self):
        return ThresholdTypes(value=self.default_value)


@dataclass
class Image3C(IOType):
    value: np.ndarray | None = None
    data_type: type = np.ndarray

    def __post_init__(self):
        if self.value is None:
            return
        if self.value.ndim != 3 or self.value.shape[2] != 3:
            raise ValueError("Expected an image with 3 channels")

@dataclass
class Image1C(IOType):
    value: np.ndarray | None = None
    data_type: type = np.ndarray

    def __post_init__(self):
        if self.value is None:
            return
        if self.value.ndim == 3 and self.value.shape[2] != 1:
            raise ValueError("Expected an image with 3 channels")


@dataclass
class Scalar(IOType):
    default_value = 0
    min_value: Any | None = None
    max_value: Any | None = None

    def __post_init__(self):
        if self.value is None:
            return
        if not self.min_value is None and self.value < self.min_value:
            raise ValueError(f"Value {self.value} is out ouf bounds for Scalar")
        if not self.max_value is None and self.value > self.max_value:
            raise ValueError(f"Value {self.value} is out ouf bounds for Scalar")

    @override
    def set_value(self, value):
        if not self.min_value is None and value < self.min_value:
            raise ValueError(f"Value {value} is out ouf bounds for Scalar")
        if not self.max_value is None and value > self.max_value:
            raise ValueError(f"Value {value} is out ouf bounds for Scalar")
        self.value = value
        return self

    def set_value_from_string(self, value: str):
        return self.set_value(int(value))


@dataclass
class Float(Scalar):
    value: float | None = None
    data_type: type = float
    default_value = 0
    min_value: float | None = None
    max_value: float | None = None

    @override
    def get_default_value(self) -> object:
        return Float(value=self.default_value)

    def set_value_from_string(self, value: str):
        return self.set_value(float(value))



@dataclass
class Int(Scalar):
    value: int | None = None
    data_type: type = int
    default_value = 0
    min_value: int | None = None
    max_value: int | None = None

    def get_default_value(self) -> object:
        return Int(value=self.default_value)

    def set_value_from_string(self, value: str):
        return self.set_value(int(value))

@dataclass
class Bool(IOType):
    value: int | None = None
    data_type: type = bool
    default_value = False

    def get_default_value(self) -> object:
        return Bool(value=self.default_value)




TYPE_DICT = {
        }
