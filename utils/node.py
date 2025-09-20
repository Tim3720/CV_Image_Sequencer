from types import FunctionType
from PySide6.QtCore import QObject


class Node(QObject):

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self.workflow: dict[FunctionType, dict[str, str]] = {}

        self.inputs = []
        self.outputs = []

    def run_workflow(self):
        ...
