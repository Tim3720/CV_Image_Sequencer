import colorsys
from typing import Any, ClassVar, Optional, override, TypeVar, Dict, Type
from dataclasses import dataclass
import numpy as np
import cv2 as cv


T = TypeVar("T", bound="Serializable")
class Serializable:
    _registry: Dict[str, Type["Serializable"]] = {}

    def __init_subclass__(cls, **kwargs):
        """Automatically register subclasses by class name."""
        super().__init_subclass__(**kwargs)
        Serializable._registry[cls.__name__] = cls


class ColorRegistry:
    _index = 0
    _colors = {}

    @classmethod
    def get_color(cls, key: str):
        if key not in cls._colors:
            hue = (cls._index * 0.618034) % 1.0  # golden ratio spacing
            cls._index += 1
            rgb = colorsys.hsv_to_rgb(hue, 0.6, 0.95)
            rgb_255 = []
            for i in range(3):
                rgb_255.append(int(round(255 * rgb[i])))
            cls._colors[key] = tuple(rgb_255)
        return cls._colors[key]


@dataclass
class IOType:
    value: Any

    def __init_subclass__(cls):
        cls.color = ColorRegistry.get_color(cls.__name__)

    def value_okay(self, other: "IOType") -> bool:
        if type(other) != type(self):
            return False
        return True



@dataclass
class GrayScaleImage(IOType):
    value: Optional[np.ndarray]

    @override
    def value_okay(self, other: "IOType") -> bool:
        if not isinstance(other, GrayScaleImage):
            return False
        if other.value is None:
            return True
        if len(other.value.shape) > 2 and other.value.shape[2] > 1:
            return False
        return True

@dataclass
class ColorImage(IOType):
    value: Optional[np.ndarray]

    @override
    def value_okay(self, other: "IOType") -> bool:
        if not isinstance(other, ColorImage):
            return False
        if other.value is None:
            return True
        if len(other.value.shape) < 3 or other.value.shape[2] < 3:
            return False
        return True

@dataclass
class Option(IOType):
    value: str
    options: ClassVar[dict[str, Any]]


@dataclass
class ThresholdType(Option):
    value: str
    options: ClassVar[dict[str, Any]] = {
        "Binary": cv.THRESH_BINARY,
        "Triangle": cv.THRESH_TRIANGLE,
        "Otsu": cv.THRESH_OTSU,
    }


@dataclass
class MorphologyTypes(Option):
    value: str
    options: ClassVar[dict[str, Any]] = {
        "Close": cv.MORPH_CLOSE,
        "Open": cv.MORPH_OPEN,
    }


@dataclass
class Scalar(IOType):
    value: Any

@dataclass
class Int(Scalar):
    value: int

@dataclass
class Float(Scalar):
    value: float

@dataclass
class String(Scalar):
    value: str

@dataclass
class Contours(IOType):
    value: Optional[list]
    
    @override
    def value_okay(self, other: "IOType") -> bool:
        if not isinstance(other, Contours):
            return False
        return True
