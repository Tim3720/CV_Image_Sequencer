import sys
from PySide6.QtWidgets import (QApplication, QGraphicsPathItem, QMainWindow, QGraphicsView, QGraphicsScene,
QGraphicsRectItem, QGraphicsTextItem, QGraphicsPathItem)
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF

# -------------------------
# Node GUI Representation
# -------------------------

class GUINode(QGraphicsRectItem):
    def __init__(self, node, width=120, height=60):
        super().__init__(0, 0, width, height)
        self.node = node
        self.setBrush(QBrush(QColor("#2e2e2e")))
        self.setPen(QPen(QColor("#888")))
        self.setFlags(QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemIsSelectable)
        
        self.text = QGraphicsTextItem(node.name, parent=self)
        self.text.setDefaultTextColor(Qt.white)
        self.text.setPos(10, 10)

# -------------------------
# Edge GUI Representation
# -------------------------

class GUIEdge(QGraphicsPathItem):
    def __init__(self, start_node: GUINode, end_node: GUINode):
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        self.setPen(QPen(QColor(50, 200, 50), 2))
        self.update_path()
        
    def update_path(self):
        p1 = self.start_node.scenePos() + QPointF(self.start_node.rect().width(), self.start_node.rect().height()/2)
        p2 = self.end_node.scenePos() + QPointF(0, self.end_node.rect().height()/2)
        path = QPainterPath()
        path.moveTo(p1)
        dx = (p2.x() - p1.x()) * 0.5
        c1 = QPointF(p1.x() + dx, p1.y())
        c2 = QPointF(p2.x() - dx, p2.y())
        path.cubicTo(c1, c2, p2)
        self.setPath(path)

# -------------------------
# Main Window
# -------------------------

class WorkflowGUI(QMainWindow):
    def __init__(self, nodes):
        super().__init__()
        self.setWindowTitle("Workflow GUI Prototype")
        self.resize(800, 600)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        
        # Create GUI nodes
        self.gui_nodes = {}
        x, y = 50, 50
        for n in nodes:
            gnode = GUINode(n)
            gnode.setPos(x, y)
            self.scene.addItem(gnode)
            self.gui_nodes[n] = gnode
            y += 120
        
        # Create GUI edges based on node connections
        self.gui_edges = []
        for n in nodes:
            for out_node in n.outputs:
                edge = GUIEdge(self.gui_nodes[n], self.gui_nodes[out_node])
                self.scene.addItem(edge)
                self.gui_edges.append(edge)

        # Timer to update edges dynamically when nodes move
        from PySide6.QtCore import QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_edges)
        self.timer.start(30)

    def update_edges(self):
        for edge in self.gui_edges:
            edge.update_path()

# -------------------------
# Example Nodes
# -------------------------

class Node:
    def __init__(self, name):
        self.name = name
        self.inputs = []
        self.outputs = []

    def add_input(self, node):
        self.inputs.append(node)
        node.outputs.append(self)

# Build example workflow
input_node = Node("Input")
gray_node = Node("Grayscale")
blur_node = Node("Blur")
threshold_node = Node("Threshold")

gray_node.add_input(input_node)
blur_node.add_input(gray_node)
threshold_node.add_input(blur_node)

nodes = [input_node, gray_node, blur_node, threshold_node]

# -------------------------
# Run GUI
# -------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorkflowGUI(nodes)
    window.show()
    sys.exit(app.exec())
