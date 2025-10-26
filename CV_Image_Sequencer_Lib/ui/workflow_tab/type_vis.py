from PySide6.QtWidgets import (QCheckBox, QGraphicsItem, QGraphicsProxyWidget, QHBoxLayout, QLineEdit, QWidget, QLabel, QComboBox)
from ...assets.styles.style import STYLE
from ...core.nodes import OutPut, InPut
from ...utils.types import Bool, DictType, Float, Int, Scalar
from PySide6.QtCore import Qt

def port_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("font-size: 11px; border: none;")
    return label


class EnumVisInput(QWidget):
    
    def __init__(self, port: InPut, parent=None):
        super().__init__(parent)

        self.port = port

        self.init_ui()

    def init_ui(self):
        data_type = type(self.port.data)
        if not issubclass(data_type, DictType): # enum like
            raise ValueError("Wrong type passed to port_dropdown")
        self.setStyleSheet("background-color: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = port_label(self.port.label)

        self.dropdown = QComboBox()
        for option in data_type.value_dict.keys():
            self.dropdown.addItem(option, option)

        if data_type.value is not None:
            self.dropdown.setCurrentText(data_type.value)
        else:
            default = data_type.default_value
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

        self.dropdown.currentTextChanged.connect(lambda x:
                                            self.port.data_update(self.port.data.set_value(x)))

        layout.addWidget(label)
        layout.addWidget(self.dropdown)

    def set_value(self, value: str):
        self.dropdown.setCurrentText(value)

    def get_value(self):
        return self.dropdown.currentText()


class EnumVisOutput(QWidget):
    
    def __init__(self, port: OutPut, parent=None):
        super().__init__(parent)

        self.port = port

        self.init_ui()

    def init_ui(self):
        if not isinstance(self.port.data, DictType): # enum like
            raise ValueError("Wrong type passed to port_dropdown")
        self.setStyleSheet("background-color: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = port_label(self.port.label)

        dropdown = QLabel(self.port.data.value)

        dropdown.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    border: 2px solid #333;
                }
        """)


        layout.addWidget(label)
        layout.addWidget(dropdown)


class ScalarVisInput(QWidget):
    
    def __init__(self, port: InPut, parent=None):
        super().__init__(parent)
        self.port = port
        self.current_text = ""

        self.init_ui()

    def init_ui(self):
        data_type = type(self.port.data)
        if not issubclass(data_type, Scalar): # enum like
            raise ValueError("Wrong type passed to port_line_edit")
        self.setStyleSheet("background-color: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = port_label(self.port.label)

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
        self.port.computation_trigger_signal.connect(self.on_computation_trigger)
        if self.port.data.value is not None:
            self.edit.setText(str(self.port.data.value))
        self.current_text = self.edit.text()

    def set_style(self, color: str):
        self.edit.setStyleSheet(f"""
                QLineEdit {{
                    font-size: 11px;
                    color: {color};
                    border: 2px solid #333;
                }}
        """)

    def on_computation_trigger(self):
        if not self.edit.hasFocus():
            self.edit.setText(str(self.port.data.value))

    def on_edit(self, text: str):
        try:
            if type(self.port.data) == Float:
                value = float(text)
            elif type(self.port.data) == Int:
                value = int(text)
            else:
                raise ValueError("Unknown Scalar type passed to ScalarVisInput.")
            if self.port.data.max_value and value > self.port.data.max_value:
                self.edit.setText(self.current_text)
            elif self.port.data.min_value and value < self.port.data.min_value:
                self.edit.setText(self.current_text)
            self.port.data_update(self.port.data.set_value_from_string(self.edit.text()))
            self.current_text = text
            self.set_style(STYLE["textcolor"])
        except:
            self.set_style(STYLE["error"])

    def set_value(self, value: str):
        self.edit.setText(value)

    def get_value(self):
        return self.edit.text()


class ScalarVisOutput(QWidget):
    
    def __init__(self, port: OutPut, parent=None):
        super().__init__(parent)
        self.port = port

        self.init_ui()

    def init_ui(self):
        data_type = type(self.port.data)
        if not issubclass(data_type, Scalar): # enum like
            raise ValueError("Wrong type passed to port_line_edit")
        self.setStyleSheet("background-color: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = port_label(self.port.label)

        edit = QLabel()
        edit.setFixedWidth(50)

        edit.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    border: 2px solid #333;
                }
        """)

        layout.addWidget(edit, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignRight)
        self.port.computation_finished_signal.connect(lambda x: edit.setText(str(x.value)))


class BoolVis(QWidget):
    def __init__(self, port: InPut | OutPut, parent=None):
        super().__init__(parent)
        self.port = port

        self.init_ui()

    def init_ui(self):
        if not isinstance(self.port.data, Bool):
            raise ValueError("Wrong type passed to BoolVis")
        self.setStyleSheet("background-color: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = port_label(self.port.label)
        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("border: 2px solid #333;")
        self.checkbox.setFixedSize(15, 15)

        if isinstance(self.port, InPut):
            layout.addWidget(label)
            layout.addWidget(self.checkbox)
            self.checkbox.checkStateChanged.connect(lambda : self.port.data_update(Bool(value=self.checkbox.isChecked())))
        else:
            layout.addWidget(self.checkbox)
            layout.addWidget(label)
            self.checkbox.setEnabled(False)
            self.port.computation_finished_signal.connect(lambda x: self.checkbox.setChecked(x.value))
    
    def set_value(self, value: bool):
        self.checkbox.setChecked(value)

    def get_value(self):
        return self.checkbox.isChecked()



def create_proxy(parent: QGraphicsItem, widget: QWidget, x: float, y: float, w: float, h: float):
    proxy = QGraphicsProxyWidget(parent)
    proxy.setWidget(widget)
    proxy.setGeometry(x, y, w, h)

def create_proxy_no_position(parent: QGraphicsItem, widget: QWidget):
    proxy = QGraphicsProxyWidget(parent)
    proxy.setWidget(widget)
    return proxy

