from PySide6.QtWidgets import QMainWindow, QWidget, QGridLayout, QTabWidget, QVBoxLayout, QToolBar, QPushButton
from PySide6.QtCore import Qt

from .video_tab import VideoTabWidget
from .frame_tab import FrameTabWidget
from .workflow_widget import WorkflowWidget
from utils.file_handler import FileHandler
from .styled_widgets import StyledButton, StyledLabel

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("CV Image Sequencer")
        self.setGeometry(100, 100, 1200, 800)

        self.file_handler = FileHandler()

        # Create a toolbar for main actions
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # Add "Load File" button to the toolbar
        self.load_file_button = StyledButton("Load File")
        self.toolbar.addWidget(self.load_file_button)
        self.load_file_button.clicked.connect(self.on_load_file_clicked)

        # Main layout widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QGridLayout(central_widget)

        # Left panel for workflows
        self.workflow_widget = WorkflowWidget()
        main_layout.addWidget(self.workflow_widget, 0, 0, 1, 1)

        # Right panel for tabs (video and frames)
        self.tab_widget = QTabWidget()
        self.video_tab = VideoTabWidget()
        self.frame_tab = FrameTabWidget()

        self.tab_widget.addTab(self.video_tab, "Live Video")
        self.tab_widget.addTab(self.frame_tab, "Still Frame")

        main_layout.addWidget(self.tab_widget, 0, 1, 1, 1)
        
        # Set layout column stretch factors for resizing
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 3)
    
    def on_load_file_clicked(self):
        video_path = self.file_handler.open_video_file_dialog()
        if video_path:
            frame, error_msg = self.file_handler.load_video(video_path)
            if frame is not None:
                print(f"Loaded frame from: {video_path}")
                self.frame_tab.display_frame(frame)
            else:
                print(f"Failed to load video: {error_msg}")
