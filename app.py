import sys
from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget
from CV_Image_Sequencer_Lib import CVImageSequencerWidget
from CV_Image_Sequencer_Lib.assets.styles.style import DARK, LIGHT, STYLE
from CV_Image_Sequencer_Lib.ui import main_window
from pathlib import Path

USE_DARK = True

def main():
    """
    Main function to run the application.
    """
    app = QApplication(sys.argv)
    
    # Create an instance of the main window
    main_window = QMainWindow()
    main_window.setWindowTitle("CV Image Sequencer")
    main_window.setGeometry(0, 0, 1920, 1080)
    main_window.setFixedSize(1920, 1080)
    # main_window.setGeometry(330, 60, 1260, 960)


    app.setStyle("Fusion")
    if USE_DARK:
        for key in DARK:
            STYLE[key] = DARK[key]
        qss = Path("./CV_Image_Sequencer_Lib/assets/styles/dark_style.qss").read_text()
        app.setStyleSheet(qss)
    else:
        for key in LIGHT:
            STYLE[key] = LIGHT[key]
        qss = Path("./CV_Image_Sequencer_Lib/assets/styles/light_style.qss").read_text()
        app.setStyleSheet(qss)

    central_widget = CVImageSequencerWidget(app)
    main_window.setCentralWidget(central_widget)

    main_window.show()

    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
