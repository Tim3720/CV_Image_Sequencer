import os
import sys
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QFileSystemWatcher
import cv2 as cv

from CV_Image_Sequencer_Lib.core.custom_nodes import ImageInputNode, ABSDiffNode, InvertNode
from CV_Image_Sequencer_Lib.core.graph import Graph
from CV_Image_Sequencer_Lib.core.types import GrayScaleImage
from CV_Image_Sequencer_Lib.ui.workflow_tab.graph_vis import GraphVis

from importlib import reload



graph = Graph()
img_path = "/home/tim/Documents/Arbeit/HDF5Test/SO298_298-10-1_PISCO2_20230422-2334_Results/Images"
files = os.listdir(img_path)
img1 = cv.imread(os.path.join(img_path, files[10]), cv.IMREAD_GRAYSCALE)
img2 = cv.imread(os.path.join(img_path, files[11]), cv.IMREAD_GRAYSCALE)

img_node1 = ImageInputNode(GrayScaleImage(img1), 0, 0)
img_node2 = ImageInputNode(GrayScaleImage(img2), 0, 200)
invert_node = InvertNode(200, 200)
absdiff_node = ABSDiffNode(400, 100)

# graph.node_added.connect(lambda x: print("Node added", x))
# graph.connection_added.connect(lambda x: print("Connection added", x))

graph.add_node(img_node1)
graph.add_node(img_node2)
graph.add_node(invert_node)
graph.add_node(absdiff_node)

graph.connect_sockets_by_idx(img_node1, 0, absdiff_node, 0)
graph.connect_sockets_by_idx(img_node2, 0, invert_node, 0)
graph.connect_sockets_by_idx(invert_node, 0, absdiff_node, 1)

# img_node1.get_output_by_idx(0).data_received.connect(lambda x: print(x))
# absdiff_node.get_output_by_idx(0).data_received.connect(lambda x: print(x))

# # Evaluate lazily
# cv.imshow("result", result.value)
# cv.waitKey()


app = QApplication(sys.argv)
main_window = QMainWindow()

c_widget = QWidget()
layout = QVBoxLayout(c_widget)
layout.setContentsMargins(0, 0, 0, 0)
graph_vis = GraphVis(graph)

layout.addWidget(graph_vis)
main_window.setCentralWidget(c_widget)

def reload_widget():
    global graph_vis
    # reload(sys.modules["CV_Image_Sequencer_Lib"])
    to_reload = []
    for key in sys.modules.keys():
        if key.startswith("CV_Image_Sequencer_Lib.ui.workflow_tab"):
            to_reload.append(sys.modules[key])
    for module in to_reload:
        reload(module)

    to_reload = []
    for key in sys.modules.keys():
        if key.startswith("CV_Image_Sequencer_Lib.core."):
            to_reload.append(sys.modules[key])
    for module in to_reload:
        reload(module)
    # reload(sys.modules["CV_Image_Sequencer_Lib.ui.workflow_tab.graph_vis"])
    # reload(sys.modules["CV_Image_Sequencer_Lib.ui.workflow_tab.type_vis"])
    layout.removeWidget(graph_vis)
    graph_vis.deleteLater()
    graph_vis = GraphVis(graph)
    layout.addWidget(graph_vis)
    print("✅ Widget reloaded.")


watcher = QFileSystemWatcher(["/home/tim/Documents/OtherProjects/CV_Image_Sequencer/CV_Image_Sequencer_Lib/ui/workflow_tab/",
                    "/home/tim/Documents/OtherProjects/CV_Image_Sequencer/CV_Image_Sequencer_Lib/core/"])
watcher.directoryChanged.connect(reload_widget)
reload_widget()

main_window.show()
result = graph.evaluate(absdiff_node,
                        absdiff_node.output_uuids[0])[absdiff_node.output_uuids[0]]

app.exec()

