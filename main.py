import sys
from PyQt5.QtWidgets import QApplication
import qdarkstyle
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()