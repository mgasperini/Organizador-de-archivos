from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtGui import QIcon

class NavigationBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        self.home_button = QPushButton(QIcon("Assets/home.svg"), "")
        self.back_button = QPushButton(QIcon("Assets/flecha-pequena-izquierda.svg"), "")
        self.forward_button = QPushButton(QIcon("Assets/Adelante.svg"), "")
        self.up_button = QPushButton(QIcon("Assets/arriba.svg"), "")
        self.select_folder_button = QPushButton("Seleccionar Carpeta")
        self.date_view_button = QPushButton("Ver por Fechas")
        self.to_original_button = QPushButton("Vista Actual a Original")
        
        layout.addWidget(self.home_button)
        layout.addWidget(self.back_button)
        layout.addWidget(self.forward_button)
        layout.addWidget(self.up_button)
        layout.addWidget(self.select_folder_button)
        layout.addWidget(self.date_view_button)
        layout.addWidget(self.to_original_button)
        layout.addStretch()