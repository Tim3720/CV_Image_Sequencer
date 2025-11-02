from typing import Type
from PySide6.QtWidgets import (QCheckBox, QGraphicsItem, QGraphicsProxyWidget, QHBoxLayout, QLineEdit, QWidget, QLabel, QComboBox)

from CV_Image_Sequencer_Lib.utils.type_base import IOType
from ...assets.styles.style import STYLE
from ...core.node_base import DataNode, SourceNode
from ...utils.types import Bool, DictType, Float, Int, Scalar
from PySide6.QtCore import Qt, Signal, Slot

def port_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("font-size: 11px; border: none;")
    return label


class EnumVisInput(QWidget):

    data_changed_signal = Signal()
    
    def __init__(self, node: DataNode, parent=None):
        super().__init__(parent)
        self.node = node

        self.data_type = self.node.data_type

        self.init_ui()


    def init_ui(self):
        if self.data_type is None or not issubclass(self.data_type, DictType): # enum like
            raise ValueError("Wrong type passed to port_dropdown")

        self.setStyleSheet("background-color: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = port_label(self.node.name)

        self.dropdown = QComboBox()
        for option in self.data_type.value_dict.keys():
            self.dropdown.addItem(option, option)

        if self.data_type.value is not None:
            self.dropdown.setCurrentText(self.data_type.value)
        else:
            default = self.data_type.default_value
            if default is not None:
                self.dropdown.setCurrentText(default)

        self.dropdown.setStyleSheet(f"""
                QComboBox {{
                    font-size: 11px;
                    border: 2px solid #333;
                }}
                QComboBox QAbstractItemView {{
                    font-size: 11px;  /* font size for the drop-down items */
                    background: {STYLE["bg_default"]};
                }}
        """)

        self.dropdown.currentTextChanged.connect(self._set_value)
        self.node.data_request_signal.connect(self.on_data_request)

        layout.addWidget(label)
        layout.addWidget(self.dropdown)

    @Slot(str)
    def _set_value(self, value: str):
        # data_type = self.node.output_nodes[0].data_type
        # data = data_type(value=value)
        self.data_changed_signal.emit()
        # self.node.send_data((data, None), False)

    def set_value(self, value: str):
        self.dropdown.setCurrentText(value)

    def get_value(self):
        return self.dropdown.currentText()

    def on_data_request(self):
        if self.node.input_node is None:
            value = self.dropdown.currentText()
            data_type = self.node.output_nodes[0].data_type
            data = data_type(value=value)
            self.node.send_data((data, None), False)



class EnumVisOutput(QWidget):
    
    def __init__(self, port: DataNode | SourceNode, parent=None):
        super().__init__(parent)

        self.port = port

        self.init_ui()

    def init_ui(self):
        if self.port.data_type != DictType: # enum like
            raise ValueError("Wrong type passed to port_dropdown")
        self.setStyleSheet("background-color: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = port_label(self.port.name)

        dropdown = QLabel()
        dropdown.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    border: 2px solid #333;
                }
        """)

        layout.addWidget(label)
        layout.addWidget(dropdown)


class ScalarVisInput(QWidget):
    
    def __init__(self, port: DataNode | SourceNode, parent=None):
        super().__init__(parent)
        self.port = port
        self.current_text = ""
        self.current_data: Scalar | None = None

        self.init_ui()

    def init_ui(self):
        data_type = self.port.data_type
        if not issubclass(data_type, Scalar): # enum like
            raise ValueError("Wrong type passed to port_line_edit")
        self.setStyleSheet("background-color: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = port_label(self.port.name)

        self.edit = QLineEdit()
        self.edit.setFixedWidth(50)

        self.edit.setStyleSheet("""
                QLineEdit {
                    font-size: 11px;
                    border: 2px solid #333;
                }
        """)

        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.edit, alignment=Qt.AlignmentFlag.AlignRight)
        self.edit.textChanged.connect(self.on_edit)

        self.port.data_signal.connect(self.on_computation_trigger)
        self.port.request_data_signal.connect(self.get_data)

        self.current_text = self.edit.text()

    def set_style(self, color: str):
        self.edit.setStyleSheet(f"""
                QLineEdit {{
                    font-size: 11px;
                    color: {color};
                    border: 2px solid #333;
                }}
        """)

    @Slot(IOType)
    def on_computation_trigger(self, data: IOType):
        if not self.edit.hasFocus():
            self.edit.setText(str(data.value))

    def on_edit(self, text: str):
        try:
            data_type = self.port.data_type
            if not issubclass(data_type, Scalar):
                raise ValueError("Wrong type passed to port_line_edit")
            if data_type == Float:
                value = float(text)
            elif data_type == Int:
                value = int(text)
            else:
                raise ValueError("Unknown Scalar type passed to ScalarVisInput.")

            if data_type.max_value and value > data_type.max_value:
                self.edit.setText(self.current_text)
            elif data_type.min_value and value < data_type.min_value:
                self.edit.setText(self.current_text)

            self.port.on_new_data()

            self.current_text = text
            self.set_style(STYLE["textcolor"])
        except:
            self.set_style(STYLE["error"])

    def get_data(self):
        if not issubclass(self.port.data_type, Scalar):
            raise ValueError("Wrong type passed to port_line_edit")
        data = self.port.data_type()
        data.set_value_from_string(self.edit.text())
        self.port.send_data(data)

    def set_value(self, value: str):
        self.edit.setText(value)

    def get_value(self):
        return self.edit.text()


class ScalarVisOutput(QWidget):
    
    def __init__(self, port: DataNode, parent=None):
        super().__init__(parent)
        self.port = port

        self.init_ui()

    def init_ui(self):
        data_type = self.port.data_type
        if not issubclass(data_type, Scalar): # enum like
            raise ValueError("Wrong type passed to port_line_edit")
        self.setStyleSheet("background-color: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = port_label(self.port.name)

        self.edit = QLabel()
        self.edit.setFixedWidth(50)

        self.edit.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    border: 2px solid #333;
                }
        """)

        layout.addWidget(self.edit, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignRight)

        self.port.data_signal.connect(self.update_text)

    def update_text(self, text: IOType):
        self.edit.setText(str(text.value))


class BoolVis(QWidget):
    def __init__(self, port: DataNode, parent=None):
        super().__init__(parent)
        self.port = port

        self.init_ui()

    def init_ui(self):
        if not self.port.data_type == Bool:
            raise ValueError("Wrong type passed to BoolVis")
        self.setStyleSheet("background-color: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = port_label(self.port.name)
        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("border: 2px solid #333;")
        self.checkbox.setFixedSize(15, 15)

        if self.port.is_input:
            layout.addWidget(label)
            layout.addWidget(self.checkbox)
            self.checkbox.checkStateChanged.connect(self._get_value)
        else:
            layout.addWidget(self.checkbox)
            layout.addWidget(label)
            self.checkbox.setEnabled(False)
            self.port.data_signal.connect(self._set_value)

    def _get_value(self):
        if self.port.is_input:
            self.port.send_data(Bool(value=self.checkbox.isChecked()))
    
    def _set_value(self, value: Type):
        self.checkbox.setChecked(value.value)

    def set_value(self, value: bool):
        self.checkbox.setChecked(value)

    def get_value(self):
        return self.checkbox.isChecked()

