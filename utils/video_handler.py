from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QImage
import cv2 as cv
from cv2.typing import MatLike
import numpy as np

class VideoManager(QObject):
    frame_ready = Signal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.video_capture = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.get_frame)
        self.current_frame_idx: int = 0
        self.current_frame = None
        self.n_frames: int = 0
        self.loop_mode: bool = True

    def get_frame(self, offset: int = 1):
        if self.video_capture is None:
            return 

        new_index = self.current_frame_idx + offset
        if self.loop_mode and new_index >= self.n_frames: # loop mode
            new_index = 0

        self.video_capture.set(cv.CAP_PROP_POS_FRAMES, new_index)
        self.current_frame_idx = new_index

        ret, frame = self.video_capture.read()
        if not ret:
            return self.stop()
        self.current_frame = frame
        self.frame_ready.emit(frame)

    def get_current_frame(self) -> MatLike | None:
        return self.current_frame

    def stop(self):
        self.timer.stop()

    def start(self, interval=30):
        if self.video_capture and self.video_capture.isOpened():
            self.timer.start(interval)

    def load_video(self, path: str):
        try:
            self.video_capture = cv.VideoCapture(path)

            if not self.video_capture.isOpened():
                self.video_capture.release()
                self.video_capture = None
                # TODO: Warning
                return 

            ret, preview = self.video_capture.read()
            if not ret:
                self.video_capture.release()
                self.video_capture = None
                return 

            self.frame_ready.emit(preview)

            self.video_capture.set(cv.CAP_PROP_POS_FRAMES, 0)
            self.n_frames = int(self.video_capture.get(cv.CAP_PROP_FRAME_COUNT))
            self.current_frame_idx = 0
        except:
            pass

def convert_cv_to_qt(image: MatLike) -> QImage:
    if image.ndim == 2: # grayscale
        h, w = image.shape
        return QImage(image.data, w, h, w, QImage.Format.Format_Grayscale8)
    elif image.shape[2] == 3:
        h, w, ch = image.shape
        rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        return QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
    else:
        raise ValueError("Unsupported image format")
