from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListView, QProgressBar
from PyQt5.QtCore import QDir, pyqtSignal
from PyQt5.QtWidgets import QFileSystemModel
from core.file_scanner import FileScanWorker

class FileView(QWidget):
    name = "FileView"
    directory_changed = pyqtSignal(str)  # Nueva señal para notificar cambios
    directory_selected = pyqtSignal(str)  # Para la selección de carpeta
    scan_completed = pyqtSignal(dict)  # Nueva señal para notificar cuando el escaneo termina


    def __init__(self, parent=None):
        super().__init__(parent)
        self.scan_thread = None
        self.setup_ui()
        self.initialize_model()

        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.file_list = QListView()
        layout.addWidget(self.file_list)

        # Agregar Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def initialize_model(self):
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(QDir.homePath())
        self.file_list.setModel(self.fs_model)
        self.file_list.setRootIndex(self.fs_model.index(QDir.homePath()))


    def setup_connections(self):
        # Conectar doble click en file_list con la señal de cambio
        self.file_list.doubleClicked.connect(self._on_item_double_clicked)

    def _on_item_double_clicked(self, index):
        """Manejador interno para el doble click en un item"""
        if self.fs_model.isDir(index):
            new_path = self.fs_model.filePath(index)
            self.directory_changed.emit(new_path)

    def start_date_scan(self, directory):
        """Iniciar el escaneo de archivos por fecha"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Limpiar thread anterior si existe
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.wait()
        
        # Iniciar nuevo escaneo
        self.scan_thread = FileScanWorker(directory)
        self.scan_thread.progress.connect(self.progress_bar.setValue)
        self.scan_thread.finished.connect(self._handle_scan_completed)
        self.scan_thread.start()

    def _handle_scan_completed(self, files_by_date):
        """Manejador interno para cuando termina el escaneo"""
        self.progress_bar.setVisible(False)
        self.scan_completed.emit(files_by_date)
    
    def update_root_index(self, directory):
        """Método público para actualizar el directorio mostrado"""
        self.file_list.setRootIndex(self.fs_model.index(directory))
        

