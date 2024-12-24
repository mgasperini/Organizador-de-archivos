import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QFileSystemModel, 
    QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel, 
    QComboBox, QFileDialog, QListView, QSplitter, QStackedWidget,
    QGraphicsView, QGraphicsScene, QProgressBar
)
from PySide6.QtCore import QDir, Qt, QSize, QModelIndex, QDateTime, QRect, QThread, QObject, Signal, QTimer
from PySide6.QtGui import (
    QStandardItemModel, QStandardItem, QPixmap, QIcon
)
from PySide6.QtWidgets import QGraphicsPixmapItem
import os
import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
from pathlib import Path
import hashlib

class ThumbnailCache:
    def __init__(self, cache_dir=None, max_size=1000):
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser('~'), '.thumbnails')
        self.max_size = max_size
        self.cache = {}
        self.cache_lock = threading.Lock()
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def get_cache_path(self, file_path):
        # Crear un hash único para el archivo basado en su ruta y fecha de modificación
        file_stat = os.stat(file_path)
        hash_str = f"{file_path}{file_stat.st_mtime}"
        hash_name = hashlib.md5(hash_str.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hash_name}.png")

    def get_thumbnail(self, file_path):
        with self.cache_lock:
            cache_path = self.get_cache_path(file_path)
            if cache_path in self.cache:
                return self.cache[cache_path]
            
            if os.path.exists(cache_path):
                pixmap = QPixmap(cache_path)
                self.cache[cache_path] = pixmap
                return pixmap
        return None

    def save_thumbnail(self, file_path, pixmap):
        with self.cache_lock:
            cache_path = self.get_cache_path(file_path)
            pixmap.save(cache_path, "PNG")
            self.cache[cache_path] = pixmap
            
            # Limpiar caché si excede el tamaño máximo
            if len(self.cache) > self.max_size:
                # Eliminar 20% de las entradas más antiguas
                items_to_remove = int(self.max_size * 0.2)
                for _ in range(items_to_remove):
                    self.cache.pop(next(iter(self.cache)))

class ImageLoader(QObject):
    thumbnail_ready = Signal(str, QPixmap)
    batch_complete = Signal()

    def __init__(self, cache):
        super().__init__()
        self.cache = cache
        self.queue = queue.Queue()
        self.active = True
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.processing_thread = threading.Thread(target=self._process_queue)
        self.processing_thread.start()

    def queue_image(self, file_path):
        self.queue.put(file_path)

    def _process_queue(self):
        while self.active:
            try:
                file_paths = []
                # Recolectar hasta 10 imágenes o esperar 100ms
                try:
                    while len(file_paths) < 10:
                        file_path = self.queue.get(timeout=0.1)
                        file_paths.append(file_path)
                except queue.Empty:
                    pass

                if file_paths:
                    # Procesar el lote de imágenes
                    futures = []
                    for file_path in file_paths:
                        futures.append(self.thread_pool.submit(self._load_thumbnail, file_path))
                    
                    # Esperar que todas las miniaturas del lote estén listas
                    for future in futures:
                        future.result()
                    
                    self.batch_complete.emit()

            except queue.Empty:
                continue

    def _load_thumbnail(self, file_path):
        try:
            # Intentar obtener del caché primero
            thumbnail = self.cache.get_thumbnail(file_path)
            if thumbnail is None:
                # Crear miniatura si no está en caché
                with Image.open(file_path) as img:
                    img.thumbnail((96, 96))
                    pixmap = QPixmap()
                    pixmap.loadFromData(img.tobytes())
                    self.cache.save_thumbnail(file_path, pixmap)
                    thumbnail = pixmap
            
            self.thumbnail_ready.emit(file_path, thumbnail)
            return thumbnail
        except Exception as e:
            print(f"Error loading thumbnail for {file_path}: {e}")
            return None

    def stop(self):
        self.active = False
        self.thread_pool.shutdown()

