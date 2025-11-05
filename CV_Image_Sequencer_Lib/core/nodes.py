from typing import IO, Any, Optional, Type
from PySide6.QtCore import QObject, Signal
from uuid import UUID, uuid4

from .types import IOType


class Socket(QObject):

    data_changed = Signal()
    data_received = Signal(object)

    def __init__(self, node: "Node", name: str, dtype: type[IOType]):
        super().__init__()
        self.uuid: UUID = uuid4()
        self.node: "Node" = node
        self.name: str = name
        self.dtype: type[IOType] = dtype

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.node.name}.{self.name}:{self.dtype.__name__}>"


class InputSocket(Socket):

    def __init__(self, node: "Node", name: str, dtype: type[IOType], min_value:
                 Optional[type] = None, max_value: Optional[type] = None):
        super().__init__(node, name, dtype)

        self.connected_output: Optional[OutputSocket] = None
        self._manual_value: Any = None

        self._min_value = min_value
        self._max_value = max_value

    def connect_output(self, output: "OutputSocket"):
        if not issubclass(output.dtype, self.dtype) and not issubclass(self.dtype, output.dtype):
            raise TypeError(f"Incompatible connection: {output.dtype.__name__} -> {self.dtype.__name__}")
        if self.connected_output:
            self.disconnect_output()
        self.connected_output = output
        output.connected_inputs.append(self)
        output.data_changed.connect(self.data_changed)
        self.data_changed.connect(self.node.on_input_data_changed)

    def disconnect_output(self):
        if self.connected_output:
            try:
                self.connected_output.connected_inputs.remove(self)
            except ValueError:
                print("Could not remove input from output's list of connected inputs")
            self.connected_output = None
            self.data_changed.emit()

    def set_manual_value(self, value: IOType):
        if not issubclass(type(value), self.dtype):
            raise TypeError(f"Expected {self.dtype.__name__}, got {type(value).__name__}")
        if not self._min_value is None and value.value < self._min_value:
            raise ValueError(f"Value {value} is smaller then minimal allowed value {self._min_value}")
        if not self._max_value is None and value.value > self._max_value:
            raise ValueError(f"Value {value} is bigger then maximal allowed value {self._max_value}")
        self._manual_value = value
        self.data_changed.emit()

    def value_ok(self, value: IOType) -> bool:
        if not issubclass(type(value), self.dtype):
            return False
        if not self._min_value is None and value.value < self._min_value:
            return False
        if not self._max_value is None and value.value > self._max_value:
            return False
        return True

    def get_value(self) -> Any:
        """Return connected output value or local manual value."""
        if self.connected_output:
            val = self.connected_output.get_value()
        else:
            val = self._manual_value
        self.data_received.emit(val)
        return val
        

    def get_value_buffered(self) -> Any:
        if self.connected_output:
            val = self.connected_output.get_value_buffered(self.uuid)
        else:
            val = self._manual_value
            self.data_received.emit(val)
        return val



class OutputSocket(Socket):

    def __init__(self, node: "Node", name: str, dtype: Type[IOType]):
        super().__init__(node, name, dtype)
        self.connected_inputs: list[InputSocket] = []

    def get_value(self) -> Any:
        val = self.node.compute_output({self.uuid})
        self.data_received.emit(val[self.uuid])
        return val

    def get_value_buffered(self, uuid: UUID) -> Any:
        val = self.node.add_output_request((self.uuid, uuid))
        return val

    def notify_data_changed(self):
        self.data_changed.emit()




class Node(QObject):

    data_changed = Signal()

    def __init__(self, name: str, x: float = 0, y: float = 0):
        super().__init__()
        self.uuid: UUID = uuid4()
        self.name: str = name
        self.x = x
        self.y = y

        self.inputs: dict[UUID, InputSocket] = {}
        self.input_uuids: list[UUID] = []
        self.outputs: dict[UUID, OutputSocket] = {}
        self.output_uuids: list[UUID] = []

        self.request_buffer: dict[UUID, set[UUID]] = {}

    def get_output_by_idx(self, idx) -> OutputSocket:
        return self.outputs[self.output_uuids[idx]]

    def get_input_by_idx(self, idx) -> InputSocket:
        return self.inputs[self.input_uuids[idx]]

    def add_input(self, name: str, dtype: Type[Any]) -> InputSocket:
        socket = InputSocket(self, name, dtype)
        self.inputs[socket.uuid] = socket
        self.input_uuids.append(socket.uuid)
        return socket

    def add_output(self, name: str, dtype: Type[Any]) -> OutputSocket:
        socket = OutputSocket(self, name, dtype)
        self.outputs[socket.uuid] = socket
        self.output_uuids.append(socket.uuid)
        return socket

    def on_input_data_changed(self):
        self.data_changed.emit()
        for out in self.outputs.values():
            out.notify_data_changed()

    def add_output_request(self, connected_uuids: tuple[UUID, UUID]):
        output_uuid, input_uuid = connected_uuids
        # self.request_buffer[output_uuid] = input_uuid
        self.request_buffer.setdefault(output_uuid, set()).add(input_uuid)

    def compute(self, inputs: dict[UUID, Any]) -> dict[UUID, Any]:
        """Override this to perform computation."""
        raise NotImplementedError

    def compute_output(self, requested_outputs: Optional[set[UUID]] = None) -> Any:
        nodes: set[Node] = set()
        inputs: dict[UUID, Any] = {}
        for uuid, socket in self.inputs.items():
            if socket.connected_output:
                nodes.add(socket.connected_output.node)
                socket.get_value_buffered()
            else:
                inputs[uuid] = socket.get_value()

        for node in nodes:
            res_in = node.compute_output()
            inputs.update(res_in)
        for uuid, data in inputs.items():
            self.inputs[uuid].data_received.emit(data)

        outputs = self.compute(inputs)

        if requested_outputs:
            return {uuid: outputs[uuid] for uuid in requested_outputs}

        res_out = {}
        for output_uuid, input_uuids in self.request_buffer.items():
            self.outputs[output_uuid].data_received.emit(outputs[output_uuid])
            for input_uuid in input_uuids:
                res_out[input_uuid] = outputs[output_uuid]
        self.request_buffer = {}
        return res_out
