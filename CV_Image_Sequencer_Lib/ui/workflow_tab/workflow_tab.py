from PySide6.QtWidgets import QSplitter, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize
import numpy as np

from CV_Image_Sequencer_Lib.utils.type_base import Serializable
from CV_Image_Sequencer_Lib.assets.styles.style import STYLE

from .workflow_widget import WorkflowWidget
from CV_Image_Sequencer_Lib.utils.source_manager import SourceManager, convert_cv_to_qt

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
        self.workflow_manager = WorkflowWidget(self.source_manager)
        splitter.addWidget(self.workflow_manager)
        self.workflow_manager.update_frame_signal.connect(self.update_frame)

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
        nodes = self.workflow_manager.get_current_state()
        state = {}
        state["nodes"] = []
        for node in nodes:
            d = {}
            d["type"] = node.node.__class__.__name__
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
                    d["values"].append(i.data_widget.get_value())
            state["nodes"].append(d)
        return state


    def load_state(self, d: dict):
        for node in d["nodes"]:
            self.workflow_manager.add_node(Serializable._registry[node["type"]], id=node["id"])
            self.workflow_manager.node_visulisations[-1].setPos(node["x"], node["y"])

        nodes = self.workflow_manager.node_visulisations
        nodes_id = {node.node.id: node for node in nodes}
        for i, node in enumerate(d["nodes"]):
            connections = node["connections"]
            for connection in connections:
                self.workflow_manager.scene.connect_nodes(nodes[i].input_ports[connection["input"]],
                                                      nodes_id[connection["output"]["node"]].output_ports[connection["output"]["index"]])

        for node in d["nodes"]:
            node_vis = nodes_id[node["id"]]
            for idx, i in enumerate(node_vis.input_ports):
                if not i.data_widget is None:
                    i.data_widget.set_value(str(node["values"][idx]))
