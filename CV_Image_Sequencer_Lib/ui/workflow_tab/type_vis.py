from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QHBoxLayout, QLineEdit, QSizePolicy, QWidget
import numpy as np
import cv2 as cv

from ...assets.styles.style import STYLE
from ...core.types import ColorImage, GrayScaleImage, IOType, Int
from ...utils.source_manager import convert_cv_to_qt

from ...core.nodes import InputSocket, Socket



class TypeVis(QWidget):

    def __init__(self, socket: Socket):
        super().__init__()
        self.socket: Socket = socket

        self.init_ui()


    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if self.socket.dtype == ColorImage or self.socket.dtype == GrayScaleImage:
            widget = ImageVis(self.socket)
        elif self.socket.dtype == Int:
            widget = IntVis(self.socket)
        else:
            widget = QLabel(self.socket.name)
        
        layout.addWidget(widget)



class ImageVis(QWidget):

    def __init__(self, socket: Socket):
        super().__init__()
        
        self.socket = socket
        self.socket.data_received.connect(self.new_img)
        self.img_size = 30
        random_img = np.random.randint(0, 255, (self.img_size, self.img_size), np.uint8)
        self.image = convert_cv_to_qt(random_img)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self.socket.name)

        self.image_label = QLabel()
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setFixedSize(self.img_size, self.img_size)
        self.image_label.setPixmap(QPixmap(self.image))


        layout.addWidget(label)
        layout.addWidget(self.image_label)

    @Slot()
    def new_img(self, data):
        if data is None:
            print(self.socket)
            return
        self.image = convert_cv_to_qt(cv.resize(data.value, (self.img_size, self.img_size)))
        self.image_label.setPixmap(QPixmap(self.image))


class IntVis(QWidget):

    def __init__(self, socket: Socket):
        super().__init__()
        
        self.socket = socket

        self.init_ui()

        self.socket.data_received.connect(self.set_data)
        self.input.textChanged.connect(self._set_data)

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self.socket.name)
        layout.addWidget(label)

        self.input = QLineEdit()
        self.input.setFixedSize(40, 20)
        self.input.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        if isinstance(self.socket, InputSocket) and not self.socket._manual_value is None:
            self.input.setText(str(self.socket._manual_value))

        layout.addWidget(self.input)

    @Slot(IOType)
    def set_data(self, data: Optional[IOType]):
        if data is None:
            print(self.socket)
            return
        self.input.setText(str(data.value))

    @Slot()
    def _set_data(self):
        text = self.input.text()
        try: 
            value = int(text)
            if isinstance(self.socket, InputSocket):
                if self.socket.value_ok(Int(value=value)):
                    self.socket.set_manual_value(Int(value))
                    self.input.setStyleSheet(f"color: {STYLE["textcolor"]};")
                else:
                    self.input.setStyleSheet("color: red;")
        except Exception as e:
            print(e)
            self.input.setStyleSheet("color: red;")

