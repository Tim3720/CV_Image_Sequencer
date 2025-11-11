import os
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QImage
import cv2 as cv
from cv2.typing import MatLike

from ..core.types import ColorImage, GrayScaleImage

class SourceManager(QObject):
    frame_ready = Signal(ColorImage)

    def __init__(self):
        super().__init__()

        self.timer = QTimer()
        self.timer.timeout.connect(self.get_frame)

        self.video_mode: bool = True

        self.video_capture = None
        self.image_directory = None
        self.image_files = []

        self.current_frame_idx: int = 0
        self.current_frame = None
        self.n_frames: int = 0
        self.loop_mode: bool = True

    def get_number_of_frames(self):
        return self.n_frames

    def get_frame(self, offset: int = 1, grayscale: bool = False):
        new_index = self.current_frame_idx + offset
        if new_index < 0:
            return
        if self.loop_mode and new_index >= self.n_frames: # loop mode
            new_index = 0
        self.current_frame_idx = new_index

        if self.video_mode:
            if self.video_capture is None:
                return 

            self.video_capture.set(cv.CAP_PROP_POS_FRAMES, new_index)

            ret, frame = self.video_capture.read()
            if not ret:
                return self.stop()
            if grayscale:
                frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        else:
            if self.image_directory is None:
                return
            if grayscale:
                frame = cv.imread(os.path.join(self.image_directory,
                                           self.image_files[self.current_frame_idx]),
                                  cv.IMREAD_GRAYSCALE)
            else:
                frame = cv.imread(os.path.join(self.image_directory,
                                           self.image_files[self.current_frame_idx]))

        self.current_frame = frame
        self.frame_ready.emit(ColorImage(value=frame))

    def get_next_n_frames(self, n, offset: int = 0, grayscale: bool = False):
        indices = []
        for i in range(n):
            new_index = self.current_frame_idx + i + offset
            if new_index < 0:
                return
            if self.loop_mode and new_index >= self.n_frames: # loop mode
                new_index = 0
            indices.append(new_index)

        output = []
        if self.video_mode:
            if self.video_capture is None:
                return 
            for index in indices:
                self.video_capture.set(cv.CAP_PROP_POS_FRAMES, index)
                ret, frame = self.video_capture.read()
                if not ret:
                    self.stop()
                    return
                if grayscale:
                    frame = GrayScaleImage(value=cv.cvtColor(frame, cv.COLOR_BGR2GRAY))
                else:
                    frame = ColorImage(value=frame)
                output.append(frame)
            self.video_capture.set(cv.CAP_PROP_POS_FRAMES, self.current_frame_idx)
        else:
            if self.image_directory is None:
                return
            for index in indices:
                if grayscale:
                    frame = GrayScaleImage(value=cv.imread(os.path.join(self.image_directory,
                                               self.image_files[index]),
                                      cv.IMREAD_GRAYSCALE))
                else:
                    frame = ColorImage(value=cv.imread(os.path.join(self.image_directory,
                                               self.image_files[index])))
                output.append(frame)
        return output


    def emit_frame(self):
        if self.current_frame is not None:
            self.frame_ready.emit(ColorImage(value=self.current_frame))

    def get_current_frame(self) -> ColorImage:
        return ColorImage(value=self.current_frame)

    def stop(self):
        self.timer.stop()

    def start(self, interval=30):
        if self.video_capture and self.video_capture.isOpened():
            self.timer.start(interval)
        elif not self.image_directory is None:
            self.timer.start(interval)

    def load_video(self, path: str):
        try:
            self.video_capture = cv.VideoCapture(path)
            if not self.video_capture.isOpened():
                self.video_capture.release()
                self.video_capture = None
                # TODO: Warning
                return 

            self.n_frames = int(self.video_capture.get(cv.CAP_PROP_FRAME_COUNT))
            self.video_mode = True
            self.get_frame()
        except Exception as e:
            print(e)
            pass

    def _check_img_file_type(self, file: str) -> bool:
        if file.endswith(".png") or file.endswith(".jpg") or file.endswith(".tiff"):
            return True
        return False

    def load_directory(self, path: str):
        if not os.path.isdir(path):
            raise ValueError("Invalid path: No directory")
        try:
            files = [f for f in os.listdir(path) if self._check_img_file_type(f)]
            if not files:
                raise ValueError("No valid image files could be found in the directory.")
            self.image_directory = path
            self.image_files = files
            self.video_mode = False
            self.n_frames = len(files)
            self.get_frame()
        except Exception as e:
            print(e)
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
