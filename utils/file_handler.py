import cv2
from PySide6.QtWidgets import QFileDialog

class FileHandler:
    def __init__(self):
        self.video_capture = None

    def open_video_file_dialog(self):
        """
        Opens a file dialog to select a video file.
        Returns the path of the selected file.
        """
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("Video Files (*.mp4 *.avi *.mov);;All Files (*)")
        if dialog.exec():
            file_paths = dialog.selectedFiles()
            if file_paths:
                return file_paths[0]
        return None

    def load_video(self, video_path):
        """
        Loads a video file and returns the first frame.
        """
        if not video_path:
            return None, "No file path provided."

        self.video_capture = cv2.VideoCapture(video_path)
        
        if not self.video_capture.isOpened():
            return None, "Error: Could not open video file."
        
        ret, frame = self.video_capture.read()
        if not ret:
            self.video_capture.release()
            return None, "Error: Could not read the first frame."
        
        # Release the video capture object after getting the first frame
        self.video_capture.release()
        self.video_capture = None
        
        return frame, None
