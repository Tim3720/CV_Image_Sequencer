from typing import Optional
from PySide6.QtCore import Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QComboBox, QLabel, QHBoxLayout, QLineEdit, QMenu, QSizePolicy, QWidget
import numpy as np
import cv2 as cv


from ...assets.styles.style import STYLE
from ...core.types import ColorImage, Float, GrayScaleImage, IOType, Int, Option
from ...core.nodes import Node
from ...utils.source_manager import convert_cv_to_qt



class TypeVis(QWidget):

    def __init__(self, node: Node, idx: int, dtype: type[IOType], name: str, is_input: bool):
        super().__init__()
        self.node: Node = node
        self.idx = idx
        self.dtype: type[IOType] = dtype
        self.name: str = name
        self.is_input: bool = is_input

        self.init_ui()


    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if self.dtype == ColorImage or self.dtype == GrayScaleImage:
            self.widget = ImageVis(self.node, self.idx, self.dtype, self.name, self.is_input)
        elif issubclass(self.dtype, Int):
            self.widget = IntVis(self.node, self.idx, self.dtype, self.name, self.is_input)
        elif issubclass(self.dtype, Float):
            self.widget = FloatVis(self.node, self.idx, self.dtype, self.name, self.is_input)
        elif issubclass(self.dtype, Option):
            self.widget = OptionVis(self.node, self.idx, self.dtype, self.name, self.is_input)
        else:
            self.widget = QLabel(self.name)
        
        layout.addWidget(self.widget)

    @Slot(object)
    def new_input_data(self, data):
        if isinstance(self.widget, ImageVis):
            self.widget.new_img(data)
        elif isinstance(self.widget, IntVis):
            self.widget.on_new_input(data)
        elif isinstance(self.widget, FloatVis):
            self.widget.on_new_input(data)
        elif isinstance(self.widget, OptionVis):
            self.widget.on_new_input(data)



class ImageVis(QWidget):

    def __init__(self, node: Node, idx: int, dtype: type[IOType], name: str, is_input: bool):
        super().__init__()
        
        self.node = node
        self.idx = idx
        self.dtype = dtype
        self.name = name
        self.is_input = is_input

        if not self.is_input:
            node.new_results.connect(self.on_new_results)

        self.img_size = 30
        random_img = np.random.randint(0, 255, (self.img_size, self.img_size), np.uint8)
        self.image = convert_cv_to_qt(random_img)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background-color: transparent;")

        label = QLabel(self.name)
        label.setStyleSheet("background-color: transparent;")

        self.image_label = QLabel()
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setFixedSize(self.img_size, self.img_size)
        self.image_label.setPixmap(QPixmap(self.image))


        layout.addWidget(label)
        layout.addWidget(self.image_label)


    def on_new_results(self):
        data = self.node.results[self.idx]
        self.new_img(data)

    @Slot()
    def new_img(self, data):
        if data is None:
            return
        if data.value is None:
            random_img = np.random.randint(0, 255, (self.img_size, self.img_size), np.uint8)
            self.image = convert_cv_to_qt(random_img)
            self.image_label.setPixmap(QPixmap(self.image))
        else:
            self.image = convert_cv_to_qt(cv.resize(data.value, (self.img_size, self.img_size)))
            self.image_label.setPixmap(QPixmap(self.image))


class IntVis(QWidget):

    def __init__(self, node: Node, idx: int, dtype: type[Int], name: str, is_input: bool):
        super().__init__()
        
        self.node = node
        self.idx = idx
        self.dtype = dtype
        self.name = name
        self.is_input = is_input

        self.init_ui()

        if self.is_input:
            self.input.textChanged.connect(self._set_data)
        else:
            self.input.setReadOnly(True)
            self.node.new_results.connect(self.on_new_results)


    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background-color: transparent;")

        label = QLabel(self.name)
        label.setStyleSheet("background-color: transparent;")
        layout.addWidget(label)

        self.input = QLineEdit()
        self.input.setFixedSize(40, 20)
        self.input.setStyleSheet("border: 1px solid black;")
        self.input.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        default_value = self.node.default_values[self.idx]
        if self.is_input and not default_value is None:
            self.input.setText(str(default_value.value))

        layout.addWidget(self.input)

    @Slot()
    def on_new_results(self):
        data = self.node.results[self.idx]
        if data is None:
            return
        self.input.setText(str(data.value))

    @Slot(Int)
    def on_new_input(self, data: Optional[Int]):
        if data is None:
            return
        self.input.setText(str(data.value))

    @Slot()
    def _set_data(self):
        text = self.input.text()
        try: 
            value = int(text)
            min_value = self.node.min_values[self.idx]
            max_value = self.node.max_values[self.idx]
            if not min_value is None and value < min_value.value:
                self.input.setStyleSheet("color: red; border: 1px solid black")
            elif not max_value is None and value > max_value.value:
                self.input.setStyleSheet("color: red; border: 1px solid black")
            else:
                self.node.external_inputs[self.idx] = Int(value)
                self.node.compute()
                self.node.new_params.emit()

                self.input.setStyleSheet(f"color: {STYLE["textcolor"]}; border: 1px solid black;")

        except Exception:
            self.input.setStyleSheet("color: red;border: 1px solid black;")

