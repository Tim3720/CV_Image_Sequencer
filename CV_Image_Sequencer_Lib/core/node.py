from PySide6.QtCore import QObject, Signal
from numpy import isin

from ..core.workflow_base import Workflow
from ..core.workflows import ABSDiff, ChannelSplit, GetFrame, GrayScale, Threshold
from ..utils.types import (ColorCode3C21C, Float, Image1C, Image3C, Int, ThresholdTypes, Type)
from ..utils.video_manager import VideoManager

class OutPut(QObject):
    """
    Implements a node output. If a node computation is finished, the corresponding outputs
    will send a message that new data is available and make sure the data can be grabbed
    from the output. One output can be connected to multiple inputs.
    """

    computation_finished_signal = Signal(object)

    def __init__(
        self, label: str, output_type: Type, show_output: bool = False
    ) -> None:
        super().__init__()
        self.label = label
        self.data_type = type(output_type)
        self.show_output = show_output
        self.data: Type = output_type

    def data_updated(self, data):
        """This function can be called by the node when the computation is finished."""
        if not isinstance(data, self.data_type):
            raise ValueError(
                f"Wrong datatype passed to output. Expected {self.data_type}, got {type(data)}"
            )
        self.data = data
        self.computation_finished_signal.emit(data)


class InPut(QObject):
    """
    Implements a node input. The input keeps a connection to the one output it is connected
    to. If the output sends a signal, the input grabs the data and triggers a new
    computation in the node the input is a member of. An input can only receive data from
    one output.
    """

    computation_trigger_signal = Signal()

    def __init__(
        self, label: str, input_type: Type, show_input: bool = False
    ) -> None:
        super().__init__()
        self.label = label
        self.data_type = type(input_type)
        self.show_input = show_input

        self.connected_output = None
        self.data = input_type

    def connect_output(self, output: OutPut):
        self.connected_output = output
        self.connected_output.computation_finished_signal.connect(self.data_update)

    def disconnect_output(self):
        if self.connected_output is None:
            return
        self.connected_output.computation_finished_signal.disconnect(self.data_update)
        self.connected_output = None

    def data_update(self, data: object | None = None, recompute_data: bool = False):
        if data is None:
            if self.data.value is not None and not recompute_data:
                self.computation_trigger_signal.emit()
            elif (self.connected_output is not None and self.connected_output.data is not
                None):
                self.data_update(self.connected_output.data)
            return
        if not isinstance(data, self.data_type):
            raise ValueError(
                f"Wrong datatype passed to input. Expected {self.data_type}, got {type(data)}"
            )
        self.data = data
        self.computation_trigger_signal.emit()


class Node(QObject):
    """
    A node is a base class for a collection of n inputs and m outputs. The node itself is
    responsible for the calculation of the output data from the input data using a
    workflow. All settings needed by the node are represented as inputs. It reacts upon
    changed input data signals and ensures the output receives the right data.
    """

    input_updated_signal = Signal()
    output_updated_signal = Signal()

    def __init__(
        self,
        inputs: list[InPut],
        outputs: list[OutPut],
        name: str,
        workflow: Workflow,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.output = None
        self.args = []
        self.workflow = workflow
        self.name = name
        self.data = []

        self.inputs = inputs
        self.outputs = outputs

        for i in self.inputs:
            i.computation_trigger_signal.connect(self.run_workflow)

    def run_workflow(self):
        self.input_updated_signal.emit()

        input_data = []
        for i in self.inputs:
            if i.data is not None and i.data.value is not None:
                input_data.append(i.data)
            elif i.data is not None:
                input_data.append(i.data.get_default_value())
        output_data = self.workflow.run(input_data)

        self.data = output_data
        # distribute data to outputs and call output methods
        for i, output in enumerate(self.outputs):
            output.data_updated(self.data[i])
        self.output_updated_signal.emit()


class SourceNode(Node):
    def __init__(self, video_manager: VideoManager, n_frames: int = 1, parent=None) -> None:
        workflow = GetFrame(video_manager, n_frames)
        outputs = []
        for _ in range(n_frames):
            outputs.append(OutPut("Frame", Image3C(), True))
        super().__init__(
            [], outputs, "Source", workflow, parent=parent
        )
        video_manager.frame_ready.connect(self.run_workflow)


class GrayScaleNode(Node):
    def __init__(self, parent=None) -> None:
        workflow = GrayScale()
        super().__init__(
            [
                InPut("RGB", Image3C(), True),
                InPut("ColorCode", ColorCode3C21C(), False)
            ],
            [OutPut("Gray", Image1C(), True)],
            "GrayScale",
            workflow,
            parent=parent,
        )


class ThresholdNode(Node):
    def __init__(self, parent=None) -> None:
        workflow = Threshold()
        super().__init__(
            [
                InPut("Image", Image1C(), True),
                InPut("Threshold value", Int(value=100, min_value=0, max_value=255), False),
                InPut("New Value", Int(value=255, min_value=0, max_value=255), False),
                InPut("Threshold Type", ThresholdTypes(), False),
            ],
            [
                OutPut("Threshold", Float(), False),
                OutPut("Image", Image1C(), True),
            ],
            "Threshold",
            workflow,
            parent=parent,
        )


class ChannelSplitNode(Node):
    def __init__(self, parent=None) -> None:
        workflow = ChannelSplit()
        super().__init__(
            [
                InPut("Image", Image3C(), True),
            ],
            [
                OutPut("Blue", Image1C(), True),
                OutPut("Green", Image1C(), True),
                OutPut("Red", Image1C(), True),
            ],
            "ChannelSplit",
            workflow,
            parent=parent,
        )

class ABSDiffNode(Node):
    def __init__(self, parent=None) -> None:
        workflow = ABSDiff()
        super().__init__(
            [
                InPut("Image1", Image1C(), True),
                InPut("Image2", Image1C(), True),
            ],
            [
                OutPut("Diff", Image1C(), True),
            ],
            "ABSDiff",
            workflow,
            parent=parent,
        )
