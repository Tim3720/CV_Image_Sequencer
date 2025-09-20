from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QSizePolicy, QWidget, QGridLayout, QTabWidget, QVBoxLayout, QToolBar, QPushButton
from PySide6.QtCore import Qt, Slot, QTimer

from .video_tab import VideoPlayerTab
from .frame_tab import FrameTabWidget
from .workflow_widget import WorkflowWidget
from utils.video_handler import VideoManager

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.video_manager = VideoManager()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("CV Image Sequencer")
        # self.setGeometry(320, 140, 1280, 800)
        self.setGeometry(0, 0, 1920, 1080)
        # self.setFixedSize(1280, 720)

        # Main layout widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # # Left panel for workflows
        # self.workflow_widget = WorkflowWidget()
        # main_layout.addWidget(self.workflow_widget, 1)

        # Right panel for tabs (video and frames)
        self.tab_widget = QTabWidget()
        self.video_tab = VideoPlayerTab(self.video_manager)
        self.frame_tab = FrameTabWidget(self.video_manager)
        self.tab_widget.addTab(self.video_tab, "Live Video")
        self.tab_widget.addTab(self.frame_tab, "Still Frame")

        main_layout.addWidget(self.tab_widget, 4)

    # @Slot(bool)
    # def play_video(self, play: bool):
    #     print(play)
    #     if play:
    #         self.video_timer.setInterval(round(1000 / 30))
    #         self.video_timer.start()
    #         self.video_timer.timeout.connect(self.get_frame)
    #     else:
    #         self.video_timer.timeout.disconnect(self.get_frame)
    #         self.video_timer.stop()
    #
