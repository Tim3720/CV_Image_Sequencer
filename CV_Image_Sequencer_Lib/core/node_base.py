from dataclasses import asdict, replace
from PySide6.QtCore import QObject, Signal
import uuid

from CV_Image_Sequencer_Lib.utils.type_base import Serializable 

from ..core.workflow_base import Workflow
from ..utils.types import (Float, Image1C, Image3C, IOType)

class OutPut(QObject):
    """
    Implements a node output. If a node computation is finished, the corresponding outputs
    will send a message that new data is available and make sure the data can be grabbed
    from the output. One output can be connected to multiple inputs.
    """

    computation_finished_signal = Signal(object)

    def __init__(
            self, label: str, output_type: IOType, parent_id: str, show_output: bool = False
    ) -> None:
        super().__init__()
        self.label = label
        self.show_output = show_output
        self.data: IOType = output_type
        self.parent_id = parent_id
        self.index: int | None = None

    def data_updated(self, data):
        """This function can be called by the node when the computation is finished."""
        if not isinstance(data, type(self.data)):
            raise ValueError(
                f"Wrong datatype passed to output. Expected {type(self.data)}, got {type(data)}"
            )
        self.data.value = data.value
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
            self, label: str, input_type: IOType, parent_id: str, show_input: bool = False
    ) -> None:
        super().__init__()
        self.label = label
        # self.data_type = type(input_type)
        self.show_input = show_input

        self.connected_output = None
        self.data = input_type
        self.parent_id = parent_id

        self.index: int | None = None

    def connect_output(self, output: OutPut):
        self.connected_output = output
        self.connected_output.computation_finished_signal.connect(self.data_update)

    def disconnect_output(self):
        if self.connected_output is None:
            return
        self.connected_output.computation_finished_signal.disconnect(self.data_update)
        self.connected_output = None

    def data_update(self, data: IOType | None = None, recompute_data: bool = False):
        if data is None:
            if self.data.value is not None and not recompute_data:
                self.computation_trigger_signal.emit()
            elif (self.connected_output is not None and self.connected_output.data is not
                None):
                self.data_update(self.connected_output.data)
            return
        if not isinstance(data, type(self.data)):
            raise ValueError(
                f"Wrong datatype passed to input. Expected {type(self.data)}, got {type(data)}"
            )
        self.data = data
        self.computation_trigger_signal.emit()


class Node(QObject, Serializable):
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
        id: str = "",
    ) -> None:
        super().__init__()

        self.workflow = workflow
        self.name = name
        self.data = []
        self.id = id if id else str(uuid.uuid4())
        self.help_text: str = "This is the template for a default node."

        self.inputs = inputs
        self.outputs = outputs

        for idx, i in enumerate(self.inputs):
            i.computation_trigger_signal.connect(self.run_workflow)
            i.index = idx

        for idx, o in enumerate(self.outputs):
            o.index = idx

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

