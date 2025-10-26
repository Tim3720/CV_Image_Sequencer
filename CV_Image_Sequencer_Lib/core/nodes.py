from .node_base import Node, InPut, OutPut
from ..core.workflows import ABSDiff, ChannelSplit, ClampedDiff, GetFrame, GetFrameGray, GrayScale, Invert3C, Max, Min, Threshold
from ..utils.source_manager import SourceManager
from ..utils.types import (Bool, ColorCode3C21C, Float, Image1C, Image3C, Int, ThresholdTypes)
import uuid


class SourceNode(Node):
    def __init__(self, source_manager: SourceManager, n_frames: int = 1, id: str = "") -> None:
        workflow = GetFrame(source_manager, n_frames)
        outputs = []
        self.id = id if id else str(uuid.uuid4())
        for _ in range(n_frames):
            outputs.append(OutPut("Frame", Image3C(), self.id, True))
        super().__init__(
            [
                InPut("Offset", Int(value=0), self.id, False),
            ],
            outputs, "Source", workflow, self.id
        )
        source_manager.frame_ready.connect(self.run_workflow)

        self.help_text = """
# SourceNode
The **source node** outputs *n_frames* frames from the source.  
The *offset* parameter can be used to set a constant offset to the currently shown source image.

For example:
- *offset = 1* → shows *n_frames* images starting at index *current_source_index + 1*.
        """



class GrayScaleSourceNode(Node):
    def __init__(self, source_manager: SourceManager, n_frames: int = 1, id: str = "") -> None:
        self.id = id if id else str(uuid.uuid4())
        workflow = GetFrameGray(source_manager, n_frames)
        outputs = []
        for _ in range(n_frames):
            outputs.append(OutPut("Frame", Image1C(), self.id, True))
        super().__init__(
            [
                InPut("Offset", Int(value=0), self.id, False),
            ],
            outputs, "GrayScaleSource", workflow,
            self.id
        )
        source_manager.frame_ready.connect(self.run_workflow)


class GrayScaleNode(Node):
    def __init__(self, id: str = "") -> None:
        self.id = id if id else str(uuid.uuid4())
        workflow = GrayScale()
        super().__init__(
            [
                InPut("RGB", Image3C(), self.id, True),
                InPut("ColorCode", ColorCode3C21C(), self.id, False)
            ],
            [OutPut("Gray", Image1C(), self.id, True)],
            "GrayScale",
            workflow,
            self.id
        )


class ThresholdNode(Node):
    def __init__(self, id: str = "") -> None:
        self.id = id if id else str(uuid.uuid4())
        workflow = Threshold()
        super().__init__(
            [
                InPut("Image", Image1C(), self.id, True),
                InPut("Threshold value", Float(value=100, min_value=0, max_value=255),
                      self.id, False),
                InPut("New Value", Float(value=255, min_value=0, max_value=255), self.id, False),
                InPut("Threshold Type", ThresholdTypes(), self.id, False),
            ],
            [
                OutPut("Threshold", Float(min_value=0, max_value=255), self.id, False),
                OutPut("Image", Image1C(), self.id, True),
            ],
            "Threshold",
            workflow,
            self.id
        )


class ChannelSplitNode(Node):
    def __init__(self, id: str = "") -> None:
        self.id = id if id else str(uuid.uuid4())
        workflow = ChannelSplit()
        super().__init__(
            [
                InPut("Image", Image3C(), self.id, True),
            ],
            [
                OutPut("Blue", Image1C(), self.id, True),
                OutPut("Green", Image1C(), self.id, True),
                OutPut("Red", Image1C(), self.id, True),
            ],
            "ChannelSplit",
            workflow,
            self.id
        )

class ABSDiffNode(Node):
    def __init__(self, id: str = "") -> None:
        self.id = id if id else str(uuid.uuid4())
        workflow = ABSDiff()
        super().__init__(
            [
                InPut("Image1", Image1C(), self.id, True),
                InPut("Image2", Image1C(), self.id, True),
            ],
            [
                OutPut("Diff", Image1C(), self.id, True),
            ],
            "ABSDiff",
            workflow,
            self.id
        )

class ClampedDiffNode(Node):
    def __init__(self, id: str = "") -> None:
        self.id = id if id else str(uuid.uuid4())
        workflow = ClampedDiff()
        super().__init__(
            [
                InPut("Image1", Image1C(), self.id, True),
                InPut("Image2", Image1C(), self.id, True),
                InPut("Cutoff", Int(value=0, min_value=0, max_value=255), self.id, False),
            ],
            [
                OutPut("Diff", Image1C(), self.id, True),
            ],
            "ClampedDiff",
            workflow,
            self.id
        )

class Invert3CNode(Node):
    def __init__(self, id: str = "") -> None:
        self.id = id if id else str(uuid.uuid4())
        workflow = Invert3C()
        super().__init__(
            [
                InPut("Image", Image3C(), self.id, True),
            ],
            [
                OutPut("Inverted", Image3C(), self.id, True),
            ],
            "Invert",
            workflow,
            self.id
        )


class MinNode(Node):
    def __init__(self, id: str = "") -> None:
        self.id = id if id else str(uuid.uuid4())
        workflow = Min()
        super().__init__(
            [
                InPut("Image1", Image1C(), self.id, True),
                InPut("Image2", Image1C(), self.id, True),
            ],
            [
                OutPut("Min", Image1C(), self.id, True),
            ],
            "Min",
            workflow,
            self.id
        )


class MaxNode(Node):
    def __init__(self, id: str = "") -> None:
        self.id = id if id else str(uuid.uuid4())
        workflow = Max()
        super().__init__(
            [
                InPut("Image1", Image1C(), self.id, True),
                InPut("Image2", Image1C(), self.id, True),
            ],
            [
                OutPut("Max", Image1C(), self.id, True),
            ],
            "Max",
            workflow,
            self.id
        )
