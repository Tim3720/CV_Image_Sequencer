from typing import Callable
from PySide6.QtCore import QObject, Signal
from core.workflow import Workflow
from utils.video_handler import VideoManager


class OutPut(QObject):
    """
    Implements a node output. If a node computation is finished, the corresponding outputs
    will send a message that new data is available and make sure the data can be grabbed
    from the output. One output can be connected to multiple inputs.
    """

    new_data_signal = Signal()

    def __init__(self, get_data_method: Callable) -> None:
        super().__init__()
        self.get_data_method = get_data_method

    def data_updated(self):
        """This function can be called by the node when the computation is finished."""
        self.new_data_signal.emit()

    def get_data(self):
        """This functions is needed for connected inputs to get the new data. It has to be
        overwritten by the node to which the output is connected"""
        return self.get_data_method


class InPut(QObject):
    """
    Implements a node input. The input keeps a connection to one output it is connected
    to. If the output sends a signal, the input grabs the data and triggers a new
    computation in the node the input is a member of. A input can only receive data from
    one input.
    """

    computation_trigger_signal = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.connected_output = None
        self.data = None

    def connect_output(self, output: OutPut):
        self.connected_output = output
        self.connected_output.new_data_signal.connect(self.data_update)

    def disconnect_output(self):
        if self.connected_output is None:
            return
        self.connected_output.new_data_signal.disconnect(self.data_update)
        self.connected_output = None

    def data_update(self):
        if self.connected_output is not None:
            self.data = self.connected_output.get_data()
            self.computation_trigger_signal.emit()
        

class Node(QObject):
    """
    A node is a base class for a collection of n inputs and m outputs. The node itself is
    responsible for the calculation of the output data from the input data. It reacts upon
    changed input data signals and ensures the output receives the right data.
    """
    computation_finished_signal = Signal()

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self.workflow: list[tuple[Callable, dict[str, str]]] = []
        self.output = None
        self.type_name: str = ""

        self.inputs: list[InPut] = []
        self.outputs: list[OutPut] = []
        self.data = []

        for i in self.inputs:
            i.computation_trigger_signal.connect(self.run_workflow)

    def run_workflow(self):
        input_data = [i.data for i in self.inputs]
        output = []
        for f, args in self.workflow:
            output = f(*input_data, **args)
        self.data = output
        # distribute data to outputs and call output methods
        for output in self.outputs:
            output.data_updated()


class SourceNode(Node):

    def __init__(self, video_manager: VideoManager, parent=None) -> None:
        super().__init__(parent)
        self.type_name: str = "Source"

        self.output = OutPut(video_manager.get_current_frame)
        self.outputs = [self.output]

        # video_manager.frame_ready.connect(lambda _: self.output.data_updated())
        video_manager.frame_ready.connect(self.update)

    def update(self, frame):
        print("SourceNode received update!")
        self.output.data_updated()

class IONode(Node):

    def __init__(self, workflow: Workflow, parent=None) -> None:
        super().__init__(parent)
        self.type_name: str = "I/O"

        self.input = InPut()
        self.inputs = [self.input]

        self.output = OutPut(lambda: None)
        self.outputs = [self.output]

        self.input.computation_trigger_signal.connect(self.update)

    def update(self):
        print("IONode received update!")
        self.output.data_updated()

