import colorsys
from typing import Any, Optional, override
from dataclasses import dataclass
import numpy as np

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
    value: dict[str, Any]



@dataclass
class Scalar(IOType):
    value: Any
    min_value: Optional[Any]
    max_value: Optional[Any]

@dataclass
class Int(Scalar):
    value: int
    min_value: Optional[int] = None
    max_value: Optional[int] = None

@dataclass
class Float(Scalar):
    value: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
