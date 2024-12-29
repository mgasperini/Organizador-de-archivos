from PyQt5.QtWidgets import QApplication
import qdarkstyle
from qdarkstyle import LightPalette

class ThemeManager:
    def __init__(self):
        self.dark_mode = True
        self._app = QApplication.instance()
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._update_theme()
    
    def _update_theme(self):
        if self.dark_mode:
            self._app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        else:
            self._app.setStyleSheet(qdarkstyle.load_stylesheet(palette=LightPalette,qt_api='pyqt5'))  # Estilo claro por defecto


    @property
    def is_dark_mode(self):
        return self.dark_mode