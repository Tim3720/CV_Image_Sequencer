from ast import Tuple
from typing import Any, Optional, Type
from PySide6.QtCore import QObject, Signal
from dataclasses import dataclass
import numpy as np
from uuid import UUID, uuid4
import cv2 as cv


@dataclass
class GrayScaleImage:
    value: Optional[np.ndarray]

@dataclass
class ColorImage:
    value: Optional[np.ndarray]

@dataclass
class Option:
    value: dict[str, Any]

class Socket(QObject):

    data_changed = Signal()

    def __init__(self, node: "Node", name: str, dtype: Type[Any]):
        super().__init__()
        self.uuid: UUID = uuid4()
        self.node: Node = node
        self.name: str = name
        self.dtype: Type = dtype

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.node.name}.{self.name}:{self.dtype.__name__}>"


class InputSocket(Socket):

    def __init__(self, node: "Node", name: str, dtype: Type[Any]):
        super().__init__(node, name, dtype)

        self.connected_output: Optional[OutputSocket] = None
        self._manual_value: Any = None

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

    def set_manual_value(self, value: Any):
        if not isinstance(value, self.dtype):
            raise TypeError(f"Expected {self.dtype.__name__}, got {type(value).__name__}")
        self._manual_value = value
        self.data_changed.emit()

    def get_value(self) -> Any:
        """Return connected output value or local manual value."""
        if self.connected_output:
            return self.connected_output.get_value()
        return self._manual_value

    def get_value_buffered(self) -> Any:
        if self.connected_output:
            return self.connected_output.get_value_buffered(self.uuid)
        return self._manual_value



class OutputSocket(Socket):

    def __init__(self, node: "Node", name: str, dtype: Type[Any]):
        super().__init__(node, name, dtype)
        self.connected_inputs: list[InputSocket] = []

    def get_value(self) -> Any:
        return self.node.compute_output({self.uuid})

    def get_value_buffered(self, uuid: UUID) -> Any:
        return self.node.add_output_request((self.uuid, uuid))

    def notify_data_changed(self):
        self.data_changed.emit()



class Node(QObject):

    data_changed = Signal()

    def __init__(self, name: str):
        super().__init__()
        self.uuid: UUID = uuid4()
        self.name: str = name

        self.inputs: dict[UUID, InputSocket] = {}
        self.input_uuids: list[UUID] = []
        self.outputs: dict[UUID, OutputSocket] = {}
        self.output_uuids: list[UUID] = []

        self.request_buffer: dict[UUID, set[UUID]] = {}

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

        outputs = self.compute(inputs)

        if requested_outputs:
            return {uuid: outputs[uuid] for uuid in requested_outputs}

        res_out = {}
        # for uuid in self.request_buffer:
        #     res_out[self.request_buffer[uuid]] = outputs[uuid]
        for output_uuid, input_uuids in self.request_buffer.items():
            for input_uuid in input_uuids:
                res_out[input_uuid] = outputs[output_uuid]
        self.request_buffer = {}
        return res_out

    # def compute_output(self, uuid: UUID) -> Any:
    #     """Recursively compute only requested output."""
    #     print("Compute output", self)
    #     # Gather inputs lazily
    #     inputs = {n: s.get_value() for n, s in self.inputs.items()}
    #     outputs = self.compute(inputs)
    #     return outputs[uuid]



class Graph(QObject):
    """Manages nodes and connections."""
    def __init__(self):
        super().__init__()
        self.nodes: list[Node] = []

    def add_node(self, node: Node):
        self.nodes.append(node)

    def connect_sockets(self, out_socket: OutputSocket, in_socket: InputSocket):
        in_socket.connect_output(out_socket)

    def connect_sockets_by_idx(self, node_out: Node, idx_out: int, node_in: Node, idx_in: int):
        try:
            out_socket = node_out.outputs[node_out.output_uuids[idx_out]]
            in_socket = node_in.inputs[node_in.input_uuids[idx_in]]
            self.connect_sockets(out_socket, in_socket)
        except KeyError or IndexError:
            ...

    def evaluate(self, node: Node, output_uuid: UUID) -> Any:
        return node.outputs[output_uuid].get_value()

class BlackBoxNode(Node):

    def __init__(self, name: str):
        super().__init__(name)
        self.sub_graph = Graph()
        self.input_map: dict[UUID, InputSocket] = {}
        self.output_map: dict[UUID, OutputSocket] = {}

    def expose_input(self, inner_input: InputSocket, name: Optional[str] = None):
        external_name: str = name or inner_input.name
        external_socket = self.add_input(external_name, inner_input.dtype)
        self.input_map[external_socket.uuid] = inner_input

        # Connect external -> internal manually (value forwarding)
        def forward_value_changed():
            value = external_socket.get_value()
            inner_input.set_manual_value(value)
        external_socket.data_changed.connect(forward_value_changed)

    def expose_output(self, inner_output: OutputSocket, name: Optional[str] = None):
        external_name: str = name or inner_output.name
        external_socket = OutputSocket(self, external_name, inner_output.dtype)
        self.output_map[external_socket.uuid] = inner_output

        inner_output.data_changed.connect(external_socket.data_changed)

    def compute(self, inputs: dict[UUID, Any]) -> dict[UUID, Any]:
        """When an external output is requested, pull it from the inner graph."""
        results = {}
        for uuid, inner_output in self.output_map.items():
            results[uuid] = inner_output.get_value()
        return results


##################################
## Example:
##################################
class ImageInputNode(Node):
    """Provides a fixed grayscale image."""
    def __init__(self, name: str, image: GrayScaleImage):
        super().__init__(name)
        self.image = image
        self.add_output("image", GrayScaleImage)

    def compute(self, inputs: dict[UUID, Any]) -> dict[UUID, Any]:
        return {self.output_uuids[0]: self.image}



