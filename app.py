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
        QTabWidget::pane {
            border: 1px solid #444444;
        }
        QTabBar::tab {
            background-color: #3d3d3d;
            color: #f0f0f0;
            padding: 8px 16px;
        }
        QTabBar::tab:selected {
            background-color: #2b2b2b;
            border-top: 2px solid #5d85c7;
            border-bottom: none;
        }
    """
    app.setStyleSheet(dark_stylesheet)

    main_window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
