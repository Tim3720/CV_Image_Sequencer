from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class WorkflowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        label = QLabel("This panel will contain the image processing workflows.")
        layout.addWidget(label)
