import cv2
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt

class FrameTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QHBoxLayout(self)
        self.original_frame_label = QLabel("Original Frame")
        self.original_frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_frame_label.setStyleSheet("border: 1px solid #444444; background-color: #1a1a1a;")
        
        self.processed_frame_label = QLabel("Processed Subimage")
        self.processed_frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.processed_frame_label.setStyleSheet("border: 1px solid #444444; background-color: #1a1a1a;")
        
        main_layout.addWidget(self.original_frame_label, 1)
        main_layout.addWidget(self.processed_frame_label, 1)

    def display_frame(self, frame):
        """
        Converts an OpenCV frame (NumPy array) and displays it.
        """
        if frame is not None:
            # Convert the frame to RGB format
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            # Convert to QImage and QPixmap
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)

            # Scale the pixmap to fit the label, while maintaining aspect ratio
            pixmap_scaled = pixmap.scaled(self.original_frame_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Set the pixmap on the original frame label
            self.original_frame_label.setPixmap(pixmap_scaled)
