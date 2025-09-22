from PySide6.QtWidgets import QGraphicsView, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QSize

from ui.workflow_widget import WorkflowScene, WorkflowWidget
from utils.video_handler import VideoManager, convert_cv_to_qt

class FrameTabWidget(QWidget):
    def __init__(self, video_manager: VideoManager, parent=None):
        super().__init__(parent)

        self.video_manager = video_manager
        self.org_img_size = QSize(0, 0)
        self.processed_img_size = QSize(0, 0)

        self.init_ui()

        self.video_manager.frame_ready.connect(self.update_frame)

    def init_ui(self):
        main_layout = QVBoxLayout(self)


        frame_widget = QWidget()
        frame_layout = QHBoxLayout(frame_widget)
        main_layout.addWidget(frame_widget, 1)

        ##############################
        # Frames:
        ##############################
        self.original_frame_label = QLabel("Original Frame")
        self.original_frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_frame_label.setStyleSheet("border: 1px solid #444444; background-color: #1a1a1a;")
        self.org_img_size = self.original_frame_label.size()
        
        self.processed_frame_label = QLabel("Processed Subimage")
        self.processed_frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.processed_frame_label.setStyleSheet("border: 1px solid #444444; background-color: #1a1a1a;")
        self.processed_img_size = self.processed_frame_label.size()
        
        frame_layout.addWidget(self.original_frame_label, 1)
        frame_layout.addWidget(self.processed_frame_label, 1)

        ##############################
        # Workflow:
        ##############################
        workflow_widget = WorkflowWidget(self.video_manager)
        main_layout.addWidget(workflow_widget, 1)

    def update_frame(self, frame):
        qimg = convert_cv_to_qt(frame)
        pixmap = QPixmap.fromImage(qimg)
        pixmap_scaled = pixmap.scaled(self.org_img_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.original_frame_label.setPixmap(pixmap_scaled)
