from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt

class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        
        self.reorganize_button = QPushButton("Reorganizar Archivos")
        self.duplicates_button = QPushButton("Eliminar Duplicados")
        self.duplicates_button.setEnabled(False)
        
        layout.addWidget(self.reorganize_button)
        layout.addWidget(self.duplicates_button)