class FileMetadata:
    @staticmethod
    def get_file_date(file_path):
        """
        Obtiene la fecha de un archivo, intentando primero obtener la fecha EXIF si es una imagen,
        y si no es posible, usa la fecha de modificación del archivo.
        """
        # Primero intentar obtener fecha EXIF para imágenes
        if file_path.lower().endswith(('.jpg', '.jpeg')):
            try:
                with Image.open(file_path) as img:
                    exif = img.getexif()
                    if exif:
                        # Buscar la fecha en diferentes tags EXIF
                        for tag_id in (36867, 306, 36868):  # DateTimeOriginal, DateTime, DateTimeDigitized
                            if tag_id in exif:
                                date_str = exif[tag_id]
                                try:
                                    return datetime.datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                                except ValueError:
                                    pass
            except Exception:
                pass

        # Si no se pudo obtener la fecha EXIF, usar la fecha de modificación del archivo
        return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        
        # Etiqueta para el nombre del archivo
        self.file_name_label = QLabel()
        self.file_name_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.file_name_label)
        
        # Vista de la imagen
        self.preview_view = QGraphicsView()
        self.preview_scene = QGraphicsScene()
        self.preview_view.setScene(self.preview_scene)
        self.layout.addWidget(self.preview_view)
        
        # Etiqueta para la información del archivo
        self.file_info_label = QLabel()
        self.layout.addWidget(self.file_info_label)

    def update_preview(self, file_path):
        if not file_path:
            self.clear_preview()
            return

        self.file_name_label.setText(os.path.basename(file_path))
        
        if os.path.isfile(file_path):
            # Obtener información del archivo
            file_info = os.stat(file_path)
            size_mb = file_info.st_size / (1024 * 1024)
            date = datetime.datetime.fromtimestamp(file_info.st_mtime)
            
            info_text = f"Tamaño: {size_mb:.2f} MB\n"
            info_text += f"Fecha: {date.strftime('%Y-%m-%d %H:%M:%S')}"
            self.file_info_label.setText(info_text)

            # Mostrar previsualización
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    self.preview_scene.clear()
                    # Escalar manteniendo proporción
                    view_size = self.preview_view.size()
                    scaled_pixmap = pixmap.scaled(
                        view_size.width() - 20, 
                        view_size.height() - 20,
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.preview_scene.addPixmap(scaled_pixmap)
                    self.preview_scene.setSceneRect(scaled_pixmap.rect())
            else:
                self.preview_scene.clear()
        else:
            self.clear_preview()

    def clear_preview(self):
        self.preview_scene.clear()
        self.file_info_label.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Reajustar la imagen si hay una en la escena
        if len(self.preview_scene.items()) > 0:
            pixmap_item = self.preview_scene.items()[0]
            if isinstance(pixmap_item, QGraphicsPixmapItem):
                original_pixmap = pixmap_item.pixmap()
                scaled_pixmap = original_pixmap.scaled(
                    event.size().width() - 20,
                    event.size().height() - 20,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                pixmap_item.setPixmap(scaled_pixmap)
                self.preview_scene.setSceneRect(scaled_pixmap.rect())

class FileListView(QListView):

    directory_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListView.IconMode)
        self.setIconSize(QSize(96, 96))  # Iconos más grandes
        self.setGridSize(QSize(120, 140))  # Grid más grande para acomodar nombres
        self.setSpacing(10)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)
        self.setWordWrap(True)  # Permitir nombres largos en múltiples líneas
        # Habilitar el seguimiento del mouse para detectar doble clic
        self.setMouseTracking(True)
        
    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.position().toPoint())
        if index.isValid():
            # Obtener el modelo del sistema de archivos
            fs_model = self.model()
            if isinstance(fs_model, QFileSystemModel):
                # Verificar si es un directorio
                if fs_model.isDir(index):
                    # Navegar al directorio
                    self.setRootIndex(index)
                    # Emitir una señal personalizada para notificar el cambio
                    if hasattr(self, 'directory_changed'):
                        self.directory_changed.emit(fs_model.filePath(index))

