from PySide6.QtWidgets import QHBoxLayout, QInputDialog, QWidget, QLabel, QVBoxLayout, QFileDialog
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QSize, Qt, Signal, Slot
import numpy as np

from CV_Image_Sequencer_Lib.utils.types import Image3C

from ...assets.styles.style import STYLE
from ...utils.source_manager import SourceManager, convert_cv_to_qt
from ..styled_widgets import StyledButton

class SourcePlayerTab(QWidget):

    play_video_signal = Signal(bool)

    def __init__(self, source_manager: SourceManager, parent=None):
        super().__init__(parent)

        self.source_manager = source_manager

        self.playing_video: bool = False
        self.current_frame = None
        self.img_size = QSize(0, 0)

        self.init_ui()

        self.source_manager.frame_ready.connect(self.update_frame)

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.frame_number_label = QLabel("Frame: ")
        layout.addWidget(self.frame_number_label, 1)

        self.video_frame_label = QLabel("Source")
        self.video_frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_frame_label.setStyleSheet(f"background-color: {STYLE["bg_default"]};")
        layout.addWidget(self.video_frame_label, 10)
        self.img_size = self.video_frame_label.size()

        button_row = QWidget()
        button_row_layout = QHBoxLayout(button_row)
        button_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_row_layout.setContentsMargins(0, 0, 0, 0)
        button_row_layout.setSpacing(10)


        self.open_file = StyledButton("", ["open_file"])
        self.open_file.setFixedSize(30, 30)
        self.open_file.setIconSize(QSize(28, 28))
        self.open_file.clicked.connect(self.open_source_dialog)

        self.skip_previous_button = StyledButton("", ["skip_previous"])
        self.skip_previous_button.setFixedSize(30, 30)
        self.skip_previous_button.setIconSize(QSize(28, 28))
        self.skip_previous_button.clicked.connect(lambda: self.source_manager.get_frame(-5))

        self.previous_frame_button = StyledButton("", ["previous"])
        self.previous_frame_button.setFixedSize(30, 30)
        self.previous_frame_button.setIconSize(QSize(28, 28))
        self.previous_frame_button.clicked.connect(lambda: self.source_manager.get_frame(-1))

        self.start_stop_button = StyledButton("", ["play_circle", "pause_circle"])
        self.start_stop_button.setFixedSize(30, 30)
        self.start_stop_button.setIconSize(QSize(28, 28))
        self.start_stop_button.clicked.connect(self.play_video)

        self.next_frame_button = StyledButton("", ["next"])
        self.next_frame_button.setFixedSize(30, 30)
        self.next_frame_button.setIconSize(QSize(28, 28))
        self.next_frame_button.clicked.connect(lambda: self.source_manager.get_frame(1))

        self.skip_next_button = StyledButton("", ["skip_next"])
        self.skip_next_button.setFixedSize(30, 30)
        self.skip_next_button.setIconSize(QSize(28, 28))
        self.skip_next_button.clicked.connect(lambda: self.source_manager.get_frame(5))

        button_row_layout.addWidget(self.open_file, alignment=Qt.AlignmentFlag.AlignLeft)
        button_row_layout.addWidget(self.skip_previous_button)
        button_row_layout.addWidget(self.previous_frame_button)
        button_row_layout.addWidget(self.start_stop_button)
        button_row_layout.addWidget(self.next_frame_button)
        button_row_layout.addWidget(self.skip_next_button)

        layout.addWidget(button_row, 1)

    def play_video(self):
        if self.playing_video:
            self.start_stop_button.setIcon(self.start_stop_button.icons[0])
            self.source_manager.stop()
        else:
            self.start_stop_button.setIcon(self.start_stop_button.icons[1])
            self.source_manager.start(1000 // 60)

        self.playing_video = not self.playing_video
        self.skip_next_button.setDisabled(self.playing_video)
        self.skip_previous_button.setDisabled(self.playing_video)
        self.next_frame_button.setDisabled(self.playing_video)
        self.previous_frame_button.setDisabled(self.playing_video)


    @Slot(Image3C)
    def update_frame(self, frame: Image3C):
        # convert from cv to qt:
        if frame.value is None:
            return
        qimg = convert_cv_to_qt(frame.value)
        pixmap = QPixmap.fromImage(qimg)
        pixmap_scaled = pixmap.scaled(self.img_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.video_frame_label.setPixmap(pixmap_scaled)

        self.frame_number_label.setText(f"Frame: {self.source_manager.current_frame_idx}")

    def resizeEvent(self, event) -> None:
        ret = super().resizeEvent(event)
        self.img_size = self.video_frame_label.size()
        return ret

    def open_source_dialog(self):
        mode, ok = QInputDialog.getItem(None, "Select Mode", "Source type:", ["Video", "Image Directory"], 0, False)
        if not ok:
            return

        if mode == "Video":
            file_paths = QFileDialog.getOpenFileName(caption="Select Video File",
                                                 dir="/home/tim/Documents/Arbeit/BloodCellsProject/Data",
                                                 filter="Video Files (*.mp4 *.avi *.mov);;All Files (*)")
            if file_paths:
                self.source_manager.load_video(file_paths[0])
        else:
            path = QFileDialog.getExistingDirectory(None, "Select Image Directory",
                                                    dir="/home/tim/Documents/Arbeit/HDF5Test/SO298_298-10-1_PISCO2_20230422-2334_Results/")
            self.source_manager.load_directory(path)
