import numpy as np
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QGraphicsSceneMouseEvent, QWidget, QVBoxLayout
)

from ...core.node_base import Node
from .workflow_manager import WorkflowManager
from .workflow_scene import WorkflowScene
from .workflow_view import WorkflowView
# from .add_node_menu import AddNodeMenu

class WorkflowWidget(QWidget):
    update_frame_signal = Signal(np.ndarray)

    def __init__(self, workflow_manager: WorkflowManager):
        super().__init__()

        self.workflow_manager = workflow_manager

        self.node_viewing: Node | None = None
        self.init_ui()


    def init_ui(self):
        main_layout = QVBoxLayout(self)

        self.scene = WorkflowScene(self.workflow_manager)
        self.scene.setSceneRect(self.rect())
        self.scene.request_node_menu_signal.connect(self.add_node_menu)
        self.view = WorkflowView(self.scene)

        main_layout.addWidget(self.view)
        self.view.show()

    @Slot(QGraphicsSceneMouseEvent)
    def add_node_menu(self, event: QGraphicsSceneMouseEvent):
        ...
        # menu = AddNodeMenu(event)
        # node_type, kwargs = menu.run()
        # if node_type is None:
        #     return
        # kwargs["x"] = event.scenePos().x()
        # kwargs["y"] = event.scenePos().y()
        # self.add_node(node_type, **kwargs)


    # @Slot(Node)
    # def update_frame(self, node: Node):
    #     frames: list[np.ndarray] = []
    #     for i in node.inputs:
    #         if i.show_input and i.data.data_type == np.ndarray and i.data.value is not None:
    #             frames.append(i.data.value)
    #     for o in node.outputs:
    #         if o.show_output and o.data.data_type == np.ndarray and o.data.value is not None:
    #             frames.append(o.data.value)
    #
    #     self.node_viewing = node
    #     if not frames:
    #         self.update_frame_signal.emit(None)
    #         return
    #
    #     # recolor frames if needed
    #     shape = frames[0].shape
    #     recolor = False
    #     for f in frames[1:]:
    #         if f.shape != shape:
    #             recolor = True
    #             break
    #     if recolor:
    #         for i in range(len(frames)):
    #             if len(frames[i].shape) == 2:
    #                 frames[i] = cv.cvtColor(frames[i], cv.COLOR_GRAY2BGR)
    #
    #     border_shape = list(frames[0].shape)
    #     border_shape[1] = 5
    #     border = 50 * np.ones(border_shape, dtype=np.uint8)
    #     for i in range(len(frames) - 1):
    #         frames[i] = np.concatenate([frames[i], border], 1)
    #     full_frame = np.concatenate(frames, 1)
    #     self.update_frame_signal.emit(full_frame)
    #
    # def get_current_state(self):
    #     return self.node_visulisations
    #
    # def add_node(self, node_type: type, **kwargs):
    #     x = 0
    #     y = 0
    #     if "x" in kwargs:
    #         x = kwargs.pop("x")
    #     if "y" in kwargs:
    #         y = kwargs.pop("y")
    #
    #     node = self.node_manager.add_node(node_type, **kwargs)
    #     node_vis = NodeVis(node)
    #     self.node_visulisations.append(node_vis)
    #     self.scene.add_node(node_vis, x, y)
    #     # deselect all other nodes:
    #     for n in self.node_visulisations:
    #         n.setSelected(False)
    #     node_vis.setSelected(True)
    #
    #     node_vis.double_clicked_signal.connect(self.update_frame)
    #     node_vis.delete_signal.connect(self.delete_node)
    #
    #     node.input_updated_signal.connect(self.node_data_changed)
    #     node.output_updated_signal.connect(self.node_data_changed)
    #
    # @Slot(NodeVis)
    # def delete_node(self, node_vis: NodeVis):
    #     if node_vis in self.node_visulisations:
    #         self.node_manager.delete_node(node_vis.node)
    #         self.node_visulisations.remove(node_vis)
    #         self.scene.delete_node(node_vis)
    #
    # @Slot()
    # def node_data_changed(self):
    #     node = self.sender()
    #     if self.node_viewing != node:
    #         return
    #     self.update_frame(node)
    #
