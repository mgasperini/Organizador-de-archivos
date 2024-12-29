
# build.py
import PyInstaller.__main__
import os
import modulefinder
import sys

def build_exe():
    # Obtener todos los imports del proyecto
    project_imports = ['hashlib',
                          'os',
                          'datetime',
                          'PIL.Image',
                          'shutil',
                          'typing.Dict',
                          'typing.List',
                          're',
                          'qdarkstyle',
                          'qdarkstyle.LightPalette',
                          'enum.Enum',
                          'sys'
                       ]
    
    # Lista base de opciones
    opts = [
        'main.py',  # Tu archivo principal
        '--name=Organizador de archivos',  # Nombre del ejecutable
        '--windowed',  # Para aplicaciones GUI (no muestra consola)
        '--onefile',  # Crear un solo archivo ejecutable
        # '--onedir',
        '--add-data=./Assets/actualizar.svg;.',  # Incluir carpeta de recursos
        '--add-data=./Assets/Adelante.svg;.',
        '--add-data=./Assets/arriba.svg;.',
        '--add-data=./Assets/flecha-pequena-izquierda.svg;.',
        '--add-data=./Assets/home.svg;.',
        '--clean',  # Limpiar cache antes de construir
        '--noupx',
    ]
    
    # Añadir imports explícitos de PyQt
    qt_imports = [
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        # Otros módulos específicos de PyQt que uses
        ]
    
    # Añadir imports comunes que PyInstaller podría no detectar
    additional_imports = [
        'PIL',
        # Añade aquí otros módulos que uses
    ]
    
    # Combinar todos los imports
    all_imports = set(qt_imports + additional_imports)
    all_imports.update(project_imports)
    
    # Añadir cada import a las opciones
    for module in all_imports:
        if module not in ['__main__', '__builtins__']:  # Excluir módulos built-in
            opts.append(f'--hidden-import={module}')
    
    
    # Imprimir los imports para verificación
    print("Imports detectados:")
    for module in sorted(all_imports):
        print(f" - {module}")
    
    # Ejecutar PyInstaller
    PyInstaller.__main__.run(opts)

if __name__ == '__main__':
    build_exe()