class OptimizedFileListView(FileListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnail_cache = ThumbnailCache()
        self.image_loader = ImageLoader(self.thumbnail_cache)
        self.image_loader.thumbnail_ready.connect(self._update_item_icon)
        self.pending_thumbnails = set()
        
    def _update_item_icon(self, file_path, pixmap):
        if not pixmap.isNull():
            model = self.model()
            if isinstance(model, QFileSystemModel):
                index = model.index(file_path)
                if index.isValid():
                    model.setData(index, QIcon(pixmap), Qt.DecorationRole)
        self.pending_thumbnails.discard(file_path)

    def rowsInserted(self, parent, start, end):
        super().rowsInserted(parent, start, end)
        model = self.model()
        if isinstance(model, QFileSystemModel):
            for row in range(start, end + 1):
                index = model.index(row, 0, parent)
                file_path = model.filePath(index)
                if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                    if file_path not in self.pending_thumbnails:
                        self.pending_thumbnails.add(file_path)
                        self.image_loader.queue_image(file_path)


class ScanWorker(QObject):
    finished = Signal(dict)
    progress = Signal(int)
    
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
                    # Optimización: solo obtener fecha de modificación inicialmente
                    date = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                    year_month = f"{date.year}/{date.month:02d}"
                    
                    if year_month not in files_by_date:
                        files_by_date[year_month] = {}
                    
                    if rel_path not in files_by_date[year_month]:
                        files_by_date[year_month][rel_path] = []
                    
                    files_by_date[year_month][rel_path].append({
                        'name': file,
                        'path': full_path,
                        'date': date,
                        'icon_loaded': False
                    })
                    
                    processed_files += 1
                    if processed_files % 100 == 0:  # Actualizar progreso cada 100 archivos
                        self.progress.emit(int(processed_files * 100 / total_files))
                        
                except Exception as e:
                    print(f"Error processing {full_path}: {e}")
        
        self.finished.emit(files_by_date)

class FileOrganizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_directory = QDir.homePath()
        self.initialize_models()
        self.setup_connections()

        # Agregar señal personalizada para el cambio de directorio
        # self.normal_view.directory_changed = Signal(str)
        self.normal_view.directory_changed.connect(self.on_directory_changed)


    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Toolbar
        self.toolbar = QHBoxLayout()
        self.select_folder_button = QPushButton("Seleccionar carpeta")
        self.view_selector = QComboBox()
        self.view_selector.addItems(["Vista normal", "Vista por fecha"])
        
        self.toolbar.addWidget(self.select_folder_button)
        self.toolbar.addWidget(QLabel("Vista:"))
        self.toolbar.addWidget(self.view_selector)
        self.toolbar.addStretch()
        
        self.main_layout.addLayout(self.toolbar)

        # Agregar barra de progreso (inicialmente oculta)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

        # Splitter principal horizontal
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Tree view para la navegación
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.main_splitter.addWidget(self.tree_view)

        # Splitter secundario vertical para la vista y la previsualización
        self.right_splitter = QSplitter(Qt.Vertical)
        
        # Stack widget para las diferentes vistas
        self.stack_widget = QStackedWidget()
        self.normal_view = FileListView()
        self.date_view = QTreeView()
        
        self.stack_widget.addWidget(self.normal_view)
        self.stack_widget.addWidget(self.date_view)
        
        self.right_splitter.addWidget(self.stack_widget)
        
        # Widget de previsualización
        self.preview_widget = PreviewWidget()
        self.right_splitter.addWidget(self.preview_widget)
        
        # Agregar splitter secundario al principal
        self.main_splitter.addWidget(self.right_splitter)
        
        # Ajustar proporciones
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        self.right_splitter.setStretchFactor(0, 2)
        self.right_splitter.setStretchFactor(1, 1)

        
        self.main_layout.addWidget(self.main_splitter)

    def initialize_models(self):
        # Modelo del sistema de archivos para el árbol
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(self.current_directory)
        self.fs_model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files)
        
        # Configurar tree view
        self.tree_view.setModel(self.fs_model)
        self.tree_view.setRootIndex(self.fs_model.index(self.current_directory))
        
        # Ocultar columnas innecesarias
        for i in range(1, self.fs_model.columnCount()):
            self.tree_view.hideColumn(i)
        
        # Modelo para la vista normal (ahora usando QFileSystemModel también)
        self.normal_view.setModel(self.fs_model)
        self.normal_view.setRootIndex(self.fs_model.index(self.current_directory))
        
        # Modelo para la vista por fecha
        self.date_model = QStandardItemModel()
        self.date_model.setHorizontalHeaderLabels(["Fecha / Archivo"])
        self.date_view.setModel(self.date_model)

    def setup_connections(self):
        self.select_folder_button.clicked.connect(self.select_folder)
        self.view_selector.currentIndexChanged.connect(self.change_view)
        self.tree_view.clicked.connect(self.on_tree_view_clicked)
        self.normal_view.clicked.connect(self.on_item_clicked)
        self.date_view.clicked.connect(self.on_date_item_clicked)
        # Agregar conexión para doble clic en el tree view
        self.tree_view.doubleClicked.connect(self.on_tree_view_double_clicked)
        self.normal_view.directory_changed.connect(self.on_directory_changed)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta", self.current_directory)
        if folder:
            self.current_directory = folder
            self.tree_view.setRootIndex(self.fs_model.index(self.current_directory))
            self.normal_view.setRootIndex(self.fs_model.index(self.current_directory))
            self.update_date_view(self.current_directory)

    def on_tree_view_clicked(self, index):
        path = self.fs_model.filePath(index)
        self.current_directory = path  # Actualizar el directorio actual
        self.normal_view.setRootIndex(index)
        if self.stack_widget.currentIndex() == 1:
            self.update_date_view(path)

    def on_item_clicked(self, index):
        path = self.fs_model.filePath(index)
        self.preview_widget.update_preview(path)

    def on_date_item_clicked(self, index):
        item = self.date_model.itemFromIndex(index)
        if item and item.data(Qt.UserRole):
            self.preview_widget.update_preview(item.data(Qt.UserRole))

    def change_view(self, index):
        self.stack_widget.setCurrentIndex(index)
        if index == 1:
            self.update_date_view(self.current_directory)

    def update_date_view(self, path):
        # Mostrar y resetear la barra de progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.date_model.clear()
        self.date_model.setHorizontalHeaderLabels(["Fecha / Carpeta / Archivo"])
        
        # Usar un thread para no bloquear la interfaz
        self.scan_thread = QThread()
        self.scan_worker = ScanWorker(path)
        self.scan_worker.moveToThread(self.scan_thread)
        
        # Conectar señales
        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.progress.connect(self.update_scan_progress)
        self.scan_worker.finished.connect(self.populate_date_view)
        self.scan_worker.finished.connect(self.scan_thread.quit)
        self.scan_worker.finished.connect(self.scan_worker.deleteLater)
        self.scan_thread.finished.connect(self.scan_thread.deleteLater)
        
        # Iniciar escaneo
        self.scan_thread.start()

    def queue_icon_loading(self, item, file_path):
        """Carga el icono de forma asíncrona"""
        def load_icon():
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                icon = QIcon(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                item.setIcon(icon)
        
        QTimer.singleShot(0, load_icon)

    def populate_date_view(self, files_by_date):
        for year_month in sorted(files_by_date.keys(), reverse=True):
            year_month_item = QStandardItem(year_month)
            self.date_model.appendRow(year_month_item)
            
            folders = files_by_date[year_month]
            for folder_path in sorted(folders.keys()):
                if folder_path:
                    folder_item = QStandardItem(folder_path)
                    year_month_item.appendRow(folder_item)
                else:
                    folder_item = year_month_item
                    
                files = sorted(folders[folder_path], key=lambda x: (x['date'], x['name']))
                for file_info in files:
                    file_item = QStandardItem(file_info['name'])
                    file_item.setData(file_info['path'], Qt.UserRole)
                    
                    # Cargar iconos solo para archivos visibles
                    if not file_info.get('icon_loaded'):
                        if file_info['path'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                            self.queue_icon_loading(file_item, file_info['path'])
                    
                    folder_item.appendRow(file_item)

    def scan_directory(self, path):
        # [El método scan_directory permanece igual que en la versión anterior]
        files_by_date = {}
        
        for root, dirs, files in os.walk(path):
            rel_path = os.path.relpath(root, path)
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
                except Exception as e:
                    print(f"Error processing {full_path}: {e}")
                    
        return files_by_date
    
    def update_scan_progress(self, value):
        """Actualiza la barra de progreso durante el escaneo"""
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        if value >= 100:
            # Ocultar la barra cuando termine
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))

    def on_directory_changed(self, new_path):
        """Maneja el cambio de directorio desde cualquier vista"""
        self.current_directory = new_path
        # Actualizar el árbol para mostrar la selección correcta
        index = self.fs_model.index(new_path)
        self.tree_view.setCurrentIndex(index)
        # Si estamos en vista por fecha, actualizarla
        if self.stack_widget.currentIndex() == 1:
            self.update_date_view(new_path)

    def on_tree_view_double_clicked(self, index):
        """Maneja el doble clic en el árbol de directorios"""
        path = self.fs_model.filePath(index)
        self.current_directory = path
        # Actualizar la vista normal
        self.normal_view.setRootIndex(index)
        # Si estamos en vista por fecha, actualizarla
        if self.stack_widget.currentIndex() == 1:
            self.update_date_view(path)

