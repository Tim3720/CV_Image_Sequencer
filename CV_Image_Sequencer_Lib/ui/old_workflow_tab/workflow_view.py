from PySide6.QtGui import Qt, QPainter
from PySide6.QtWidgets import (
    QGraphicsView,
)

from .workflow_scene import WorkflowScene

class WorkflowView(QGraphicsView):
    def __init__(self, scene: WorkflowScene):
        super().__init__(scene)

        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform | self.renderHints())
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        self.scale_factor = 1.15
        # self.setSceneRect(scene.sceneRect())
        self._panning = False

    # def mousePressEvent(self, event):
    #     if event.button() == Qt.MouseButton.MiddleButton: 
    #         self._panning = True
    #         self.setCursor(Qt.CursorShape.ClosedHandCursor)
    #         self._drag_start = event.pos()
    #     else:
    #         super().mousePressEvent(event)
    #
    # def mouseMoveEvent(self, event):
    #     if self._panning:
    #         delta = event.pos() - self._drag_start
    #         self._drag_start = event.pos()
    #         self.horizontalScrollBar().setValue(
    #             self.horizontalScrollBar().value() - delta.x()
    #         )
    #         self.verticalScrollBar().setValue(
    #             self.verticalScrollBar().value() - delta.y()
    #         )
    #     else:
    #         super().mouseMoveEvent(event)
    #
    # def mouseReleaseEvent(self, event):
    #     if event.button() == Qt.MouseButton.MiddleButton:
    #         self._panning = False
    #         self.setCursor(Qt.CursorShape.ArrowCursor)
    #     else:
    #         super().mouseReleaseEvent(event)
    #
    # def wheelEvent(self, event):
    #     old_pos = self.mapToScene(event.position().toPoint())
    #     factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
    #     self.scale(factor, factor)
    #     new_pos = self.mapToScene(event.position().toPoint())
    #     delta = new_pos - old_pos
    #     self.translate(delta.x(), delta.y())
    #     self.setSceneRect(self.scene().itemsBoundingRect())
