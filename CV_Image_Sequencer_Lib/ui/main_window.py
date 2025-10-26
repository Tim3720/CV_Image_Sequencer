from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget, QTabWidget

from .tab_widget import TabWidget

from ..utils.source_manager import SourceManager

class CVImageSequencerWidget(QWidget):

    def __init__(self, app: QApplication):
        super().__init__()

        self.source_manager = SourceManager()

        app.aboutToQuit.connect(self.on_quit)

        self.init_ui()
        self.source_manager.load_video("/home/tim/Documents/Arbeit/BloodCellsProject/Data/RT_MitotrackOrange_Hoechst_KH7_01202022.avi")

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        self.tab_widget = TabWidget(self.source_manager)

        main_layout.addWidget(self.tab_widget, 4)

        self.tab_widget.load()

    def on_quit(self):
        self.tab_widget.save()

