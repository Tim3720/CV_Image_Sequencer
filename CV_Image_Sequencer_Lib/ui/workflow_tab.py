from PySide6.QtWidgets import QGraphicsView, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QSize
import numpy as np

from .workflow_widget import WorkflowScene, WorkflowManger
from ..utils.video_manager import VideoManager, convert_cv_to_qt

class WorkflowTabWidget(QWidget):
    def __init__(self, video_manager: VideoManager, parent=None):
        super().__init__(parent)

        self.video_manager = video_manager
        self.org_img_size = QSize(0, 0)
        self.processed_img_size = QSize(0, 0)

        self.init_ui()

        # self.video_manager.frame_ready.connect(self.update_source_frame)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        frame_widget = QWidget()
        frame_layout = QHBoxLayout(frame_widget)
        main_layout.addWidget(frame_widget, 1)

        ##############################
        # Frames:
        ##############################
        self.frame_label = QLabel("Double click a node to show its in and output")
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_label.setStyleSheet("border: 1px solid #444444; background-color: #1a1a1a;")
        self.frame_label.setFixedHeight(500)
        self.org_img_size = self.frame_label.size()
        
        frame_layout.addWidget(self.frame_label, 1)
        frame_layout.addStretch()

        ##############################
        # Workflow:
        ##############################
        self.workflow_widget = WorkflowManger(self.video_manager)
        main_layout.addWidget(self.workflow_widget, 1)

        # self.workflow_widget.update_source_frame_signal.connect(self.update_source_frame)
        # self.workflow_widget.update_processed_frame_signal.connect(self.update_processed_frame)
        self.workflow_widget.update_frame_signal.connect(self.update_frame)

    def update_frame(self, frame: np.ndarray | None):
        if frame is None:
            self.frame_label.setPixmap(QPixmap())
            self.frame_label.setText("Input not connected")
            return

        qimg = convert_cv_to_qt(frame)
        pixmap = QPixmap.fromImage(qimg)
        pixmap_scaled = pixmap.scaled(self.org_img_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.frame_label.setPixmap(pixmap_scaled)