class OptimizedFileOrganizerWidget(FileOrganizerWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Reemplazar la vista normal con la versión optimizada
        self.normal_view = OptimizedFileListView()
        self.stack_widget.removeWidget(self.stack_widget.widget(0))
        self.stack_widget.insertWidget(0, self.normal_view)
        
        # Optimizar el escaneo de directorios
        self._setup_scanning_optimizations()

    def _setup_scanning_optimizations(self):
        self.scan_pool = ThreadPoolExecutor(max_workers=os.cpu_count())
        self.scan_chunks = []
        self.processed_files = set()

    def update_date_view(self, path):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Dividir el escaneo en chunks para mejor rendimiento
        def scan_chunk(chunk_paths):
            files_by_date = {}
            for file_path in chunk_paths:
                if file_path in self.processed_files:
                    continue
                    
                try:
                    date = FileMetadata.get_file_date(file_path)
                    year_month = f"{date.year}/{date.month:02d}"
                    rel_path = os.path.relpath(os.path.dirname(file_path), path)
                    
                    if year_month not in files_by_date:
                        files_by_date[year_month] = {}
                    if rel_path not in files_by_date[year_month]:
                        files_by_date[year_month][rel_path] = []
                        
                    files_by_date[year_month][rel_path].append({
                        'name': os.path.basename(file_path),
                        'path': file_path,
                        'date': date
                    })
                    self.processed_files.add(file_path)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
            
            return files_by_date

        # Obtener lista de archivos y dividir en chunks
        all_files = []
        for root, _, files in os.walk(path):
            for file in files:
                all_files.append(os.path.join(root, file))
        
        chunk_size = 100  # Ajustar según necesidad
        self.scan_chunks = [all_files[i:i + chunk_size] 
                          for i in range(0, len(all_files), chunk_size)]
        
        # Procesar chunks en paralelo
        futures = []
        for chunk in self.scan_chunks:
            future = self.scan_pool.submit(scan_chunk, chunk)
            futures.append(future)
        
        # Actualizar progreso y modelo
        completed = 0
        files_by_date = {}
        for future in futures:
            chunk_result = future.result()
            for year_month, data in chunk_result.items():
                if year_month not in files_by_date:
                    files_by_date[year_month] = {}
                for rel_path, files in data.items():
                    if rel_path not in files_by_date[year_month]:
                        files_by_date[year_month][rel_path] = []
                    files_by_date[year_month][rel_path].extend(files)
            
            completed += 1
            progress = int((completed / len(futures)) * 100)
            self.progress_bar.setValue(progress)
        
        self.populate_date_view(files_by_date)
        self.progress_bar.setVisible(False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Archivos")
        self.resize(1200, 800)
        
        self.file_organizer = FileOrganizerWidget()
        self.setCentralWidget(self.file_organizer)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.file_organizer = OptimizedFileOrganizerWidget()
    window.show()
    sys.exit(app.exec())