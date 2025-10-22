from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QWidget, QTabWidget

from .tab_widget import TabWidget

from ..utils.video_manager import VideoManager

class CVImageSequencerWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.video_manager = VideoManager()

        self.init_ui()
        self.video_manager.load_video("/home/tim/Documents/Arbeit/BloodCellsProject/Data/RT_MitotrackOrange_Hoechst_KH7_01202022.avi")

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        self.tab_widget = TabWidget(self.video_manager)

        main_layout.addWidget(self.tab_widget, 4)