class InvertImageNode(Node):
    """Inverts grayscale image data."""
    def __init__(self, name: str):
        super().__init__(name)
        self.add_input("image", GrayScaleImage)
        self.add_output("inverted", GrayScaleImage)

    def compute(self, inputs: dict[UUID, Any]) -> dict[UUID, Any]:
        img: GrayScaleImage = inputs[self.input_uuids[0]]
        if img.value is None:
            return {self.output_uuids[0]: None}
        # Example computation
        inverted = GrayScaleImage(value=img.value - 255)
        return {self.output_uuids[0]: inverted}


class BrightnessNode(Node):
    """Adds brightness to an image based on manual or connected value."""
    def __init__(self, name: str):
        super().__init__(name)
        self.add_input("image", GrayScaleImage)
        self.add_input("brightness", float)
        self.add_output("result", GrayScaleImage)

    def compute(self, inputs: dict[UUID, Any]) -> dict[UUID, Any]:
        img: GrayScaleImage = inputs[self.input_uuids[0]]
        brightness: float = 0.0
        if self.input_uuids[1] in inputs:
            brightness = inputs[self.input_uuids[1]] 
        if img.value is None:
            return {self.output_uuids[0]: None}
        res = img.value.astype(np.int32) + brightness
        res[res < 0] = 0
        res[res > 255] = 255
        result = GrayScaleImage(res.astype(np.uint8))
        return {self.output_uuids[0]: result}

class ABSDiffNode(Node):
    """Adds brightness to an image based on manual or connected value."""
    def __init__(self, name: str):
        super().__init__(name)
        self.add_input("image 1", GrayScaleImage)
        self.add_input("image 2", GrayScaleImage)
        self.add_output("result", GrayScaleImage)

    def compute(self, inputs: dict[UUID, Any]) -> dict[UUID, Any]:
        img1: GrayScaleImage = inputs[self.input_uuids[0]]
        img2: GrayScaleImage = inputs[self.input_uuids[1]]
        if img1.value is None or img2.value is None:
            return {self.output_uuids[0]: None}

        res = cv.absdiff(img1.value, img2.value)
        result = GrayScaleImage(res)
        return {self.output_uuids[0]: result}


class AddDiffNode(Node):
    """Adds brightness to an image based on manual or connected value."""
    def __init__(self, name: str):
        super().__init__(name)
        self.add_input("image 1", GrayScaleImage)
        self.add_input("image 2", GrayScaleImage)
        self.add_output("result 1", GrayScaleImage)
        self.add_output("result 2", GrayScaleImage)

    def compute(self, inputs: dict[UUID, Any]) -> dict[UUID, Any]:
        img1: GrayScaleImage = inputs[self.input_uuids[0]]
        img2: GrayScaleImage = inputs[self.input_uuids[1]]
        if img1.value is None or img2.value is None:
            return {self.output_uuids[0]: None}

        res1 = cv.add(img1.value, img2.value)
        res2 = cv.subtract(img1.value, img2.value)
        result1 = GrayScaleImage(res1)
        result2 = GrayScaleImage(res2)
        return {self.output_uuids[0]: result1, self.output_uuids[1]: result2}


if __name__ == "__main__":
    from PySide6.QtCore import QCoreApplication
    app = QCoreApplication([])

    graph = Graph()
    img = cv.imread("/home/tim/Documents/Arbeit/HDF5Test/SO298_298-10-1_PISCO2_20230422-2334_Results/Images/SO298_298-10-1_PISCO2_0010.21dbar-00.00S-100.95W-22.96C_20230422-23334875.png",
              cv.IMREAD_GRAYSCALE)
    img_node = ImageInputNode("Input", GrayScaleImage(img))
    # invert_node = InvertImageNode("Invert")
    # bright_node = BrightnessNode("Brighten")
    img_node2 = ImageInputNode("Input 2", GrayScaleImage(img))
    absdiff_node = ABSDiffNode("ABSDiff")
    adddiff_node = AddDiffNode("AddDiff")

    graph.add_node(img_node)
    graph.add_node(img_node2)
    graph.add_node(absdiff_node)
    graph.add_node(adddiff_node)
    # graph.add_node(bright_node)

    output_socket_uuid = list(img_node.outputs.keys())[0]

    graph.connect_sockets_by_idx(img_node, 0, adddiff_node, 0)
    graph.connect_sockets_by_idx(img_node2, 0, adddiff_node, 1)
    graph.connect_sockets_by_idx(adddiff_node, 0, absdiff_node, 0)
    graph.connect_sockets_by_idx(adddiff_node, 1, absdiff_node, 1)

    # graph.connect_sockets_by_idx(img_node, 0, invert_node, 0)
    # graph.connect_sockets_by_idx(invert_node, 0, bright_node, 0)

    # Set a manual input value (brightness)
    # bright_node.inputs[bright_node.input_uuids[1]].set_manual_value(20.0)
    # bright_node.data_changed.connect(lambda: print("Bright node output changed"))

    # Evaluate lazily
    result = graph.evaluate(absdiff_node, absdiff_node.output_uuids[0])
    cv.imshow("result", result.value)
    cv.waitKey()

    # Trigger automatic signal propagation by changing input
    # img_node.image = GrayScaleImage(img + 100)
    # img_node.data_changed.emit()  # manually notify (GUI would do this)

    # Re-evaluate
    # result = graph.evaluate(bright_node, bright_node.output_uuids[0])
    # cv.imshow("result", result.value)
    # cv.waitKey()
