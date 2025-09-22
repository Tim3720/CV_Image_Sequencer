from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene, QGraphicsView, QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, Qt

from ui.node_vis import Connection, IOVis, NodeVis
from core.node import IONode, InPut, Node, OutPut, SourceNode
from core.node_manager import NodeManager
from utils.video_handler import VideoManager

class WorkflowWidget(QWidget):

    def __init__(self, video_manager: VideoManager, parent=None):
        super().__init__(parent)

        self.video_manager = video_manager
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.scene = WorkflowScene(self.video_manager)
        self.view = QGraphicsView(self.scene)
        main_layout.addWidget(self.view)
        self.view.show()


class WorkflowScene(QGraphicsScene):

    def __init__(self, video_manager: VideoManager, parent=None):
        super().__init__(parent)

        self.temp_connection: Connection | None = None
        self.start_port: IOVis | None = None

        self.video_manager = video_manager
        self.node_manager = NodeManager()
        self.node_visulisations: list[NodeVis] = []
        self.connections: list[Connection]  = []

        self.add_node(SourceNode(self.video_manager))
        self.add_node(IONode(None))
        self.node_visulisations[1].setPos(200, 0)

    def add_node(self, node: Node):
        self.node_manager.add_node(node)
        node_vis = NodeVis(node)
        self.node_visulisations.append(node_vis)
        self.addItem(node_vis)
        node_vis.node_changed_signal.connect(self.update_connections)

    # TODO: delete_node

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.scenePos(), self.views()[0].transform())
            items_under_mouse = self.items(event.scenePos())
            if not items_under_mouse:
                item = None
            else:
                for item in items_under_mouse:
                    if isinstance(item, IOVis):
                        break

            if isinstance(item, IOVis):
                if (self.temp_connection is not None and item != self.start_port and not
                item.is_output and not item.has_connection):

                    if (self.start_port is not None and isinstance(self.start_port.port, OutPut) and isinstance(item.port, InPut)):
                        self.temp_connection.connect(item)
                        self.node_manager.connect_nodes(self.start_port.port, item.port)
                        self.connections.append(self.temp_connection)

                    self.start_port = None
                    self.temp_connection = None
                elif item.is_output and self.temp_connection is None:
                    self.start_port = item
                    self.temp_connection = Connection(item)
                    self.addItem(self.temp_connection)

            elif ((item is None or item == self.temp_connection) and self.temp_connection is not None): # stop making connection
                self.removeItem(self.temp_connection)
                self.making_connection = False
                self.temp_connection = None
                self.start_port = None

        if event.button() == Qt.MouseButton.RightButton:
            items_under_mouse = self.items(event.scenePos())
            item = None
            for item in items_under_mouse:
                if isinstance(item, Connection):
                    break
            if isinstance(item, Connection) and item.end_port is not None: # delete connection
                self.node_manager.disconnect_input(item.end_port.port)
                item.disconnect()
                self.connections.remove(item)
                self.removeItem(item)

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.temp_connection and self.start_port:
            self.temp_connection.update_temp_path( self.start_port.scenePos(), event.scenePos())
        super().mouseMoveEvent(event)


    def update_connections(self):
        for connection in self.connections:
            connection.update_path()

