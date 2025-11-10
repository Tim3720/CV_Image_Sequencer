from typing import Optional
from PySide6.QtCore import QPoint, QPointF, Signal, Slot
from PySide6.QtGui import QMouseEvent, QPainter, Qt
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QGraphicsView, QVBoxLayout, QWidget

from uuid import uuid4

from CV_Image_Sequencer_Lib.core.nodes import Node, Graph
from CV_Image_Sequencer_Lib.core.types import IOType
from .add_node_menu import AddNodeMenu
from CV_Image_Sequencer_Lib.ui.workflow_tab.socket_vis import SocketVis
from .node_vis import NodeVis
from .connection_vis import ConnectionVis


class GraphicsScene(QGraphicsScene):
    mouse_moved = Signal(QPointF)
    mouse_pressed = Signal(QGraphicsSceneMouseEvent)

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.mouse_moved.emit(event.scenePos())
        return super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.mouse_pressed.emit(event)
        return super().mousePressEvent(event)

class GraphVis(QWidget):

    new_results = Signal(Node)
    new_inputs = Signal(object)
    new_node_viewing = Signal()

    def __init__(self):
        super().__init__()
        self.graph = Graph()

        self.node_visualizations: dict[Node, NodeVis] = {}  # node_uuid: NodeVis
        self.connections: dict[tuple[Node, int, Node, int], ConnectionVis] = {} 
        # descriptor for self.connections: (param_node, param_idx, result_node, result_idx): connection_vis
        self.node_vis_watching: Optional[NodeVis] = None

        self.init_ui()
        self.temp_connection: Optional[ConnectionVis] = None


    def init_ui(self):
        layout = QVBoxLayout(self)

        self.scene = GraphicsScene(0, 0, 800, 600)
        self.view = QGraphicsView(self.scene)

        self.view.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform | self.view.renderHints())
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        self.scene.mouse_pressed.connect(self.handle_mouse_press)

        layout.addWidget(self.view)


    def add_node(self, node_type: type[Node], add_to_graph: bool = True, x: float = 0, y: float = 0, **node_kwargs) -> Node:
        node = node_type(self.graph, **node_kwargs)
        node_vis = NodeVis(node)
        self.node_visualizations[node] = node_vis
        node_vis.delete.connect(self.delete_node)
        node_vis.double_clicked.connect(self.on_node_vis_double_click)

        node_vis.setPos(x, y)
        if add_to_graph:
            self.graph.add_node(node)

        for socket_vis in node_vis.input_sockets:
            socket_vis.clicked.connect(self.make_temp_connection)
        for socket_vis in node_vis.output_sockets:
            socket_vis.clicked.connect(self.make_temp_connection)

        self.scene.addItem(node_vis)
        node.compute()
        return node

    @Slot()
    def delete_node(self):
        sender = self.sender()
        if not isinstance(sender, NodeVis):
            raise ValueError(f"Received delete signal from non-NodeVis object: {sender}")

        if not sender.node in self.node_visualizations:
            return

        node = sender.node

        # delete connections:
        to_delete = []
        for (param_node, _, result_node, _), c in self.connections.items():
            if param_node == node or result_node == node:
                to_delete.append(c)
        for c in to_delete:
            c.delete.emit()

        for socket_vis in sender.input_sockets:
            socket_vis.clicked.disconnect(self.make_temp_connection)
        for socket_vis in sender.output_sockets:
            socket_vis.clicked.disconnect(self.make_temp_connection)

        self.graph.remove_node(sender.node)
        self.node_visualizations.pop(sender.node)
        self.scene.removeItem(sender)

    @Slot()
    def make_temp_connection(self):
        sender = self.sender()
        if not isinstance(sender, SocketVis):
            return

        if not self.temp_connection is None:
            if not self.temp_connection.output_socket is None and sender.is_input:
                input_socket = sender
                output_socket = self.temp_connection.output_socket
            elif not self.temp_connection.input_socket is None and not sender.is_input:
                input_socket = self.temp_connection.input_socket
                output_socket = sender
            else:
                return

            if input_socket.node == output_socket.node:
                print("same nodes")
                return
            if input_socket.dtype != output_socket.dtype:
                print("different dtypes")
                return
            if not self.graph.connections[input_socket.node][input_socket.idx] is None:
                print("input already connected")
                return

            self.add_connection(input_socket.node, input_socket.idx, output_socket.node, output_socket.idx)
            self.remove_temp_connection()
        else:
            self.temp_connection = ConnectionVis()
            if sender.is_input:
                self.temp_connection.add_input_socket(sender)
            else:
                self.temp_connection.add_output_socket(sender)

            self.scene.addItem(self.temp_connection)
            self.scene.mouse_moved.connect(self.temp_connection.update_path)
            self.temp_connection.delete.connect(self.remove_temp_connection)

    def handle_mouse_press(self, event: QGraphicsSceneMouseEvent):
        items_under_mouse = self.scene.items(event.scenePos())
        if not self.temp_connection is None:
            if not items_under_mouse or (len(items_under_mouse) == 1 and isinstance(items_under_mouse[0], ConnectionVis)):
                self.remove_temp_connection()
        if event.button() == Qt.MouseButton.RightButton and not items_under_mouse:
            dialog = AddNodeMenu(event)
            node_type, kwargs = dialog.run()
            if not node_type is None:
                self.add_node(node_type, True, event.scenePos().x(), event.scenePos().y(), **kwargs)


    def remove_temp_connection(self):
        if self.temp_connection is None:
            return
        self.scene.removeItem(self.temp_connection)
        self.temp_connection.deleteLater()
        self.temp_connection = None
        

    @Slot()
    def remove_connection(self):
        sender = self.sender()
        if not isinstance(sender, ConnectionVis):
            return

        if not sender.input_socket is None and sender.input_socket.is_input:
            self.graph.disconnect_nodes(sender.input_socket.node, sender.input_socket.idx)
            for connection_descriptor, c in self.connections.items():
                if c == sender:
                    self.connections.pop(connection_descriptor)
                    break

        self.scene.removeItem(sender)
        sender.deleteLater()

    def add_connection(self, parameter_node: Node, parameter_idx: int, result_node: Node, result_idx: int):
        input_socket_vis = self.node_visualizations[parameter_node].input_sockets[parameter_idx]
        output_socket_vis = self.node_visualizations[result_node].output_sockets[result_idx]

        c = ConnectionVis()
        c.add_input_socket(input_socket_vis)
        c.add_output_socket(output_socket_vis)
        self.scene.addItem(c)
        c.update_path()
        c.delete.connect(self.remove_connection)

        self.connections[(parameter_node, parameter_idx, result_node, result_idx)] = c

        self.node_visualizations[parameter_node].node_vis_position_changed.connect(c.update_path)
        self.node_visualizations[result_node].node_vis_position_changed.connect(c.update_path)

        self.graph.connect_nodes(parameter_node, parameter_idx, result_node, result_idx)
        parameter_node.compute()

    @Slot()
    def on_node_vis_double_click(self):
        sender = self.sender()
        if not isinstance(sender, NodeVis):
            return

        if not self.node_vis_watching is None:
            self.node_vis_watching.node.new_params.disconnect(self.evaluate_node)
            self.node_vis_watching.node.new_inputs.disconnect(self.on_new_inputs)
            self.node_vis_watching.node.new_results.disconnect(self.on_new_results)
            self.node_vis_watching.set_inspect_icon(False)

        self.node_vis_watching = sender
        self.new_node_viewing.emit()

        self.node_vis_watching.node.new_params.connect(self.evaluate_node)
        self.node_vis_watching.node.new_results.connect(self.on_new_results)
        self.node_vis_watching.node.new_inputs.connect(self.on_new_inputs)

        self.evaluate_node()
        self.node_vis_watching.set_inspect_icon(True)

    def evaluate_node(self):
        if self.node_vis_watching is None:
            return
        self.node_vis_watching.node.compute()

    @Slot()
    def on_new_results(self):
        if self.node_vis_watching is None:
            return
        self.new_results.emit(self.node_vis_watching.node)

    @Slot(list)
    def on_new_inputs(self, inputs: list[Optional[IOType]]):
        if self.node_vis_watching is None:
            return
        self.new_inputs.emit(inputs)

    def to_dict(self):
        node_to_uuid: dict[Node, str] = {}
        nodes: dict[str, dict] = {}
        connections: dict[str, list[tuple[int, str, int]]] = {}   # (param_node): (param_idx, result_node, result_idx)
        for param_node, param_node_vis in self.node_visualizations.items():
            uuid = str(uuid4())
            nodes[uuid] = {}
            nodes[uuid]["node"] = param_node.to_dict()
            node_to_uuid[param_node] = uuid
            nodes[uuid]["x"] = param_node_vis.scenePos().x()
            nodes[uuid]["y"] = param_node_vis.scenePos().y()

        for param_node, connection in self.graph.connections.items():
            for param_idx, c_data in enumerate(connection):
                if c_data is None:
                    continue
                result_node, result_idx = c_data
                if not node_to_uuid[param_node] in connections:
                    connections[node_to_uuid[param_node]] = []
                connections[node_to_uuid[param_node]].append((param_idx,
                                                              node_to_uuid[result_node],
                                                              result_idx))

        state = {"nodes": nodes, "connections": connections}
        return state

