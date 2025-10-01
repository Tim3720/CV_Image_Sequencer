from typing import TypeVar
import numpy as np
from PySide6.QtCore import QObject, Signal

from ..core.workflow import ChangeColor, GetFrame, GrayScale, Workflow
from ..utils.types import (ColorCodeType3C23C, GrayScaleImageType, Image3CType,
TypeBaseModel, ColorCodeType3C21C)
from ..utils.video_manager import VideoManager

U = TypeVar("U")

class OutPut(QObject):
    """
    Implements a node output. If a node computation is finished, the corresponding outputs
    will send a message that new data is available and make sure the data can be grabbed
    from the output. One output can be connected to multiple inputs.
    """

    computation_finished_signal = Signal(object)

    def __init__(
        self, label: str, output_type: TypeBaseModel[U], show_output: bool = False
    ) -> None:
        super().__init__()
        self.label = label
        self.data_type = output_type
        self.show_output = show_output
        self.data: TypeBaseModel = output_type

    def data_updated(self, data):
        """This function can be called by the node when the computation is finished."""
        if not isinstance(data, type(self.data_type)):
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
        self, label: str, input_type: TypeBaseModel[U], show_input: bool = False
    ) -> None:
        super().__init__()
        self.label = label
        self.data_type = input_type
        self.show_input = show_input

        self.connected_output = None
        self.data: TypeBaseModel = input_type

    def connect_output(self, output: OutPut):
        self.connected_output = output
        self.connected_output.computation_finished_signal.connect(self.data_update)

    def disconnect_output(self):
        if self.connected_output is None:
            return
        self.connected_output.computation_finished_signal.disconnect(self.data_update)
        self.connected_output = None

    def data_update(self, data: object | None = None):
        if data is None:
            if self.data.value is not None:
                self.computation_trigger_signal.emit()
            elif (self.connected_output is not None and self.connected_output.data is not
                None):
                self.data_update(self.connected_output.data)
            return
        if not isinstance(data, type(self.data_type)):
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
                input_data.append(i.data.value)
            elif i.data is not None:
                input_data.append(i.data.get_default_value())

        output_data = self.workflow.run(input_data)

        self.data = output_data
        # distribute data to outputs and call output methods
        for i, output in enumerate(self.outputs):
            output.data_updated(self.data[i])
        self.output_updated_signal.emit()


class SourceNode(Node):
    def __init__(self, video_manager: VideoManager, parent=None) -> None:
        workflow = GetFrame(video_manager)
        super().__init__(
            [], [OutPut("Frame", Image3CType(), True)], "Source", workflow, parent=parent
        )
        video_manager.frame_ready.connect(self.run_workflow)


class GrayScaleNode(Node):
    def __init__(self, parent=None) -> None:
        workflow = GrayScale()
        super().__init__(
            [
                InPut("RGB", Image3CType(), True),
                InPut("ColorCode", ColorCodeType3C21C(), False)
            ],
            [OutPut("Gray", GrayScaleImageType(), True)],
            "GrayScale",
            workflow,
            parent=parent,
        )


class ChangeColorNode(Node):
    def __init__(self, parent=None) -> None:
        workflow = ChangeColor()
        super().__init__(
            [InPut("Image", Image3CType(), True), InPut("ColorCode", ColorCodeType3C23C(), False)],
            [OutPut("Image", Image3CType(), True)],
            "ChangeColor",
            workflow,
            parent=parent,
        )
