import sys
import qdarkstyle
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, 
    QComboBox, QFileDialog, QListView, QStackedWidget, QProgressBar, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt, QDir, QThread, pyqtSignal, QModelIndex, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileSystemModel
import os
import datetime
import re
import shutil  # Para mover archivos físicamente



class FileMetadata:
    @staticmethod
    def get_file_date(file_path):
        if file_path.lower().endswith(('.jpg', '.jpeg')):
            try:
                from PIL import Image, ExifTags
                with Image.open(file_path) as img:
                    exif = img.getexif()
                    if exif:
                        for tag_id in (36867, 306, 36868):  # DateTimeOriginal, DateTime, DateTimeDigitized
                            if tag_id in exif:
                                date_str = exif[tag_id]
                                try:
                                    return datetime.datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                                except ValueError:
                                    pass
            except Exception:
                pass
        return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

class ScanWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        files_by_date = {}
        total_files = sum([len(files) for _, _, files in os.walk(self.path)])
        processed_files = 0

        for root, _, files in os.walk(self.path):
            rel_path = os.path.relpath(root, self.path)
            if rel_path == '.':
                rel_path = ''

            for file in files:
                full_path = os.path.join(root, file)
                try:
                    date = FileMetadata.get_file_date(full_path)
                    year_month = f"{date.year}/{date.month:02d}"

                    if year_month not in files_by_date:
                        files_by_date[year_month] = {}

                    if rel_path not in files_by_date[year_month]:
                        files_by_date[year_month][rel_path] = []

                    files_by_date[year_month][rel_path].append({
                        'name': file,
                        'path': full_path,
                        'date': date
                    })

                    processed_files += 1
                    if processed_files % 100 == 0:
                        self.progress.emit(int(processed_files * 100 / total_files))

                except Exception as e:
                    print(f"Error processing {full_path}: {e}")

        self.finished.emit(files_by_date)

class FileOrganizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_directory = QDir.homePath()
        self.history = []
        self.history_index = -1
        self.initialize_models()

    def setup_ui(self):
       # self.setStyleSheet(self.get_dark_theme())
        
        self.main_layout = QHBoxLayout(self)

        # Barra lateral
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setAlignment(Qt.AlignTop)

        self.reorganize_button = QPushButton("Reorganizar Archivos")
        self.reorganize_button.clicked.connect(self.reorganize_files)
        self.sidebar_layout.addWidget(self.reorganize_button)

        # Placeholder para futuros botones
        self.duplicates_button = QPushButton("Eliminar Duplicados")
        self.duplicates_button.setEnabled(False)
        self.sidebar_layout.addWidget(self.duplicates_button)

        self.main_layout.addLayout(self.sidebar_layout)

        # Área principal
        self.content_layout = QVBoxLayout()

        # Barra superior con botones de navegación
        self.top_bar_layout = QHBoxLayout()

        self.home_button = QPushButton()
        self.home_button.setIcon(QIcon("Assets/home.svg"))
        self.home_button.setToolTip("Adelante")
        self.home_button.clicked.connect(self.navigate_home)
        self.top_bar_layout.addWidget(self.home_button)

        self.back_button = QPushButton()
        self.back_button.setIcon(QIcon("Assets/flecha-pequena-izquierda.svg"))
        self.back_button.setToolTip("Volver atrás")
        self.back_button.clicked.connect(self.navigate_back)
        self.top_bar_layout.addWidget(self.back_button)

        self.forward_button = QPushButton()
        self.forward_button.setIcon(QIcon("Assets/Adelante.svg"))
        self.forward_button.setToolTip("Adelante")
        self.forward_button.clicked.connect(self.navigate_forward)
        self.top_bar_layout.addWidget(self.forward_button)

        self.up_button = QPushButton()
        self.up_button.setIcon(QIcon('Assets/arriba.svg'))
        self.up_button.setToolTip("Subir un nivel")
        self.up_button.clicked.connect(self.go_up_directory)
        self.top_bar_layout.addWidget(self.up_button)

        self.select_folder_button = QPushButton("Seleccionar Carpeta")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.top_bar_layout.addWidget(self.select_folder_button)

        self.date_view_button = QPushButton("Ver por Fechas")
        self.date_view_button.clicked.connect(self.toggle_date_view)
        self.top_bar_layout.addWidget(self.date_view_button)

        # Hacer que se active solo con la vista de fechas 
        self.to_original_button = QPushButton("Vista Actual a Original")
        self.to_original_button.clicked.connect(self.reorganize_to_original)
        self.top_bar_layout.addWidget(self.to_original_button)

        self.top_bar_layout.addStretch()
        self.content_layout.addLayout(self.top_bar_layout)

        # Stack de vistas
        self.stack_widget = QStackedWidget()
        self.content_layout.addWidget(self.stack_widget)

        self.main_layout.addLayout(self.content_layout)

        # Vista de reorganización de archivos
        self.reorganize_view = QWidget()
        self.reorganize_layout = QVBoxLayout(self.reorganize_view)

        self.file_list = QListView()
        self.file_list.doubleClicked.connect(self.navigate_directory)
        self.reorganize_layout.addWidget(self.file_list)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.reorganize_layout.addWidget(self.progress_bar)

        self.stack_widget.addWidget(self.reorganize_view)

        # Vista de archivos por fechas
        self.date_view = QWidget()
        self.date_layout = QVBoxLayout(self.date_view)

        self.date_tree = QTreeWidget()
        self.date_tree.setHeaderLabels(["Fecha", "Directorio/Archivo"])
        self.date_tree.setColumnWidth(0,200)
        self.date_layout.addWidget(self.date_tree)

        self.stack_widget.addWidget(self.date_view)

    def initialize_models(self):
        # Modelo de sistema de archivos
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(self.current_directory)
        self.file_list.setModel(self.fs_model)
        self.file_list.setRootIndex(self.fs_model.index(self.current_directory))

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta", self.current_directory)
        if folder:
            self.current_directory = folder
            self.file_list.setRootIndex(self.fs_model.index(self.current_directory))
            self.update_history(folder)

    def navigate_directory(self, index: QModelIndex):
        if self.fs_model.isDir(index):
            new_path = self.fs_model.filePath(index)
            self.current_directory = new_path
            self.file_list.setRootIndex(self.fs_model.index(new_path))
            self.update_history(new_path)

    def go_up_directory(self):
        new_path = os.path.dirname(self.current_directory)
        if os.path.exists(new_path):
            self.current_directory = new_path
            self.file_list.setRootIndex(self.fs_model.index(self.current_directory))
            self.update_history(new_path)

    def navigate_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_directory = self.history[self.history_index]
            self.file_list.setRootIndex(self.fs_model.index(self.current_directory))

    def navigate_home(self):
        self.current_directory = QDir.homePath()
        self.file_list.setRootIndex(self.fs_model.index(self.current_directory))
        self.update_history(self.current_directory)

    def navigate_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_directory = self.history[self.history_index]
            self.file_list.setRootIndex(self.fs_model.index(self.current_directory))

    def update_history(self, new_path):
        # Trim forward history if navigating anew
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(new_path)
        self.history_index = len(self.history) - 1

    def toggle_date_view(self):
        if self.stack_widget.currentWidget() == self.reorganize_view:
            self.show_date_view()
            self.date_view_button.setText("Ver Vista Actual")
        else:
            self.stack_widget.setCurrentWidget(self.reorganize_view)
            self.date_view_button.setText("Ver por Fechas")

    def show_date_view(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.scan_thread = ScanWorker(self.current_directory)
        self.scan_thread.progress.connect(self.progress_bar.setValue)
        self.scan_thread.finished.connect(self.populate_date_view)
        self.scan_thread.start()

    def populate_date_view(self, files_by_date):
        self.date_tree.clear()

        for year_month, directories in sorted(files_by_date.items()):
            year_month_item = QTreeWidgetItem([year_month])
            self.date_tree.addTopLevelItem(year_month_item)

            for directory, files in directories.items():
                dir_item = QTreeWidgetItem([directory])
                year_month_item.addChild(dir_item)

                for file_info in files:
                    file_item = QTreeWidgetItem(["", file_info['path']])
                    dir_item.addChild(file_item)

        self.progress_bar.setVisible(False)
        self.stack_widget.setCurrentWidget(self.date_view)
    
    def reorganize_files(self):

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar reorganización")
        msg_box.setText("Se modificarán los archivos del sistema. ¿Está seguro de continuar?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        yes_button = msg_box.button(QMessageBox.Yes)
        yes_button.setText("Sí")
        confirmation = msg_box.exec()

        current_items = self.date_tree.invisibleRootItem()
        if current_items.childCount() == 0 or confirmation != QMessageBox.Yes:
            return

        month_names = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        removing_folder = os.path.join(self.current_directory) # Guarda la carpeta actual para eliminarla si está vacía

        for i in range(current_items.childCount()):
            year_month_item = current_items.child(i)
            year_month = year_month_item.text(0)
            year, month = map(int, year_month.split('/'))
            month_name = month_names[month - 1]
            target_folder = os.path.join(self.current_directory, str(year), f"{month:02d}-{month_name}")

            

            for j in range(year_month_item.childCount()):
                dir_item = year_month_item.child(j)
                target_folder = target_folder + '\\' + dir_item.text(0)
                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)
                for k in range(dir_item.childCount()):
                    file_item = dir_item.child(k)
                    file_path = file_item.text(1)  # Ahora correctamente toma el directorio completo del archivo
                    try:
                        # print(removing_folder+'\\'+dir_item.text(0))
                        shutil.move(file_path, target_folder)
                    except Exception as e:
                        print(f"Error al mover {file_path}: {e}")
            # Eliminar carpeta si está vacía    
            if not os.listdir(removing_folder + '\\' + dir_item.text(0)):  # Verifica si la carpeta está vacía
                try:
                    os.rmdir(removing_folder + '\\' + dir_item.text(0))  # Elimina la carpeta
                except Exception as e:
                    print(f"Error al eliminar la carpeta {removing_folder} \\ {dir_item.text(0)}: {e}")

    def reorganize_to_original(self):
        """
        Reorganiza los archivos desde la estructura de fechas de vuelta a sus carpetas originales,
        agrupándolos por nombre de subcarpeta. Los archivos sin subcarpeta se mueven a la ruta inicial.
        """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar deshacer reorganización")
        msg_box.setText("Se reorganizarán los archivos al directorio original. ¿Está seguro de continuar?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        yes_button = msg_box.button(QMessageBox.Yes)
        yes_button.setText("Sí")
        confirmation = msg_box.exec()

        if confirmation != QMessageBox.Yes:
            return
        
        date_pattern = r'(?:(\d{4}\\\d{2}-(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre))|(\d{2}\\\d{2}\\)|(\d{2}\\(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre))|(\d{4}\\(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)))(\\.+)$'

        # Estructura base
        root_path = self.current_directory  # Ruta inicial
        if not os.path.exists(root_path):
            QMessageBox.warning(self, "Advertencia", "La ruta inicial no existe.")
            return

        # Crear un diccionario para mapear archivos a las carpetas originales
        folder_map = {}
        files_without_subfolder = []  # Archivos que no tienen subcarpeta

        for root, dirs, files in os.walk(root_path):
            for file in files:
                # Verificar si el archivo está en una subcarpeta
                relative_path = os.path.relpath(root, root_path)

                match = re.search(date_pattern, relative_path)
                print(relative_path)
                
                if match:
                    if os.sep in relative_path:  # Tiene una subcarpeta
                        subfolder_name = os.path.basename(root)
                        if subfolder_name not in folder_map:
                            folder_map[subfolder_name] = []
                        folder_map[subfolder_name].append(os.path.join(root, file))
                else:
                    # El archivo está en una carpeta de nivel intermedio
                    files_without_subfolder.append(os.path.join(root, file))
        

        # Mover archivos sin subcarpeta directamente a la ruta inicial
        for file_path in files_without_subfolder:
            try:
                shutil.move(file_path, root_path)
            except Exception as e:
                print(f"Error al mover {file_path} a {root_path}: {e}")

        # Crear las carpetas originales y mover los archivos
        for subfolder_name, file_list in folder_map.items():
            target_folder = os.path.join(root_path, subfolder_name)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            for file_path in file_list:
                try:
                    shutil.move(file_path, target_folder)
                except Exception as e:
                    print(f"Error al mover {file_path} a {target_folder}: {e}")

        # Eliminar las carpetas vacías
        for root, dirs, files in os.walk(root_path, topdown=False):
            if not os.listdir(root):
                try:
                    os.rmdir(root)
                except Exception as e:
                    print(f"Error al eliminar carpeta vacía {root}: {e}")
        QMessageBox.information(self, "Proceso Completo", "Los archivos han sido reorganizados a sus carpetas originales.")
    


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Archivos")
        self.resize(1200, 600)

        self.file_organizer = FileOrganizerWidget()
        self.setCentralWidget(self.file_organizer)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
