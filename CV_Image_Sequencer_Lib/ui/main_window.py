from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget, QTabWidget
from importlib import reload
import sys

from .tab_widget import TabWidget

from ..utils.source_manager import SourceManager

class CVImageSequencerWidget(QWidget):

    def __init__(self, app: QApplication):
        super().__init__()

        self.source_manager = SourceManager()

        app.aboutToQuit.connect(self.on_quit)

        self.init_ui()
        self.source_manager.load_directory("/Users/vdausmann/data/20241106-1526_SO308_1-5-1_PISCO2_png/selection")

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)

        self.tab_widget = TabWidget(self.source_manager)

        self.main_layout.addWidget(self.tab_widget, 4)

        self.tab_widget.load()

    def on_quit(self):
        self.tab_widget.save()


    def reload_widget(self):
        reload(sys.modules["TabBar"])
        self.main_layout.removeWidget(self.tab_widget)
        self.tab_widget.deleteLater()
        self.tab_widget = TabWidget(self.source_manager)
        self.main_layout.addWidget(self.tab_widget)
        print("✅ Widget reloaded.")
