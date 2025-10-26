from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QLabel, QLineEdit
import os

class StyledButton(QPushButton):

    def __init__(self, text: str = "", icon_names: list[str] = [], parent=None):
        super().__init__(text, parent)
        self.icons = []

        HERE = os.path.dirname(__file__)  # path to Lib/
        for icon_name in icon_names:
            icon = QIcon(os.path.join(HERE, "../assets/icons/",
                                      icon_name))
            self.icons.append(icon)
        self.setIcon(self.icons[0])

        self.setObjectName("Primary")

class StyledLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: #f0f0f0;")

class StyledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d3d;
                color: #f0f0f0;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 4px;
            }
        """)
