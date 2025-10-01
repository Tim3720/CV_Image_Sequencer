from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QLabel, QLineEdit


class StyledButton(QPushButton):

    def __init__(self, text: str = "", icon_names: list[str] = [], parent=None):
        super().__init__(text, parent)
        self.icons = []
        for icon_name in icon_names:
            icon = QIcon("CV_Image_Sequencer_Lib/assets/icons/" + icon_name)
            self.icons.append(icon)
        self.setIcon(self.icons[0])

        self.setObjectName("Primary")
        # self.setStyleSheet("""
        #     QPushButton {
        #         background-color: #3d3d3d;
        #         color: #f0f0f0;
        #         border: 1px solid #555555;
        #         padding: 8px 16px;
        #         border-radius: 4px;
        #     }
        #     QPushButton:hover {
        #         background-color: #555555;
        #     }
        #     QPushButton:pressed {
        #         background-color: #2b2b2b;
        #     }
        # """)

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
