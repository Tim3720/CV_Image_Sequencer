from PySide6.QtGui import QIcon, QPixmap
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
    def __init__(self, icon_name: str, invert_icon: bool, text: str = "", parent=None):
        super().__init__(text, parent)

        HERE = os.path.dirname(__file__)  # path to Lib/
        icon = QPixmap(os.path.join(HERE, "../assets/icons/", icon_name))
        self.setStyleSheet("background-color: transparent;")

        if invert_icon: 
            image = icon.toImage()
            image.invertPixels()  # inverts RGB values in place
            icon = QPixmap.fromImage(image)

        self.setScaledContents(True)
        self.setPixmap(icon)

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
