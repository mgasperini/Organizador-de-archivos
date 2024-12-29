from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem

class DateView(QWidget):
    name = "DateView"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.files_by_date = {}
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Fecha", "Directorio/Archivo"])
        self.tree.setColumnWidth(0, 200)
        layout.addWidget(self.tree)

    def populate_tree(self, files_by_date):
        self.files_by_date = files_by_date
        self.tree.clear()

        for year_month, directories in sorted(files_by_date.items()):
            year_month_item = QTreeWidgetItem([year_month])
            self.tree.addTopLevelItem(year_month_item)

            for directory, files in directories.items():
                dir_item = QTreeWidgetItem([directory])
                year_month_item.addChild(dir_item)

                for file_info in files:
                    file_item = QTreeWidgetItem(["", file_info['name']])
                    dir_item.addChild(file_item)

    def update_root_index(self, directory):
        """Método público para actualizar el directorio mostrado"""
        self.tree.setRootIndex(self.fs_model.index(directory))

    def get_files_by_date(self):
        return self.files_by_date
