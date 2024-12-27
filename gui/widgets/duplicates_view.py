from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QMessageBox, QHeaderView
from PyQt5.QtCore import Qt
import datetime
import os

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duplicate_files = {}
        self.setup_ui()
        
    def setup_ui(self):

        self.setWindowTitle('Archivos Duplicados')

        # Crear un QTableWidget con 4 columnas
        self.table_widget = QTableWidget(self)
        self.table_widget.setRowCount(0)  # Inicialmente no hay filas
        self.table_widget.setColumnCount(4)  # Cuatro columnas: Nombre, Ruta, Tamaño, Fecha
        self.table_widget.setHorizontalHeaderLabels(['Nombre', 'Ruta', 'Tamaño', 'Fecha'])

        # Ajustar el tamaño de las columnas
        header = self.table_widget.horizontalHeader()
        header.setMaximumSectionSize(500)  

        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  
        header.setSectionResizeMode(3, QHeaderView.Stretch) 
        
        # self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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
        for hash_val, data in self.duplicate_files.items():
            files = data['files']
            for file in files:
                row_position = self.table_widget.rowCount()
                self.table_widget.insertRow(row_position)

                # Insertar los datos del archivo en las celdas correspondientes
                self.table_widget.setItem(row_position, 0, QTableWidgetItem(file['name']))
                self.table_widget.setItem(row_position, 1, QTableWidgetItem(file['path']))
                self.table_widget.setItem(row_position, 2, SizeTableWidgetItem(file['size']))
                self.table_widget.setItem(row_position, 3, DateTableWidgetItem(file['date']))
        
        self.table_widget.setSortingEnabled(True)
        self.table_widget.sortItems(2, Qt.DescendingOrder)  # 2 es la columna "size", y ordenamos de mayor a menor

        # Agregar comportamiento al hacer clic en las cabeceras de las columnas
        self.table_widget.setHorizontalHeaderLabels(["Nombre", "Ruta", "Tamaño", "Fecha"])
        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
    
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
        if confirmation == QMessageBox.Yes:
            # Eliminar los archivos seleccionados
            for row in selected_rows:
                file_path = self.table_widget.item(row.row(), 1).text()
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        self.table_widget.setRowCount(0)
                        self.table_widget.clearContents()
                        # Eliminar el archivo de la lista de duplicados
                        self.duplicate_files = self.remove_file_from_duplicates(file_path)
                        self.populate_table(self.duplicate_files)

                    except Exception as e:
                        QMessageBox.warning(self, 'Error', f'No se pudo eliminar el archivo: {e}')
                    
                else:
                    QMessageBox.warning(self, 'Error', f'El archivo no existe: {file_path}')

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
    
    def get_duplicate_files(self):
        return self.duplicate_files
