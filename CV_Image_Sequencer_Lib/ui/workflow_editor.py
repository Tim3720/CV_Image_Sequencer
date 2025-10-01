from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget


class WorkflowEditor(QWidget):
    finished_signal = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        label = QLabel("Workflow")
        label.setStyleSheet("font-size: 16px; color: #456; border: none;")
        main_layout.addWidget(label)

        self.settings_area = QScrollArea()
        self.settings_area.setWidgetResizable(True)
        self.settings = QWidget()
        self.settings_layout = QVBoxLayout(self.settings)
        self.settings_layout.addStretch()

        self.settings_area.setWidget(self.settings)
 

        ############################## 
        ## Buttons
        ############################## 
        button_row = QWidget()
        # button_row.setStyleSheet("background: transparent; border: none;")
        button_row_layout = QHBoxLayout(button_row)

        self.finished_button = QPushButton("Finished")
        self.finished_button.clicked.connect(self.finished)
        self.finished_button.setObjectName("Primary")

        button_row_layout.addStretch()
        button_row_layout.addWidget(self.finished_button)

        main_layout.addWidget(self.settings_area, 1)
        main_layout.addStretch()
        main_layout.addWidget(button_row)


    @Slot()
    def finished(self):
        self.finished_signal.emit()

