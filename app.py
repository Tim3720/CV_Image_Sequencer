import sys
from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget
from CV_Image_Sequencer_Lib import CVImageSequencerWidget

def main():
    """
    Main function to run the application.
    """
    app = QApplication(sys.argv)
    
    # Create an instance of the main window
    main_window = QMainWindow()
    main_window.setWindowTitle("CV Image Sequencer")
    main_window.setGeometry(0, 0, 1920, 1080)
    # main_window.setGeometry(330, 60, 1260, 960)

    central_widget = CVImageSequencerWidget()
    main_window.setCentralWidget(central_widget)


    app.setStyle("Fusion")
    with open("./CV_Image_Sequencer_Lib/assets/styles/dark.qss", "r") as f:
        app.setStyleSheet(f.read())

    main_window.show()

    central_widget.video_manager.load_video("/home/tim/Documents/Arbeit/BloodCellsProject/Data/RT_MitotrackOrange_Hoechst_KH7_01202022.avi")
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
