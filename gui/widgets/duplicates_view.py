from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QMessageBox, QHeaderView
from PyQt5.QtCore import Qt
import datetime
import os
import platform
import subprocess
from send2trash import send2trash

class SizeTableWidgetItem(QTableWidgetItem):
    def __init__(self, size_in_bytes):
        size_text = f"{int(size_in_bytes/1024)} KB"  # Convert to KB
        super().__init__(size_text)
        self.size_in_bytes = size_in_bytes

    def __lt__(self, other):
        return self.size_in_bytes < other.size_in_bytes
    
class DateTableWidgetItem(QTableWidgetItem):
    def __init__(self, date: datetime.datetime):
        date_text = date.strftime('%Y-%m-%d %H:%M:%S')
        super().__init__(date_text)
        self.timestamp = date.timestamp()

    def __lt__(self, other):
        return self.timestamp < other.timestamp

class DuplicatesView(QWidget):
    name = "DuplicatesView"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duplicate_files = {}
        self.setup_ui()
        
    def setup_ui(self):

        self.setWindowTitle('Archivos Duplicados')

        # Crear un QTableWidget con 4 columnas
        self.table_widget = QTableWidget(self)
        self.table_widget.setRowCount(0)  # Inicialmente no hay filas
        self.table_widget.setColumnCount(5)  # Cuatro columnas: Nombre, Ruta, Tamaño, Fecha
        self.table_widget.setHorizontalHeaderLabels(['ID','Nombre', 'Ruta', 'Tamaño', 'Fecha'])

        # Ajustar el tamaño de las columnas
        header = self.table_widget.horizontalHeader()
        header.setMaximumSectionSize(500)  

        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)  
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) 

        # Conectar doble clic en las celdas
        self.table_widget.cellDoubleClicked.connect(self.handle_double_click)
        

        # Llenar la tabla con los archivos duplicados
        self.populate_table(self.duplicate_files)

        # Botón para eliminar los archivos seleccionados
        self.delete_button = QPushButton('Eliminar Seleccionados', self)
        self.delete_button.clicked.connect(self.delete_selected_files)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.table_widget)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)
        self.show()

    def populate_table(self, duplicate_files):

        # Establecer el orden inicial por tamaño de archivo (de mayor a menor)
        self.table_widget.setSortingEnabled(False)  # Deshabilitar temporalmente para evitar que el QTableWidget ordene de inmediato.

        # Agregar los archivos duplicados al QTableWidget
        self.duplicate_files = duplicate_files
        self.table_widget.setRowCount(0) #Limpia la tabla

        # Asignar un ID único a cada grupo de duplicados
        group_id = 1
        for hash_val, data in self.duplicate_files.items():
            files = data['files']
            if len(files) < 2:  # Omitir grupos con menos de 2 archivos
                continue

            for file in files:
                row_position = self.table_widget.rowCount()
                self.table_widget.insertRow(row_position)

                # Insertar los datos del archivo en las celdas correspondientes
                self.table_widget.setItem(row_position, 0, QTableWidgetItem(str(group_id)))  # ID de duplicado
                self.table_widget.setItem(row_position, 1, QTableWidgetItem(file['name']))
                self.table_widget.setItem(row_position, 2, QTableWidgetItem(file['path']))
                self.table_widget.setItem(row_position, 3, SizeTableWidgetItem(file['size']))
                self.table_widget.setItem(row_position, 4, DateTableWidgetItem(file['date']))
            
            group_id += 1
        
        self.table_widget.setSortingEnabled(True)
        self.table_widget.sortItems(3, Qt.DescendingOrder)  # 3 es la columna "size", y ordenamos de mayor a menor

        # Agregar comportamiento al hacer clic en las cabeceras de las columnas
        self.table_widget.setHorizontalHeaderLabels(["ID","Nombre", "Ruta", "Tamaño", "Fecha"])
        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
    
    def handle_double_click(self, row, column):
        """Abrir el archivo si se hace doble clic en la columna de Ruta."""
        if column == 2:  # Columna de Ruta
            file_path = self.table_widget.item(row, column).text()
            if os.path.exists(file_path):
                try:
                    if platform.system() == "Windows":
                        os.startfile(file_path)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", file_path])
                    else:  # Linux y otros
                        subprocess.run(["xdg-open", file_path])
                except Exception as e:
                    QMessageBox.warning(self, 'Error', f'No se pudo abrir el archivo: {e}')
            else:
                QMessageBox.warning(self, 'Error', 'El archivo no existe.')

    def sort_table(self, index):
        """
        Ordena la tabla de acuerdo a la columna seleccionada.
        Si ya está ordenada en ese sentido, se invierte el orden.
        """
        current_order = self.table_widget.horizontalHeader().sortIndicatorOrder()

        if current_order == Qt.AscendingOrder:
            new_order = Qt.DescendingOrder
        else:
            new_order = Qt.AscendingOrder
        
        self.table_widget.sortItems(index, new_order)


    def delete_selected_files(self):
        # Obtener las filas seleccionadas
        selected_rows = self.table_widget.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, 'Advertencia', 'No se ha seleccionado ningún archivo para eliminar.')
            return

        # Mostrar un mensaje de confirmación
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Confirmar eliminación')
        msg_box.setText('¿Está seguro de que desea eliminar los archivos seleccionados?')
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.button(QMessageBox.Yes).setText('Sí')

        confirmation = msg_box.exec()
        if confirmation != QMessageBox.Yes:
            return
        
        file_paths = [self.table_widget.item(row.row(), 2).text() for row in selected_rows]

        # Intentar eliminar los archivos
        for file_path in file_paths:
            if os.path.exists(file_path):
                try:
                    # Normalizar la ruta
                    normalized_path = os.path.abspath(os.path.normpath(file_path))
                    # print(platform.system())

                    # Agregar prefijo para rutas largas en Windows
                    if platform.system() == "Windows" and len(normalized_path) > 260:
                        normalized_path = f"\\\\?\\{normalized_path}"

                    # os.remove(file_path)
                    send2trash(file_path.replace('/','\\'))  # Mover a la papelera
                except Exception as e:
                    QMessageBox.warning(self, 'Error', f'No se pudo eliminar el archivo: {e}')
            else:
                QMessageBox.warning(self, 'Error', f'El archivo no existe: {file_path}')

            # Eliminar los archivos de la lista de duplicados
        for file_path in file_paths:
            self.duplicate_files = self.remove_file_from_duplicates(file_path)
        
        self.populate_table(self.duplicate_files)

           
    def remove_file_from_duplicates(self, file_path):
            """Elimina un archivo de la lista de duplicados."""
            new_duplicate_files = self.duplicate_files.copy()

            for hash_val, data in new_duplicate_files.items():
                seen_paths = set()
                unique_files = []

                for file in data['files']:
                    if file['path'] not in seen_paths:
                        # Si no hemos visto este path, lo agregamos a la lista y al conjunto
                        seen_paths.add(file['path'])
                        if file['path'] != file_path:
                            unique_files.append(file)

                if unique_files:
                    data['files'] = unique_files
                else:
                    # Si no quedan archivos con ese hash, eliminar la entrada
                    del new_duplicate_files[hash_val]

            return new_duplicate_files
    
    def update_root_index(self):
        """Actualiza la vista cuando se cambia el directorio."""
        self.populate_table(self.duplicate_files)
    
    def get_duplicate_files(self):
        return self.duplicate_files
