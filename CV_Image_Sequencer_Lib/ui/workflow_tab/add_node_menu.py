from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import (
    QGraphicsSceneMouseEvent,
    QInputDialog,
    QMenu,
)

from ...core.custom_nodes import (MaxNode, MinNode, SourceNode, ABSDiffNode,
                                  ThresholdNode, InvertNode, ClampedDiffNode)


class AddNodeMenu(QMenu):

    def __init__(self, event: QGraphicsSceneMouseEvent):
        super().__init__()
        self._event = event
        self._actions: dict[QAction, type] = {}

        self.init_ui()

    def init_ui(self):
        action = QAction("Source Node", self)
        self._actions[action] = SourceNode
        self.addAction(action)

        ################################################
        ## Three channel image nodes
        ################################################
        menu_3C = self.addMenu("3 channel operations") 
        # action = QAction("Invert", self)
        # self._actions[action] = Invert3CNode
        # menu_3C.addAction(action)
        # action = QAction("Split channels", self)
        # self._actions[action] = ChannelSplitNode
        # menu_3C.addAction(action)


        ################################################
        ## One channel image nodes
        ################################################
        menu_1C = self.addMenu("1 channel operations") 
        action = QAction("Threshold", self)
        self._actions[action] = ThresholdNode
        menu_1C.addAction(action)
        action = QAction("Absolute Diff", self)
        self._actions[action] = ABSDiffNode
        menu_1C.addAction(action)
        action = QAction("Clamped Diff", self)
        self._actions[action] = ClampedDiffNode
        menu_1C.addAction(action)
        action = QAction("Pixelwise Min", self)
        self._actions[action] = MinNode
        menu_1C.addAction(action)
        action = QAction("Pixelwise Max", self)
        self._actions[action] = MaxNode
        menu_1C.addAction(action)
        action = QAction("Invert", self)
        self._actions[action] = InvertNode
        menu_1C.addAction(action)


    def run(self):
        res = self.exec_(self._event.screenPos())
        if res is None:
            return None, {}

        params = {}
        if self._actions[res] == SourceNode:
            color, ok = QInputDialog.getItem(None, "Parameters"
                                            , "Colortype", ["Color", "Gray"], 0
                                            , False, Qt.WindowType.WindowStaysOnTopHint)
            if ok:
                value, ok = QInputDialog.getInt(None, "Set number of frames", "Number of frames:", 1, 1, 10, 1)
                if ok:
                    params["n_frames"] = value
                # if color == "Color":
                    return SourceNode, params
                # else:
                #     return GrayScaleSourceNode, params
            else:
                return None, {}
        return self._actions[res], {}

