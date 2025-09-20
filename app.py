import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """
    Main function to run the application.
    """
    app = QApplication(sys.argv)
    
    # Create an instance of the main window
    main_window = MainWindow()

    app.setStyle("Fusion")
    dark_stylesheet = """
        QWidget {
            background-color: #2b2b2b;
            color: #f0f0f0;
            font-size: 14px;
        }
        QMainWindow {
            background-color: #2b2b2b;
        }
        QFrame, QWidget#WorkflowWidget, QWidget#FrameTabWidget {
            background-color: #333333;
            border: 1px solid #444444;
        }
        QTabWidget::pane {
            border: 1px solid #444444;
        }
        QTabBar::tab {
            background-color: #3d3d3d;
            color: #f0f0f0;
            padding: 8px 16px;
            border-top: 1px solid #444444;
            border-left: 1px solid #444444;
            border-right: 1px solid #444444;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #2b2b2b;
            border-top: 2px solid #5d85c7;
            border-bottom: none;
        }
        QTabBar::tab:!selected {
            background-color: #3d3d3d;
        }
        QMenuBar {
            background-color: #333333;
            color: #f0f0f0;
        }
        QMenuBar::item {
            background-color: transparent;
        }
        QMenuBar::item:selected {
            background-color: #555555;
        }
        QMenu {
            background-color: #333333;
            border: 1px solid #555555;
        }
        QMenu::item {
            padding: 5px 20px 5px 20px;
            color: #f0f0f0;
        }
        QMenu::item:selected {
            background-color: #555555;
        }
    """
    app.setStyleSheet(dark_stylesheet)

    main_window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