class FloatVis(QWidget):

    def __init__(self, node: Node, idx: int, dtype: type[Float], name: str, is_input: bool):
        super().__init__()
        
        self.node = node
        self.idx = idx
        self.dtype = dtype
        self.name = name
        self.is_input = is_input

        self.init_ui()

        if self.is_input:
            self.input.textChanged.connect(self._set_data)
        else:
            self.input.setReadOnly(True)
            self.node.new_results.connect(self.on_new_results)


    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background-color: transparent;")

        label = QLabel(self.name)
        label.setStyleSheet("background-color: transparent;")
        layout.addWidget(label)

        self.input = QLineEdit()
        self.input.setFixedSize(40, 20)
        self.input.setStyleSheet("border: 1px solid black;")
        self.input.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        default_value = self.node.default_values[self.idx]
        if self.is_input and not default_value is None:
            self.input.setText(str(default_value.value))

        layout.addWidget(self.input)

    @Slot()
    def on_new_results(self):
        data = self.node.results[self.idx]
        if data is None:
            return
        self.input.setText(str(data.value))

    @Slot(Int)
    def on_new_input(self, data: Optional[Float]):
        if data is None:
            return
        if self.input.hasFocus():
            return
        self.input.setText(str(data.value))

    @Slot()
    def _set_data(self):
        text = self.input.text()
        try: 
            value = float(text)
            min_value = self.node.min_values[self.idx]
            max_value = self.node.max_values[self.idx]
            if not min_value is None and value < min_value.value:
                self.input.setStyleSheet("color: red; border: 1px solid black")
            elif not max_value is None and value > max_value.value:
                self.input.setStyleSheet("color: red; border: 1px solid black")
            else:
                self.node.external_inputs[self.idx] = Float(value)
                self.node.compute()
                self.node.new_params.emit()

                self.input.setStyleSheet(f"color: {STYLE["textcolor"]}; border: 1px solid black;")

        except Exception:
            self.input.setStyleSheet("color: red;border: 1px solid black;")

class OptionVis(QWidget):

    def __init__(self, node: Node, idx: int, dtype: type[Option], name: str, is_input: bool):
        super().__init__()
        
        self.node = node
        self.idx = idx
        self.dtype = dtype
        self.name = name
        self.is_input = is_input

        self.init_ui()

        if self.is_input:
            self.input.currentTextChanged.connect(self.set_data)
        else:
            self.node.new_results.connect(self.on_new_results)

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background-color: transparent;")

        label = QLabel(self.name)
        label.setStyleSheet("background-color: transparent;")
        layout.addWidget(label)

        self.input = QComboBox()
        self.input.addItems(list(self.dtype.options))
        self.input.setStyleSheet("border: 1px solid black;")
        self.input.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.input.setStyleSheet(f"""
                QComboBox {{
                    font-size: 11px;
                    border: 1px solid #333;
                }}
                QComboBox QAbstractItemView {{
                    font-size: 11px;  /* font size for the drop-down items */
                    background: {STYLE["bg_default"]};
                }}
        """)

        if not self.is_input:
            self.input.setEnabled(False)

        layout.addWidget(self.input)

    def set_data(self):
        text = self.input.currentText()
        self.node.external_inputs[self.idx] = self.dtype(value=text)
        self.node.compute()
        self.node.new_params.emit()

    @Slot()
    def on_new_results(self):
        data = self.node.results[self.idx]
        if data is None:
            return
        self.input.setCurrentText(data.value)

    @Slot(Option)
    def on_new_input(self, data: Optional[Option]):
        if data is None:
            return
        self.input.setCurrentText(data.value)
