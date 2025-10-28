from PySide6.QtWidgets import QFileDialog, QPushButton, QSplitter, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize
from cv2 import DrawMatchesFlags_DRAW_OVER_OUTIMG
import numpy as np
import json

from CV_Image_Sequencer_Lib.core import workflow_base
from CV_Image_Sequencer_Lib.core.node_base import InPut
from CV_Image_Sequencer_Lib.core.nodes import GrayScaleSourceNode, SourceNode

from ...utils.type_base import Serializable
from ...assets.styles.style import STYLE

from .workflow_widget import WorkflowWidget
from ...utils.source_manager import SourceManager, convert_cv_to_qt

class WorkflowTabWidget(QWidget):
    def __init__(self, source_manager: SourceManager, parent=None):
        super().__init__(parent)

        self.source_manager = source_manager
        self.org_img_size = QSize(0, 0)
        self.processed_img_size = QSize(0, 0)

        self.init_ui()

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
        self.workflow_widget = WorkflowWidget(self.source_manager)
        splitter.addWidget(self.workflow_widget)
        self.workflow_widget.update_frame_signal.connect(self.update_frame)

        button_bar = QWidget()
        button_bar_layout = QHBoxLayout(button_bar)
        button_bar_layout.setContentsMargins(0, 0, 0, 0)

        save_workflow_button = QPushButton("Save workflow")
        save_workflow_button.clicked.connect(self.save_workflow)

        load_workflow_button = QPushButton("Load workflow")
        load_workflow_button.clicked.connect(self.load_workflow)

        button_bar_layout.addWidget(save_workflow_button)
        button_bar_layout.addWidget(load_workflow_button)

        main_layout.addStretch()
        main_layout.addWidget(button_bar)

    def update_frame(self, frame: np.ndarray | None):
        if frame is None:
            self.frame_label.setPixmap(QPixmap())
            self.frame_label.setText("Input not connected")
            return

        qimg = convert_cv_to_qt(frame)
        pixmap = QPixmap.fromImage(qimg)
        pixmap_scaled = pixmap.scaled(self.org_img_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.frame_label.setPixmap(pixmap_scaled)

    def save_state(self) -> dict:
        nodes = self.workflow_widget.get_current_state()
        state = {}
        state["nodes"] = []
        for node in nodes:
            d = {}
            d["type"] = node.node.__class__.__name__
            d["type_args"] = {}
            if isinstance(node.node, SourceNode) or isinstance(node.node, GrayScaleSourceNode):
                d["type_args"]["n_frames"] = node.node.n_frames

            pos = node.pos()
            d["x"] = pos.x()
            d["y"] = pos.y()
            d["connections"] = []
            d["values"] = []
            d["id"] = node.node.id
            for i in node.node.inputs:
                if i.connected_output is not None:
                    d["connections"].append({"input": i.index, "output": {"node": i.connected_output.parent_id,
                                                                      "index": i.connected_output.index} })
            for i in node.input_ports:
                if i.data_widget is None:
                    d["values"].append(None)
                else:
                    d["values"].append(getattr(i.data_widget, "get_value")())
            state["nodes"].append(d)
        return state


    def load_state(self, d: dict):
        for node in d["nodes"]:
            self.workflow_widget.add_node(Serializable._registry[node["type"]], id=node["id"], **node["type_args"])
            self.workflow_widget.node_visulisations[-1].setPos(node["x"], node["y"])

        nodes = self.workflow_widget.node_visulisations
        nodes_id = {node.node.id: node for node in nodes}
        for i, node in enumerate(d["nodes"]):
            connections = node["connections"]
            for connection in connections:
                self.workflow_widget.scene.connect_nodes(nodes[i].input_ports[connection["input"]],
                                                      nodes_id[connection["output"]["node"]].output_ports[connection["output"]["index"]])

        for node in d["nodes"]:
            node_vis = nodes_id[node["id"]]
            for idx, i in enumerate(node_vis.input_ports):
                if not i.data_widget is None:
                    getattr(i.data_widget, "set_value")(str(node["values"][idx]))

        for node_vis in self.workflow_widget.node_visulisations:
            self.workflow_widget.scene.itemMoved(node_vis)

    def save_workflow(self):
        workflow = self.save_state()
        file_name = QFileDialog.getSaveFileName(None, "Save workflow", "Workflows", filter="JSON Files (*.json);;All Files (*)")[0]
        if not file_name:
            return

        if not file_name.endswith(".json"):
            file_name += ".json"
        with open(file_name, "w") as f:
            json.dump(workflow, f, indent=2)


    def load_workflow(self):
        file_name = QFileDialog.getOpenFileName(None, "Load workflow", "Workflows", filter="JSON Files (*.json);;All Files (*)")[0]
        if not file_name:
            return
        try:
            with open(file_name, "r") as f:
                workflow = json.load(f)
            self.load_state(workflow)
        except:
            pass
