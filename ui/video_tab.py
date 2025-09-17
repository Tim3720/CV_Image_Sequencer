from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from .styled_widgets import StyledButton

class VideoTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        label = QLabel("This tab will display the live video stream.")
        layout.addWidget(label)

        b = StyledButton()
        layout.addWidget(b)
