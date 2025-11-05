from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QVBoxLayout, QWidget

from ...core.graph import Graph
from .node_vis import NodeVis


class GraphVis(QWidget):

    def __init__(self, graph: Graph):
        super().__init__()
        self.graph = graph

        self.init_ui()

        for _, node in self.graph.nodes.items():
            self.add_node(node, False, node.x, node.y)


    def init_ui(self):
        layout = QVBoxLayout(self)

        self.scene = QGraphicsScene(0, 0, 600, 400)
        self.view = QGraphicsView(self.scene)

        layout.addWidget(self.view)


    def add_node(self, node, add_to_graph: bool = True, x: float = 0, y: float = 0):
        node_vis = NodeVis(node)
        node_vis.setPos(x, y)
        if add_to_graph:
            self.graph.add_node(node)

        self.scene.addItem(node_vis)
