from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser, QHBoxLayout, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sys

class HelpDialog(QDialog):
    def __init__(self, help_title: str, help_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(help_title)
        self.setMinimumSize(480, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title_label = QLabel(help_title)
        title_font = QFont("Inter", 13, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #222;")
        layout.addWidget(title_label)

        # Text area (Markdown)
        text_area = QTextBrowser()
        text_area.setOpenExternalLinks(True)
        # Widget-level styling (controls background, border, padding)
        text_area.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #d8d8d8;
                border-radius: 8px;
                padding: 10px;
                color: #222222;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
            }
            /* Make code spans and blocks use monospace inside the document */
            QTextBrowser QWidget { /* fallback, no-op but keeps QSS well-formed */ }
        """)
        # Set the markdown text directly (no external libs required)
        # Make sure the markdown string has blank lines between blocks
        text_area.setMarkdown(help_text)
        layout.addWidget(text_area, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setFixedWidth(88)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #2f6fa6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #3b7fb6; }
            QPushButton:pressed { background-color: #245f8f; }
        """)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

