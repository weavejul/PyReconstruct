from PySide6.QtWidgets import QDockWidget, QTableWidgetItem, QAbstractItemView, QLabel, QWidget
from PySide6.QtCore import Qt

from .copy_table_widget import CopyTableWidget

class Help3DWidget(QDockWidget):

    def __init__(self):
        """Create a text widget to display 3D options"""
        super().__init__()
        self.help_desc = help_3D

        self.setFloating(True)
        self.setAllowedAreas(Qt.NoDockWidgetArea)
        self.setWindowTitle("Help")
        
        # create the table
        self.createTable()

        self.resize(sum([self.table.columnWidth(i) for i in (0, 1)]), 600)

        self.closed = False
        self.show()

    def setRow(self, r : int, key_desc : tuple):
        """Set the data for a row.
        
            Params:
                r (int): the row index
                key_desc (tuple): key, description
        """
        if key_desc is None:
            return
        elif type(key_desc) is str:
            i = QTableWidgetItem(key_desc)
            f = i.font()
            f.setBold(True)
            i.setFont(f)
            self.table.setItem(r, 0, i)
        else:
            k, d = key_desc
            self.table.setItem(r, 0, QTableWidgetItem(k))
            if type(d) is str:
                self.table.setItem(r, 1, QTableWidgetItem(d))
            elif isinstance(d, QWidget):
                self.table.setCellWidget(r, 1, d)
        self.table.setRowHeight(r, 5)
    
    def createTable(self):
        """Create the table widget."""
        # establish table headers
        self.horizontal_headers = ["Key", "Description"]

        self.table = CopyTableWidget(len(self.help_desc) + 1, len(self.horizontal_headers))
        self.setWidget(self.table)

        # format table
        self.table.setShowGrid(False)  # no grid
        self.table.setAlternatingRowColors(True)  # alternate row colors
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # cannot be edited
        self.table.setHorizontalHeaderLabels(self.horizontal_headers)  # titles
        self.table.verticalHeader().hide()  # no veritcal header

        # fill in data
        for r, key_desc in enumerate(self.help_desc):
            self.setRow(r, key_desc)
        
        # format the table
        self.table.resizeColumnsToContents()

    def closeEvent(self, event):
        self.closed = True
        return super().closeEvent(event)

help_3D = [
    ("Left-click", "rotate scene / select objects"),
    ("Middle-click", "pan scene"),
    ("Right-click", "zoom scene in or out"),
    ("Ctrl-click", "rotate scene / select objects"),
    ("Double-click", "move to point in 2D field"),
    None,
    ("Left/Right", "translate selected object(s) in X"),
    ("Up/Down", "translate in Y"),
    ("Ctrl+Up/Down", "translate in Z"),
    None,
    ("Shift+Left/Right", "rotate selected object(s) on X-axis around the center of mass"),
    ("Shift+Up/Down", "rotate on Y-axis"),
    ("Ctrl+Shift+Up/Down", "rotate on Z-axis"),
    None,
    ("Ctrl+A", "Select all"),
    ("Ctrl+D", "Deselect all"),
    ("Home", "Focus scene on objects"),
    ("Shift+H", "Select all objects in selected object's host group"),
    (" ", "A 'host group' is a group of objects that are"),
    ("", "all connected by host/inhabitant relationships."),
    None,
    ("C", "toggle scale cube"),
    ("Ctrl+Shift+H", "Organize objects in the scene"),
    None,
    ("Ctrl+E", "edit attributes of selected objects"),
    ("[", "decrease opacity of selected object(s)"),
    ("]", "increase opacity of selected object(s)"),
    None,
    ("Delete/Backspace", "remove the selected object(s) from the scene"),
    None,
    (".", "fly camera towards last clicked point"),
    ("I", "print info about selected object"),
    ("Shift+I", "print the RGB color under the mouse"),
    # ("Y", "show the pipeline for this object as a graph"),
    ("W/S", "toggle wireframe/surface style"),
    ("P/Shift+P", "change point size of vertices"),
    ("L", "toggle edges visibility"),
    ("X", "toggle mesh visibility"),
    ("Shift+X", "invoke a cutter widget tool"),
    ("1-3", "change mesh color"),
    # ("4", "use data array as colors, if present"),
    ("5-6", "change background color(s)"),
    ("+/-", "cycle axes style"),
    ("K", "cycle available lighting styles"),
    ("Shift+K", "cycle available shading styles"),
    ("Shift+A", "toggle anti-aliasing"),
    ("Shift+D", "toggle depth-peeling (for transparencies)"),
    ("O/Shift+O", "add/remove light to scene and rotate it"),
    ("N", "show surface mesh normals"),
    ("A", "toggle interaction to Actor Mode"),
    ("J", "toggle interaction to Joystick Mode"),
    ("Shift+U", "toggle perspective/parallel projection"),
    ("R", "reset camera position"),
    ("Shift+R", "reset camera orientation to orthogonal view"),
    ("Shift+C", "print current camera settings"),
    # ("Shift+S", "save a screenshot"),
    # ("Shift+E/Shift+F", "export 3D scene to numpy file or X3D"),
    ("Q", "return control to python script"),
    ("Esc", "abort execution and exit python kernel")
]