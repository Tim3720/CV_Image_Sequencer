import os
from PySide6.QtWidgets import QTabBar, QWidget, QTabWidget, QLineEdit
from PySide6.QtCore import Signal
import json

from ..utils.source_manager import SourceManager

from .source_tab.source_tab import SourcePlayerTab
from .workflow_tab.workflow_tab import WorkflowTabWidget



class TabBar(QTabBar):
    plus_clicked_signal = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.line_edit = None
        self.editing_index = -1

    def mouseReleaseEvent(self, event) -> None:
        idx = self.tabAt(event.pos())
        if idx >= 0 and self.tabText(idx) == "+":
            self.plus_clicked_signal.emit()
            return
        return super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        idx = self.tabAt(event.pos())
        # exclude Source tab and "+" tab
        if idx >= 1 and idx != self.currentIndex:
            self.start_editing(idx)

        return super().mouseDoubleClickEvent(event)

    def start_editing(self, index: int):
        if self.line_edit is not None:
            return

        rect = self.tabRect(index)
        self.line_edit = QLineEdit(self)
        self.line_edit.setText(self.tabText(index))
        self.line_edit.setGeometry(rect)
        self.line_edit.setFocus()
        self.line_edit.selectAll()
        self.line_edit.editingFinished.connect(self.finish_editing)
        self.line_edit.show()
        self.editing_index = index

    def finish_editing(self):
        if self.line_edit and self.editing_index >= 0:
            new_text = self.line_edit.text().strip()
            if new_text:
                self.setTabText(self.editing_index, new_text)
            self.line_edit.deleteLater()
            self.line_edit = None
            self.editing_index = -1

class TabWidget(QTabWidget):

    def __init__(self, source_manager: SourceManager, parent = None) -> None:
        super().__init__(parent)

        tab_bar = TabBar()
        self.setTabBar(tab_bar)
        self.setTabsClosable(True)

        self.workflow_tabs: list[WorkflowTabWidget] = []

        self.source_manager = source_manager
        self.init_ui()

        self.tabCloseRequested.connect(self.close_tab)
        tab_bar.plus_clicked_signal.connect(self.handle_tab_clicked)


    def init_ui(self):
        self.video_tab = SourcePlayerTab(self.source_manager)
        workflow_tab = WorkflowTabWidget(self.source_manager)
        self.addTab(self.video_tab, "Source")
        self.addTab(workflow_tab, "Workflow 1")
        self.workflow_tabs.append(workflow_tab)

        self.tabBar().setTabButton(0, self.tabBar().ButtonPosition.RightSide, None)

        self.add_tab_widget = QWidget()
        self.addTab(self.add_tab_widget, "+")
        self.tabBar().setTabButton(2, self.tabBar().ButtonPosition.RightSide, None)

        self.setCurrentIndex(1)

    def handle_tab_clicked(self):
        self.insert_new_tab()

    def insert_new_tab(self, tab: WorkflowTabWidget | None = None):
        insert_index = self.count() - 1
        new_tab = tab if tab is not None else WorkflowTabWidget(self.source_manager)
        self.insertTab(insert_index, new_tab, f"Workflow {insert_index}")
        self.setCurrentIndex(insert_index)  # switch to the new tab
        self.workflow_tabs.append(new_tab)
        self.source_manager.emit_frame()

    def close_tab(self, index):
        widget = self.widget(index)
        self.removeTab(index)
        self.workflow_tabs.pop(index - 1)
        widget.deleteLater()

    def save(self):
        state = {}
        state["Workflows"] = {}
        for i, tab in enumerate(self.workflow_tabs):
            state["Workflows"][f"Workflow {i}"] = tab.save_state()

        with open(".state.json", "w") as f:
            json.dump(state, f, indent=2)

    def load(self):
        if not os.path.isfile(".state.json"):
            return

        try:
            with open(".state.json", "r") as f:
                d = json.load(f)
        except:
            return
        while self.workflow_tabs:
            self.close_tab(len(self.workflow_tabs))

        for workflow in d["Workflows"]:
            workflow_tab = WorkflowTabWidget(self.source_manager)
            workflow_tab.load_state(d["Workflows"][workflow])
            self.insert_new_tab(workflow_tab)
