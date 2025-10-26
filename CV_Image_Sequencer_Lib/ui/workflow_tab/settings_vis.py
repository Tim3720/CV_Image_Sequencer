from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from ...core.workflow_base import Setting


def set_settings_label_style(label: QLabel):
    label.setStyleSheet("""
        QLabel {
            background: transparent;
            color: #f0f0f0;
            border: none;
            font-size: 11px;
        }
    """)

class SettingsVis(QWidget):
    def __init__(self, settings: list[Setting], parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setFixedSize(200, 300)


        for setting in self.settings:
            row = QWidget()
            row.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            row_layout = QHBoxLayout(row)
            label = QLabel(setting.name)
            set_settings_label_style(label)
            row_layout.addWidget(label)

            main_layout.addWidget(row)
        main_layout.addStretch()




