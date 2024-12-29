from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QFileDialog
import os
from gui.widgets.navigation_bar import ViewMode
from core.file_scanner import FileScanWorker
from core.file_hash_scanner import FileHashScanWorker

class NavigationController(QObject):
    def __init__(self, navigation_bar, file_organizer_widget):
        super().__init__()
        self.navigation_bar = navigation_bar
        self.file_organizer = file_organizer_widget
        self.current_path = self.file_organizer.current_directory
        self.history = [self.current_path]
        self.history_index = 0
        self.actual_view = self.file_organizer.file_view
        self.hash_scan_thread = None
        self.progress_bar = None
        self.duplicates_view = None
        self.stack_widget = None

        # Conectar la señal de escaneo completado
        if self.actual_view.name == "FileView":
            self.file_organizer.file_view.scan_completed.connect(self._handle_scan_completed)

        # Conectar señales de la barra de navegación
        self.navigation_bar.path_changed.connect(self.handle_path_change)
        self.navigation_bar.directory_selected.connect(self.handle_directory_selected)
        

        # Conectar señales del file_view
        self.actual_view.directory_changed.connect(self.handle_directory_changed)
        self.actual_view.directory_selected.connect(self.handle_directory_selected)
       
       # Nuevas conexiones para cambio de vista
        self.navigation_bar.date_view_button.clicked.connect(self.toggle_date_view)
        self.navigation_bar.file_view_button.clicked.connect(self.toggle_file_view)
        self.file_organizer.view_changed.connect(self._on_view_changed)

        # Conectar botones comunes
        self.navigation_bar.home_button.clicked.connect(self.navigate_home)
        self.navigation_bar.back_button.clicked.connect(self.navigate_back)
        self.navigation_bar.forward_button.clicked.connect(self.navigate_forward)
        self.navigation_bar.up_button.clicked.connect(self.navigate_up)
        # self.navigation_bar.browse_button.clicked.connect(self.select_folder)

        # Conectar botones de las distintas vistas
        # Duplicados
        self.navigation_bar.duplicates_button.clicked.connect(self.toggle_duplicate_view)

        # Conectar botones del sidebar
        self.file_organizer.sidebar.reorganize_button.clicked.connect(self.toggle_file_view)
        self.file_organizer.sidebar.duplicates_button.clicked.connect(self.toggle_duplicate_view)

        # File view connections
        self.file_organizer.file_view.file_list.doubleClicked.connect(self.navigate_directory)

    def toggle_date_view(self):
        """Alternar entre vista de archivos y vista de fecha"""
        current_widget = self.file_organizer.stack_widget.currentWidget()
        
        if current_widget == self.file_organizer.file_view:
            # Cambiar a vista de fecha
            self.actual_view = self.file_organizer.date_view
            self.navigation_bar.update_view(ViewMode.DATE)
            self.file_organizer.file_view.start_date_scan(self.history[self.history_index])

        else:
            # Cambiar a vista de archivos
            self.actual_view = self.file_organizer.file_view
            self.file_organizer.change_view(self.file_organizer.file_view)
            self.navigation_bar.update_view(ViewMode.NORMAL)

    def toggle_file_view(self):
        """Cambia a la vista de archivos"""
        current_widget = self.file_organizer.stack_widget.currentWidget()
        
        if current_widget != self.file_organizer.file_view:
            # Cambiar a vista de archivos
            self.actual_view = self.file_organizer.file_view
            self.file_organizer.change_view(self.file_organizer.file_view)
            self.navigation_bar.update_view(ViewMode.NORMAL)
            self.actual_view.update_root_index(self.history[self.history_index])
            
    def toggle_duplicate_view(self):
        """Cambia a la vista de archivos duplicados"""
        current_widget = self.file_organizer.stack_widget.currentWidget()
        
        if current_widget != self.file_organizer.duplicates_view:
            # Cambiar a vista de archivos
            self.actual_view = self.file_organizer.duplicates_view
            self.file_organizer.change_view(self.file_organizer.duplicates_view)
            self.navigation_bar.update_view(ViewMode.DUPLICATES)
            self.show_duplicate_view(self.file_organizer.progress_bar, self.file_organizer.duplicates_view, self.file_organizer.stack_widget)

    def show_duplicate_view(self, progress_bar, duplicates_view, stack_widget):
        """
        Maneja la lógica de mostrar la vista de duplicados y ejecutar el escaneo.
        
        Args:
            progress_bar: QProgressBar para mostrar el progreso
            duplicates_view: Vista de duplicados
            stack_widget: Widget contenedor principal
        """
        self.progress_bar = progress_bar
        self.duplicates_view = duplicates_view
        self.stack_widget = stack_widget
        
        current_directory = self.history[self.history_index]
        
        # Configurar UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Limpiar thread anterior
        if self.hash_scan_thread and self.hash_scan_thread.isRunning():
            self.hash_scan_thread.wait()
            
        # Iniciar nuevo escaneo
        self.hash_scan_thread = FileHashScanWorker(current_directory)
        self.hash_scan_thread.progress.connect(self.progress_bar.setValue)
        self.hash_scan_thread.finished.connect(self._populate_duplicate_view)
        self.hash_scan_thread.start()
    
    def _populate_duplicate_view(self, duplicate_files):
        """
        Callback privado para poblar la vista de duplicados cuando termina el escaneo.
        
        Args:
            duplicate_files: Lista de archivos duplicados encontrados
        """
        self.duplicates_view.populate_table(duplicate_files)
        self.progress_bar.setVisible(False)
        self.stack_widget.setCurrentWidget(self.duplicates_view)

    def show_date_view(self):
        self.actual_view = self.file_organizer.date_view
        self.navigation_bar.update_view(view_mode=ViewMode.DATE)
        self.file_organizer.progress_bar.setVisible(True)
        self.file_organizer.progress_bar.setValue(0)
        # Limpiar thread anterior si existe
        if hasattr(self, 'scan_thread') and self.scan_thread is not None:
            if self.scan_thread.isRunning():
                self.scan_thread.wait()  # Esperar a que termine
        self.scan_thread = FileScanWorker(self.history[self.history_index])
        self.scan_thread.progress.connect(self.file_organizer.progress_bar.setValue)
        self.scan_thread.finished.connect(self.populate_date_view)
        self.scan_thread.start()

    def populate_date_view(self, files_by_date):
        self.file_organizer.date_view.populate_tree(files_by_date)
        self.file_organizer.progress_bar.setVisible(False)
        self.file_organizer.stack_widget.setCurrentWidget(self.file_organizer.date_view)

    def _on_view_changed(self, view_widget):
        """Manejar cambios en la vista actual"""
        if view_widget == self.file_organizer.file_view:
            self.navigation_bar.update_view(ViewMode.NORMAL)
        elif view_widget == self.file_organizer.date_view:
            self.navigation_bar.update_view(ViewMode.DATE)
        elif view_widget == self.file_organizer.duplicates_view:
            self.navigation_bar.update_view(ViewMode.DUPLICATES)
        else:
            self.navigation_bar.update_view(ViewMode.NORMAL)

    def _handle_scan_completed(self, files_by_date):
        """Manejar cuando el escaneo de archivos se completa"""
        self.file_organizer.date_view.populate_tree(files_by_date)
        self.file_organizer.change_view(self.file_organizer.date_view)
    
    def select_folder(self):
        new_folder = QFileDialog.getExistingDirectory(
            None, 
            "Seleccionar Carpeta",
            self.current_path
        )
        if new_folder:
            self.navigate_to(new_folder)
            return new_folder
        return None
    

    @pyqtSlot(str)
    def handle_path_change(self, new_path):
        """Manejar cambios en la ruta introducida manualmente"""
        if os.path.exists(new_path):
            self.navigate_to(new_path)
    
    @pyqtSlot(str)
    def handle_directory_selected(self, directory):
        """Manejar la selección de directorio desde el diálogo"""
        self.navigate_to(directory)

    @pyqtSlot(str)
    def handle_directory_changed(self, new_path):
        """Manejar cambios de directorio desde el FileView"""
        self.navigate_to(new_path)
    
    
    def navigate_to(self, path, update_history=True):
        """Navegar a una nueva ruta y actualizar el historial"""
        
        if os.path.exists(path):
            self.current_path = path
            # print("Antes",self.history, self.history_index)
            if update_history:
                self.update_history(path)
            # print("Despues",self.history, self.history_index)
            self.navigation_bar.update_path_display(path)
            #print("Directorio",self.history[self.history_index], self.current_path == self.history[self.history_index],self.actual_view.name)
            # Actualizar la vista
            if self.actual_view.name == "FileView":
                self.actual_view.update_root_index(path)   
            elif self.actual_view.name == "DateView":
                
                self.file_organizer.file_view.start_date_scan(self.current_path)
                self.show_date_view()
            elif self.actual_view.name == "DuplicatesView":
                self.show_duplicate_view(self.progress_bar, self.duplicates_view, self.stack_widget)
            else:
                print("Vista no reconocida")

    def navigate_directory(self, index):
        """Navegar a un directorio basado en un índice del modelo"""
        new_path = self.actual_view.fs_model.filePath(index)
        
        if os.path.isdir(new_path):
            self.navigate_to(new_path)
            return new_path
        return None

    def navigate_up(self):
        """Navegar al directorio padre"""
        parent_dir = os.path.dirname(self.current_path)
        if parent_dir != self.current_path:  # Evitar bucle en la raíz
            
            self.navigate_to(parent_dir)
            return parent_dir
        return None
    
    def navigate_home(self):
        """Navegar al directorio home del usuario"""
        self.navigate_to(os.path.expanduser("~").replace("\\", "/"))
    
    def navigate_back(self):
        """Navegar hacia atrás en el historial"""
        if self.history_index > 0:
            self.history_index -= 1
            self.navigate_to(self.history[self.history_index], False)
    
    def navigate_forward(self):
        """Navegar hacia adelante en el historial"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.navigate_to(self.history[self.history_index], False)
    
    def update_history(self, path):
        """Actualizar el historial de navegación"""
        # Si no estamos al final del historial, truncar la parte futura
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        # Evitar duplicados consecutivos en el historial
        if not self.history or self.history[-1] != path:
            self.history.append(path)
            self.history_index = len(self.history) - 1
        