from PySide6.QtWidgets import QFileDialog, QInputDialog, QPushButton, QSplitter, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize, Slot
import numpy as np
import cv2 as cv

from CV_Image_Sequencer_Lib.core.node_base import Node


from .workflow_manager import WorkflowManager
from .workflow_widget import WorkflowWidget

from ...utils.types import Image1C, Image3C
from ...utils.type_base import IOType
from ...utils.source_manager import SourceManager, convert_cv_to_qt
from ...assets.styles.style import STYLE

class WorkflowTabWidget(QWidget):
    def __init__(self, source_manager: SourceManager, parent=None):
        super().__init__(parent)

        self.source_manager = source_manager
        self.workflow_manager = WorkflowManager(self.source_manager)

        self.org_img_size = QSize(0, 0)
        self.processed_img_size = QSize(0, 0)

        # self.data_buffer: list[IOType | None] = []

        self.init_ui()

        self.workflow_manager.data_signal.connect(self.show_data)

        self.workflow_manager.test()


    def init_ui(self):
        main_layout = QVBoxLayout(self)


        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter, 1)

        frame_widget = QWidget()
        frame_layout = QHBoxLayout(frame_widget)
        splitter.addWidget(frame_widget)

        ##############################
        # Frames:
        ##############################
        self.frame_label = QLabel("Double click a node to show its in and output")
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_label.setStyleSheet(f"background-color: {STYLE["bg_default"]};")
        self.frame_label.setFixedHeight(500)
        self.org_img_size = self.frame_label.size()
        
        frame_layout.addWidget(self.frame_label, 1)
        frame_layout.addStretch()

        ##############################
        # Workflow:
        ##############################
        self.workflow_widget = WorkflowWidget(self.workflow_manager)
        splitter.addWidget(self.workflow_widget)
        self.workflow_widget.update_frame_signal.connect(self.update_frame)

        button_bar = QWidget()
        button_bar_layout = QHBoxLayout(button_bar)
        button_bar_layout.setContentsMargins(0, 0, 0, 0)

        # create_blackbox_button = QPushButton("Create blackbox")
        # create_blackbox_button.clicked.connect(self.create_blackbox)
        #
        # save_workflow_button = QPushButton("Save workflow")
        # save_workflow_button.clicked.connect(self.save_workflow)
        #
        # load_workflow_button = QPushButton("Load workflow")
        # load_workflow_button.clicked.connectself.load_workflow)

        # button_bar_layout.addWidget(create_blackbox_button)
        # button_bar_layout.addWidget(save_workflow_button)
        # button_bar_layout.addWidget(load_workflow_button)

        main_layout.addStretch()
        main_layout.addWidget(button_bar)

    def show_data(self, data_package: tuple[list[IOType], Node]):
        data, _ = data_package
        frames: list[np.ndarray] = []
        color = False
        for elem in data:
            if isinstance(elem, Image1C) and not elem.value is None:
                frames.append(elem.value)
            elif isinstance(elem, Image3C) and not elem.value is None:
                frames.append(elem.value)
                color = True

        if color:
            for frame in frames:
                if len(frame.shape) == 2 or frame.shape[2] == 1:
                    frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        if frames:
            frame = np.concatenate(frames, axis=0)
            self.update_frame(frame)
        else:
            self.update_frame(None)

    def update_frame(self, frame: np.ndarray | None):
        if frame is None:
            self.frame_label.setPixmap(QPixmap())
            self.frame_label.setText("Input not connected")
            return

        qimg = convert_cv_to_qt(frame)
        pixmap = QPixmap.fromImage(qimg)
        pixmap_scaled = pixmap.scaled(self.org_img_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.frame_label.setPixmap(pixmap_scaled)

    def load_state(self, d: dict):
        ...

    def save_state(self) -> dict:
        print(self.workflow_manager.graph_manager._uuid_to_nodes)
        print(self.workflow_manager.graph_manager._node_connections)
        return {}


