from typing import Optional
from PySide6.QtWidgets import QFileDialog, QInputDialog, QPushButton, QSplitter, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea
from PySide6.QtGui import QPixmap, QWheelEvent, QPainter, QPen, QMouseEvent
from PySide6.QtCore import Qt, QSize, Slot, QRect, QPoint
import numpy as np
import cv2 as cv
import json

from ...core.types import ColorImage, GrayScaleImage
from ...core.nodes import Node
from ...core.custom_nodes import ABSDiffNode, SourceNode, ThresholdNode
from .graph_vis import GraphVis
from ...core.types import IOType, Serializable
from ...utils.source_manager import SourceManager, convert_cv_to_qt
from ...assets.styles.style import STYLE


class ZoomableLabel(QLabel):
    """QLabel that supports region selection to zoom"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zoom_factor = 1.0
        self.original_pixmap = None
        self.full_image_pixmap = None  # Store the full-size image
        self.view_rect = None  # Current view rectangle on the full image
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Selection rectangle
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        
    def setPixmap(self, pixmap: QPixmap):
        self.original_pixmap = pixmap
        self.full_image_pixmap = pixmap
        self.view_rect = None  # Reset view to full image
        self.zoom_factor = 1.0
        self.selection_start = None
        self.selection_end = None
        self.update_pixmap()
        
    def update_pixmap(self):
        if self.full_image_pixmap is None or self.full_image_pixmap.isNull():
            super().setPixmap(QPixmap())
            return
        
        # If no view_rect, show full image
        if self.view_rect is None:
            pixmap_to_show = self.full_image_pixmap
        else:
            # Crop to view_rect
            pixmap_to_show = self.full_image_pixmap.copy(self.view_rect)
        
        # Scale to fit the label
        scaled_pixmap = pixmap_to_show.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        super().setPixmap(scaled_pixmap)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.is_selecting = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            # Right click = reset zoom
            self.view_rect = None
            self.zoom_factor = 1.0
            self.update_pixmap()
        event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_selecting:
            self.selection_end = event.pos()
            self.update()
        event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            
            if self.selection_start and self.selection_end:
                # Get selection rectangle in widget coordinates
                sel_rect = QRect(self.selection_start, self.selection_end).normalized()
                
                # Only zoom if selection is big enough (avoid accidental clicks)
                if sel_rect.width() > 10 and sel_rect.height() > 10:
                    self.zoom_to_selection(sel_rect)
            
            self.selection_start = None
            self.selection_end = None
            self.update()
        event.accept()
    
    def zoom_to_selection(self, sel_rect: QRect):
        """Zoom to the selected rectangle"""
        if self.pixmap() is None or self.pixmap().isNull():
            return
        
        # Get current displayed pixmap rect
        pixmap = self.pixmap()
        pixmap_rect = pixmap.rect()
        
        # Calculate offset (pixmap is centered in label)
        x_offset = (self.width() - pixmap.width()) // 2
        y_offset = (self.height() - pixmap.height()) // 2
        
        # Translate selection to pixmap coordinates
        sel_on_pixmap = sel_rect.translated(-x_offset, -y_offset)
        
        # Clip to pixmap bounds
        sel_on_pixmap = sel_on_pixmap.intersected(pixmap_rect)
        
        if sel_on_pixmap.isEmpty():
            return
        
        # Calculate scale factor from current pixmap to full image
        if self.view_rect is None:
            # Currently showing full image
            scale_x = self.full_image_pixmap.width() / pixmap.width()
            scale_y = self.full_image_pixmap.height() / pixmap.height()
            
            # Map selection to full image coordinates
            new_view_rect = QRect(
                int(sel_on_pixmap.x() * scale_x),
                int(sel_on_pixmap.y() * scale_y),
                int(sel_on_pixmap.width() * scale_x),
                int(sel_on_pixmap.height() * scale_y)
            )
        else:
            # Currently showing a zoomed view
            scale_x = self.view_rect.width() / pixmap.width()
            scale_y = self.view_rect.height() / pixmap.height()
            
            # Map selection relative to current view
            new_view_rect = QRect(
                self.view_rect.x() + int(sel_on_pixmap.x() * scale_x),
                self.view_rect.y() + int(sel_on_pixmap.y() * scale_y),
                int(sel_on_pixmap.width() * scale_x),
                int(sel_on_pixmap.height() * scale_y)
            )
        
        # Clip to full image bounds
        new_view_rect = new_view_rect.intersected(self.full_image_pixmap.rect())
        
        if not new_view_rect.isEmpty():
            self.view_rect = new_view_rect
            self.update_pixmap()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        # Draw selection rectangle if selecting
        if self.is_selecting and self.selection_start and self.selection_end:
            painter = QPainter(self)
            pen = QPen(Qt.GlobalColor.cyan, 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            
            sel_rect = QRect(self.selection_start, self.selection_end).normalized()
            painter.drawRect(sel_rect)
    
    def wheelEvent(self, event: QWheelEvent):
        # Optional: Keep scroll wheel zoom as well
        delta = event.angleDelta().y()
        
        if delta > 0:
            # Zoom in around mouse position
            self.zoom_at_point(event.position().toPoint(), 1.2)
        else:
            # Zoom out
            self.zoom_at_point(event.position().toPoint(), 0.8)
        
        event.accept()
    
    def zoom_at_point(self, point: QPoint, factor: float):
        """Zoom in/out centered at a specific point"""
        if self.full_image_pixmap is None or self.full_image_pixmap.isNull():
            return
        
        if self.view_rect is None:
            self.view_rect = self.full_image_pixmap.rect()
        
        # Get point in image coordinates
        pixmap = self.pixmap()
        if pixmap is None or pixmap.isNull():
            return
        
        x_offset = (self.width() - pixmap.width()) // 2
        y_offset = (self.height() - pixmap.height()) // 2
        
        point_on_pixmap = point - QPoint(x_offset, y_offset)
        
        # Map to full image coordinates
        scale_x = self.view_rect.width() / pixmap.width()
        scale_y = self.view_rect.height() / pixmap.height()
        
        point_on_full = QPoint(
            self.view_rect.x() + int(point_on_pixmap.x() * scale_x),
            self.view_rect.y() + int(point_on_pixmap.y() * scale_y)
        )
        
        # Calculate new view rect
        new_width = int(self.view_rect.width() / factor)
        new_height = int(self.view_rect.height() / factor)
        
        # Don't zoom out beyond full image
        if new_width >= self.full_image_pixmap.width() or new_height >= self.full_image_pixmap.height():
            self.view_rect = None
            self.update_pixmap()
            return
        
        # Don't zoom in too much
        if new_width < 50 or new_height < 50:
            return
        
        # Center new view on the point
        new_x = point_on_full.x() - new_width // 2
        new_y = point_on_full.y() - new_height // 2
        
        new_view_rect = QRect(new_x, new_y, new_width, new_height)
        
        # Clip to image bounds
        new_view_rect = new_view_rect.intersected(self.full_image_pixmap.rect())
        
        if not new_view_rect.isEmpty():
            self.view_rect = new_view_rect
            self.update_pixmap()


class WorkflowTabWidget(QWidget):
    def __init__(self, source_manager: SourceManager, parent=None):
        super().__init__(parent)

        self.source_manager = source_manager
        self.graph_vis = GraphVis(self.source_manager)

        self.init_ui()

        self.graph_vis.new_results.connect(self.on_new_results)
        self.graph_vis.new_inputs.connect(self.on_new_inputs)
        self.graph_vis.new_node_viewing.connect(self.on_new_node)


    def init_ui(self):
        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter, 1)

        frame_widget = QWidget()
        frame_layout = QHBoxLayout(frame_widget)
        splitter.addWidget(frame_widget)

        ##############################
        # Frames with scroll areas:
        ##############################
        
        # Input frame with scroll area
        input_scroll = QScrollArea()
        input_scroll.setWidgetResizable(True)
        input_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        input_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.input_frame_label = ZoomableLabel("Double click a node to show its in and output")
        self.input_frame_label.setStyleSheet(f"background-color: {STYLE['bg_default']};")
        self.input_frame_label.setMinimumSize(920, 500)
        
        input_scroll.setWidget(self.input_frame_label)
        input_scroll.setMinimumSize(920, 500)

        # Output frame with scroll area
        output_scroll = QScrollArea()
        output_scroll.setWidgetResizable(True)
        output_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        output_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.output_frame_label = ZoomableLabel("Double click a node to show its in and output")
        self.output_frame_label.setStyleSheet(f"background-color: {STYLE['bg_default']};")
        self.output_frame_label.setMinimumSize(920, 500)
        
        output_scroll.setWidget(self.output_frame_label)
        output_scroll.setMinimumSize(920, 500)

        self.org_img_size = (920, 500)
        
        frame_layout.addWidget(input_scroll)
        frame_layout.addStretch()
        frame_layout.addWidget(output_scroll)

        ##############################
        # Workflow:
        ##############################
        splitter.addWidget(self.graph_vis)

        button_bar = QWidget()
        button_bar_layout = QHBoxLayout(button_bar)
        button_bar_layout.setContentsMargins(0, 0, 0, 0)

        save_button = QPushButton("Save workflow")
        save_button.clicked.connect(self.save_workflow)
        button_bar_layout.addWidget(save_button)

        load_button = QPushButton("Load workflow")
        load_button.clicked.connect(self.load_workflow)
        button_bar_layout.addWidget(load_button)

        main_layout.addStretch()
        main_layout.addWidget(button_bar)

    def test(self):
        self.graph_vis.add_node(SourceNode, x=0, y=100, n_frames=3)
        self.graph_vis.add_node(SourceNode, x=0, y=300)
        self.graph_vis.add_node(ABSDiffNode, x=200, y=200)
        self.graph_vis.add_node(ThresholdNode, x=400, y=200)

    @Slot(Node)
    def on_new_results(self, node: Node):
        images = []
        color = False
        for d in node.results:
            if isinstance(d, GrayScaleImage) and not d.value is None:
                images.append(d.value)
            elif isinstance(d, ColorImage) and not d.value is None:
                images.append(d.value)
                color = True

        if not images:
            return

        if color:
            border = np.ones((images[0].shape[0], 10, 3), dtype=np.uint8) * 150
        else:
            border = np.ones((images[0].shape[0], 20), dtype=np.uint8) * 150
        frames = []
        for img in images:
            frames.append(img)
            frames.append(border)
        frames.pop()

        frame = np.concatenate(frames, axis=1)
        if frame.shape[1] > frame.shape[0]:
            factor = self.org_img_size[0] / frame.shape[1]
        else:
            factor = self.org_img_size[1] / frame.shape[0]

        frame = cv.resize(frame, None, fx=factor, fy=factor)

        qimg = convert_cv_to_qt(frame)
        pixmap = QPixmap.fromImage(qimg)
        self.output_frame_label.setPixmap(pixmap)

    @Slot(object)
    def on_new_inputs(self, inputs: list[Optional[IOType]]):
        images = []
        color = False
        for d in inputs:
            if isinstance(d, GrayScaleImage) and not d.value is None:
                images.append(d.value)
            elif isinstance(d, ColorImage) and not d.value is None:
                images.append(d.value)
                color = True

        if not images:
            return

        border = np.ones((images[0].shape[0], 10), dtype=np.uint8) * 150
        frames = []
        for img in images:
            frames.append(img)
            frames.append(border)
        frames.pop()

        frame = np.concatenate(frames, axis=1)
        if frame.shape[1] >= frame.shape[0]:
            factor = self.org_img_size[1] / frame.shape[0]
        else:
            factor = self.org_img_size[0] / frame.shape[1]
        frame = cv.resize(frame, None, fx=factor, fy=factor)

        qimg = convert_cv_to_qt(frame)
        pixmap = QPixmap.fromImage(qimg)
        self.input_frame_label.setPixmap(pixmap)

    @Slot()
    def on_new_node(self):
        self.input_frame_label.setPixmap(QPixmap())
        self.output_frame_label.setPixmap(QPixmap())


    def get_state(self):
        return self.graph_vis.to_dict()

    def save_workflow(self):
        file, _ = QFileDialog.getSaveFileName(None, "Workflow file", "/home/tim/Documents/OtherProjects/CV_Image_Sequencer/Workflows/", "*.json")
        if not file.endswith(".json"):
            file += ".json"
        state = self.get_state()
        with open(file, "w") as f:
            json.dump(state, f, indent=2)


    def load_workflow(self):
        file, _ = QFileDialog.getOpenFileName(None, "Workflow file", "/home/tim/Documents/OtherProjects/CV_Image_Sequencer/Workflows/", "*.json")
        with open(file, "r") as f:
            state = json.load(f)
        self.load_state(state)

    def load_state(self, state: dict):
        nodes = state["nodes"]
        connections = state["connections"]

        # unselect all other nodes:
        for node_vis in list(self.graph_vis.node_visualizations.values()):
            node_vis.setSelected(False)

        uuid_to_nodes: dict[str, Node] = {}
        for uuid, node_vis_info in nodes.items():
            node_info = node_vis_info["node"]
            node_type = Serializable._registry[node_info["node_type"]]
            if not issubclass(node_type, Node):
                continue

            node = self.graph_vis.add_node(node_type, True,
                                                          node_vis_info["x"],
                                                          node_vis_info["y"],
                                                          **node_info["params"])
            uuid_to_nodes[uuid] = node
            external_inputs = []
            for i, (_, dtype) in enumerate(node.parameter_template):
                if node_info["external_inputs"][i] is None:
                    external_inputs.append(None)
                else:
                    value = dtype(node_info["external_inputs"][i])
                    external_inputs.append(value)
            node.external_inputs = external_inputs
            node.new_inputs.emit(node.external_inputs)
            self.graph_vis.node_visualizations[node].setSelected(True)


        for param_uuid, connection_data in connections.items():
            for (param_idx, result_uuid, result_idx) in connection_data:
                self.graph_vis.add_connection(uuid_to_nodes[param_uuid], param_idx,
                                              uuid_to_nodes[result_uuid], result_idx)




