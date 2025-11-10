from typing import Optional
from PySide6.QtWidgets import QFileDialog, QInputDialog, QPushButton, QSplitter, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize, Slot
import numpy as np
import cv2 as cv
import json

from CV_Image_Sequencer_Lib.core.types import ColorImage, GrayScaleImage


from ...core.nodes import Graph, Node
from ...core.custom_nodes import ABSDiffNode, SourceNode, ThresholdNode
from .graph_vis import GraphVis

from ...core.types import IOType, Serializable
from ...utils.source_manager import SourceManager, convert_cv_to_qt
from ...assets.styles.style import STYLE

class WorkflowTabWidget(QWidget):
    def __init__(self, source_manager: SourceManager, parent=None):
        super().__init__(parent)

        self.source_manager = source_manager

        self.graph_vis = GraphVis()

        self.init_ui()
        self.test()

        self.graph_vis.new_results.connect(self.on_new_results)
        self.graph_vis.new_inputs.connect(self.on_new_inputs)
        self.graph_vis.new_node_viewing.connect(self.on_new_node)


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
        self.input_frame_label = QLabel("Double click a node to show its in and output")
        self.input_frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_frame_label.setStyleSheet(f"background-color: {STYLE["bg_default"]};")
        self.input_frame_label.setFixedHeight(500)
        self.input_frame_label.setFixedWidth(920)

        self.output_frame_label = QLabel("Double click a node to show its in and output")
        self.output_frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.output_frame_label.setStyleSheet(f"background-color: {STYLE["bg_default"]};")
        self.output_frame_label.setFixedHeight(500)
        self.output_frame_label.setFixedWidth(920)

        self.org_img_size = (920, 500)
        
        frame_layout.addWidget(self.input_frame_label)
        frame_layout.addStretch()
        frame_layout.addWidget(self.output_frame_label)

        ##############################
        # Workflow:
        ##############################
        splitter.addWidget(self.graph_vis)

        button_bar = QWidget()
        button_bar_layout = QHBoxLayout(button_bar)
        button_bar_layout.setContentsMargins(0, 0, 0, 0)

        save_button = QPushButton("Save workflow")
        save_button.clicked.connect(self.save_workflow)
        button_bar_layout.addWidget(save_button)

        load_button = QPushButton("Load workflow")
        load_button.clicked.connect(self.load_workflow)
        button_bar_layout.addWidget(load_button)

        main_layout.addStretch()
        main_layout.addWidget(button_bar)

    def test(self):
        self.graph_vis.add_node(SourceNode, x=0, y=100, n_frames=3)
        self.graph_vis.add_node(SourceNode, x=0, y=300)
        self.graph_vis.add_node(ABSDiffNode, x=200, y=200)
        self.graph_vis.add_node(ThresholdNode, x=400, y=200)

    @Slot(Node)
    def on_new_results(self, node: Node):
        images = []
        color = False
        for d in node.results:
            if isinstance(d, GrayScaleImage) and not d.value is None:
                images.append(d.value)
            elif isinstance(d, ColorImage) and not d.value is None:
                images.append(d.value)
                color = True

        if not images:
            return

        border = np.ones((images[0].shape[0], 10), dtype=np.uint8) * 150
        frames = []
        for img in images:
            frames.append(img)
            frames.append(border)
        frames.pop()

        frame = np.concatenate(frames, axis=1)
        if frame.shape[1] > frame.shape[0]:
            factor = self.org_img_size[0] / frame.shape[1]
        else:
            factor = self.org_img_size[1] / frame.shape[0]

        frame = cv.resize(frame, None, fx=factor, fy=factor)

        qimg = convert_cv_to_qt(frame)
        pixmap = QPixmap.fromImage(qimg)
        self.output_frame_label.setPixmap(pixmap)

    @Slot(object)
    def on_new_inputs(self, inputs: list[Optional[IOType]]):
        images = []
        color = False
        for d in inputs:
            if isinstance(d, GrayScaleImage) and not d.value is None:
                images.append(d.value)
            elif isinstance(d, ColorImage) and not d.value is None:
                images.append(d.value)
                color = True

        if not images:
            return

        border = np.ones((images[0].shape[0], 10), dtype=np.uint8) * 150
        frames = []
        for img in images:
            frames.append(img)
            frames.append(border)
        frames.pop()

        frame = np.concatenate(frames, axis=1)
        if frame.shape[1] >= frame.shape[0]:
            factor = self.org_img_size[1] / frame.shape[0]
        else:
            factor = self.org_img_size[0] / frame.shape[1]
        frame = cv.resize(frame, None, fx=factor, fy=factor)

        qimg = convert_cv_to_qt(frame)
        pixmap = QPixmap.fromImage(qimg)
        self.input_frame_label.setPixmap(pixmap)

    @Slot()
    def on_new_node(self):
        self.input_frame_label.setPixmap(QPixmap())
        self.output_frame_label.setPixmap(QPixmap())

    def save_workflow(self):
        file, _ = QFileDialog.getSaveFileName(None, "Workflow file", "/home/tim/Documents/OtherProjects/CV_Image_Sequencer/Workflows/", "*.json")
        if not file.endswith(".json"):
            file += ".json"
        state = self.graph_vis.graph.to_dict()
        with open(file, "w") as f:
            json.dump(state, f, indent=2)


    def load_workflow(self):
        file, _ = QFileDialog.getOpenFileName(None, "Workflow file", "/home/tim/Documents/OtherProjects/CV_Image_Sequencer/Workflows/", "*.json")
        with open(file, "r") as f:
            state = json.load(f)

    def load_state(self, state: dict):
        nodes = state["nodes"]
        connections = state["connections"]

        # remove all current notes
        for node_vis in list(self.graph_vis.node_visualizations.values()):
            node_vis.delete.emit()

