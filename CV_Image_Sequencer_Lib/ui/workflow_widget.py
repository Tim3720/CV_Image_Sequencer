import cv2 as cv
import numpy as np
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import Qt, QPainter
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from CV_Image_Sequencer_Lib.ui.workflow_editor import WorkflowEditor

from ..core.node import ChangeColorNode, GrayScaleNode, InPut, Node, OutPut, SourceNode
from ..core.node_manager import NodeManager
from ..utils.video_manager import VideoManager
from .node_vis import Connection, IOPort, NodeVis


class WorkflowManger(QWidget):
    update_frame_signal = Signal(np.ndarray)

    def __init__(self, video_manager: VideoManager, parent=None):
        super().__init__(parent)

        self.node_viewing: Node | None = None
        self.video_manager = video_manager

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.stacked = QStackedWidget()

        self.scene = WorkflowScene(self.video_manager, self)
        self.scene.setSceneRect(self.rect())
        self.view = WorkflowView(self.scene)

        self.editor = WorkflowEditor()
        self.editor.finished_signal.connect(lambda: self.stacked.setCurrentIndex(0))

        self.stacked.addWidget(self.view)
        self.stacked.addWidget(self.editor)
        self.stacked.setCurrentIndex(0)

        main_layout.addWidget(self.stacked)

        self.view.show()

    @Slot(Node)
    def update_frame(self, node: Node):
        frames: list[np.ndarray] = []
        for i in node.inputs:
            if i.show_input and type(i.data.value) == np.ndarray:
                frames.append(i.data.value)
        for o in node.outputs:
            if o.show_output and type(o.data.value) == np.ndarray:
                frames.append(o.data.value)

        self.node_viewing = node
        if not frames:
            self.update_frame_signal.emit(None)
            return

        # recolor frames if needed
        shape = frames[0].shape
        recolor = False
        for f in frames[1:]:
            if f.shape != shape:
                recolor = True
                break
        if recolor:
            for i in range(len(frames)):
                if len(frames[i].shape) == 2:
                    frames[i] = cv.cvtColor(frames[i], cv.COLOR_GRAY2BGR)

        self.update_frame_signal.emit(np.concatenate(frames, 1))


class WorkflowScene(QGraphicsScene):
    def __init__(self, video_manager: VideoManager, workflow_manager: WorkflowManger):
        super().__init__()

        self.workflow_manager = workflow_manager

        self.temp_connection: Connection | None = None
        self.start_port: IOPort | None = None

        self.video_manager = video_manager
        self.node_manager = NodeManager()
        self.node_visulisations: list[NodeVis] = []
        self.connections: list[Connection] = []

        # TODO: Remove test:
        self.add_node(SourceNode(self.video_manager))
        self.add_node(GrayScaleNode())
        self.add_node(ChangeColorNode())
        self.node_visulisations[1].setPos(200, 100)
        self.node_visulisations[2].setPos(200, 0)

    def add_node(self, node: Node):
        self.node_manager.add_node(node)
        node_vis = NodeVis(node)
        self.node_visulisations.append(node_vis)
        self.addItem(node_vis)

        node_vis.node_position_changed_signal.connect(self.update_connections)
        node_vis.double_clicked_signal.connect(self.workflow_manager.update_frame)
        node.input_updated_signal.connect(self.node_data_changed)
        node.output_updated_signal.connect(self.node_data_changed)

        # connect to ports:
        for i in node_vis.input_ports:
            i.port_press_signal.connect(self.port_clicked)
        for o in node_vis.output_ports:
            o.port_press_signal.connect(self.port_clicked)

    @Slot()
    def port_clicked(self):
        port = self.sender()
        if not isinstance(port, IOPort):
            return

        # start new temporary connection
        if self.start_port is None and (
            isinstance(port.port, OutPut) or port.port.connected_output is None
        ):
            self.start_port = port
            self.temp_connection = Connection(self.start_port)
            self.addItem(self.temp_connection)
            return

        # try to finish connection
        if (
            self.temp_connection is not None
            and self.start_port is not None
            and self.start_port.parent_node != port.parent_node
            and self.start_port.port.data_type == port.port.data_type
        ):
            if (
                isinstance(port.port, InPut)
                and isinstance(self.start_port.port, OutPut)
                and port.port.connected_output is None
            ):
                self.node_manager.connect_nodes(self.start_port.port, port.port)
            elif (
                isinstance(port.port, OutPut)
                and isinstance(self.start_port.port, InPut)
                and self.start_port.port.connected_output is None
            ):
                self.node_manager.connect_nodes(port.port, self.start_port.port)
            else:
                return

            self.temp_connection.connect_path(port)
            self.connections.append(self.temp_connection)
            self.temp_connection.delete_connection_sigal.connect(self.delete_connection)
            self.temp_connection = None
            self.start_port = None

    @Slot()
    def delete_connection(self):
        connection = self.sender()
        if not isinstance(connection, Connection) or connection.end_port is None:
            return
        connection.delete_connection_sigal.disconnect(self.delete_connection)
        self.connections.remove(connection)
        if isinstance(connection.start_port.port, InPut):
            self.node_manager.disconnect_input(connection.start_port.port)
        elif isinstance(connection.end_port.port, InPut):
            self.node_manager.disconnect_input(connection.end_port.port)
        else:
            return
        self.removeItem(connection)

    # TODO: delete_node

    @Slot()
    def node_data_changed(self):
        node = self.sender()
        if self.workflow_manager.node_viewing != node:
            return
        self.workflow_manager.update_frame(node)

    def mousePressEvent(self, event) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.temp_connection is not None
        ):
            # get items under mouse:
            items_under_mouse = self.items(event.scenePos())
            item = None
            for item in items_under_mouse:
                if isinstance(item, IOPort):
                    break
            if not isinstance(item, IOPort):
                self.start_port = None
                self.removeItem(self.temp_connection)
                self.temp_connection = None
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.temp_connection and self.start_port:
            self.temp_connection.update_temp_path(
                self.start_port.scenePos(), event.scenePos()
            )
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        return super().mouseDoubleClickEvent(event)

    def update_connections(self):
        for connection in self.connections:
            connection.update_path()


class WorkflowView(QGraphicsView):
    def __init__(self, scene: WorkflowScene):
        super().__init__(scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.SmoothPixmapTransform | self.renderHints())
        self.setDragMode(QGraphicsView.DragMode.NoDrag)  # pan with middle mouse drag
        self.scale_factor = 1.15
        self.setSceneRect(scene.sceneRect())
        self._panning = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:  # scroll wheel pressed
            self._panning = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self._drag_start = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.pos() - self._drag_start
            self._drag_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        old_pos = self.mapToScene(event.position().toPoint())
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
        new_pos = self.mapToScene(event.position().toPoint())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
        self.setSceneRect(self.scene().itemsBoundingRect())
