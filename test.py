import os
import sys
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import QFileSystemWatcher
import cv2 as cv

from CV_Image_Sequencer_Lib.core.custom_nodes import InvertNode, SourceNode, ABSDiffNode, Graph, ThresholdNode
from CV_Image_Sequencer_Lib.core.types import GrayScaleImage
from CV_Image_Sequencer_Lib.ui.workflow_tab.graph_vis import GraphVis

import importlib 

class ReloadingTest:

    def __init__(self) -> None:
        img_path = "/home/tim/Documents/Arbeit/HDF5Test/SO298_298-10-1_PISCO2_20230422-2334_Results/Images"
        files = os.listdir(img_path)
        self.img1 = cv.imread(os.path.join(img_path, files[10]), cv.IMREAD_GRAYSCALE)
        self.img2 = cv.imread(os.path.join(img_path, files[11]), cv.IMREAD_GRAYSCALE)

        self.graph = Graph()
        self.app = QApplication(sys.argv)
        main_window = QMainWindow()

        c_widget = QWidget()
        self.layout = QVBoxLayout(c_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.graph_vis = GraphVis(self.graph)

        self.graph_vis.add_node(SourceNode, True, 100, 200)
        self.graph_vis.add_node(SourceNode, True, 100, 400)
        self.graph_vis.add_node(ThresholdNode, True, 500, 300)


        reload_button = QPushButton("Reload")
        reload_button.clicked.connect(self.reload)
        self.layout.addWidget(reload_button)
        self.layout.addWidget(self.graph_vis)

        main_window.setCentralWidget(c_widget)
        main_window.show()

        self.app.exec()


    def reload(self):
        # reload modules:
        to_reload = []
        for key, module in sys.modules.items():
            if key.startswith("CV_Image_Sequencer_Lib.ui"):
                to_reload.append(module)
        for m in to_reload:
            importlib.reload(m)

        module = sys.modules["CV_Image_Sequencer_Lib.ui.workflow_tab.graph_vis"]
        cls = getattr(module, "GraphVis")

        try:
            self.layout.removeWidget(self.graph_vis)
            self.graph_vis.deleteLater()
            del self.graph
            self.graph = Graph()
            self.graph_vis = GraphVis(self.graph)

            self.graph_vis = cls(self.graph)
            self.graph_vis.add_node(SourceNode, True, 100, 200)
            self.graph_vis.add_node(SourceNode, True, 100, 400)
            self.graph_vis.add_node(ThresholdNode, True, 300, 300)
            self.graph_vis.add_node(ThresholdNode, True, 500, 300)
            self.graph_vis.add_node(InvertNode, True, 200, 100)


            # self.graph.connect_sockets_by_idx(img_node1, 0, self.absdiff_node, 0)
            # self.graph.connect_sockets_by_idx(img_node2, 0, invert_node, 0)
            # self.graph.connect_sockets_by_idx(invert_node, 0, self.absdiff_node, 1)

            self.layout.addWidget(self.graph_vis)
        except:
            print("Failed to reload")

        # result = self.graph.evaluate_socket(self.absdiff_node, self.absdiff_node.output_uuids[0])[self.absdiff_node.output_uuids[0]]
        print("Reloaded ✅")


if __name__ == "__main__":
    app = ReloadingTest()
