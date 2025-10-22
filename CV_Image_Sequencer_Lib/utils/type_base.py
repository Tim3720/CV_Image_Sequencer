from dataclasses import dataclass
from typing import Any


@dataclass
class Type:
    data_type: type
    value: Any | None = None
    default_value = None

    def get_default_value(self) -> object:
        return Type(data_type=self.data_type)

    def set_value(self, value):
        self.value = value
        return self

    def get_value(self):
        return self.value

@dataclass
class DictType(Type):
    value_dict = {}
    data_type: type = str

    def get_value(self):
        return self.value_dict[self.value]




#
#
#
# T = TypeVar("T")
# class TypeBaseModel(BaseModel, Generic[T]):
#     value: T | None
#
#     model_config = {
#         "arbitrary_types_allowed": True
#     }
#
#     def get_model_type(self) -> type:
#         return type(T)
#
#     def get_default_value(self) -> T | None:
#         return None
#
#     def from_string(self, value: str) -> object:
#         return None
#
#
#
# class ColorCode3C23C(Enum):
#     """Color codes for conversion from a 3 channel image to a 3 channel image."""
#     BGR2RGB = cv.COLOR_BGR2RGB
#
#
# # class ColorCode3C21C(Enum):
# #     """Color codes for conversion from a 3 channel image to a 1 channel image."""
# #     BGR2GRAY = 0
# #     B2GRAY = 1
# #     G2GRAY = 2
# #     R2GRAY = 3
#
# class ColorCode1C23C(Enum):
#     """Color codes for conversion from a 1 channel image to a 3 channel image."""
#     GRAY2BGR = cv.COLOR_GRAY2BGR
#
# class ScalarType(TypeBaseModel[T]):
#     value: T | None = None
#     min_value: T | None = None
#     max_value: T | None = None
#
#     @field_validator("value")
#     @classmethod
#     def check_bounds(cls, v, info):
#         min_val = info.data.get("min_value")
#         max_val = info.data.get("max_value")
#         if v is not None:
#             if min_val is not None and v < min_val:
#                 raise ValueError(f"value {v} is below minimum {min_val}")
#             if max_val is not None and v > max_val:
#                 raise ValueError(f"value {v} is above maximum {max_val}")
#         return v
#
# class IntType(ScalarType[int]):
#     value: int | None = None
#     def get_default_value(self) -> int | None:
#         return 0
#
#     @override
#     def from_string(self, value: str):
#         return IntType(value=int(value), min_value=self.min_value, max_value=self.max_value)
#
#     def get_model_type(self) -> type:
#         return int
#
# class FloatType(ScalarType[float]):
#     value: float | None = None
#     def get_default_value(self) -> float | None:
#         return 0.
#
#     @override
#     def from_string(self, value: str):
#         return FloatType(value=float(value), min_value=self.min_value, max_value=self.max_value)
#
#     def get_model_type(self) -> type:
#         return float
#
#
# class ColorCodeType3C23C(TypeBaseModel[ColorCode3C23C]):
#     value: ColorCode3C23C | None = None
#
#     @override
#     def get_default_value(self) -> ColorCode3C23C | None:
#         return ColorCode3C23C.BGR2RGB
#
#     def get_model_type(self) -> type:
#         return ColorCode3C23C
#
#
# class Image3CType(TypeBaseModel[np.ndarray]):
#     value: np.ndarray | None = None
#
#     @field_validator("value")
#     def check_channels(cls, arr):
#         if arr.ndim != 3 or arr.shape[2] != 3:
#             raise ValueError("Expected an image with 3 channels")
#         return arr
#
#     def get_model_type(self) -> type:
#         return np.ndarray
#
#
# class GrayScaleImageType(TypeBaseModel[np.ndarray]):
#     value: np.ndarray | None = None
#
#     @field_validator("value")
#     def check_channels(cls, arr):
#         if arr.ndim == 3 and arr.shape[2] != 1:
#             raise ValueError("Expected an Grayscale image with 1 channel")
#         return arr
#
#     def get_model_type(self) -> type:
#         return np.ndarray
