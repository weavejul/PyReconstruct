import os

from PySide6.QtWidgets import (
    QWidget,
    QDialog, 
    QDialogButtonBox, 
    QLabel, 
    QLineEdit,
    QTextEdit,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QRadioButton,
    QGridLayout,
    QTabWidget,
    QScrollArea
)
from PySide6.QtCore import Qt

from .helper import resizeLineEdit, BrowseWidget
from .color_button import ColorButton
from .shape_button import ShapeButton
from PyReconstruct.modules.gui.utils import notify

class InputField():

    def __init__(self, type, widget, check_params=None, required=False):
        self.type = type
        self.widget = widget
        self.check_params = check_params
        self.required = required
    
    def getResponse(self):
        if self.type == "text" or self.type == "textbox":
            t = self.widget.text() if self.type == "text" else self.widget.toPlainText()
            if not t and self.required:
                notify("Please enter a response.")
                return None, False
            else:
                return t, True
        elif self.type == "int":
            if not self.widget.text():
                if self.required:
                    notify("Please enter an integer.")
                    return None, False
                else:
                    return None, True
            try:
                n = int(self.widget.text())
                if self.check_params:
                    if n in self.check_params:
                        return n, True
                    else:
                        notify("Please enter a valid integer.")
                        return None, False
                else:
                    return n, True
            except ValueError:
                notify("Please enter a valid integer.")
                return None, False
        elif self.type == "float":
            if not self.widget.text():
                if self.required:
                    notify("Please enter a number.")
                    return None, False
                else:
                    return None, True
            try:
                n = float(self.widget.text())
                if self.check_params:
                    lower, upper = tuple(self.check_params)
                    if lower <= n <= upper:
                        return n, True
                    else:
                        notify("Please enter a valid number.")
                        return None, False
                else:
                    return n, True
            except ValueError:
                notify("Please enter a valid number.")
                return None, False
        elif self.type == "combo":
            t = self.widget.currentText()
            if t == "" and self.required:
                notify("Please select a field from the dropdown menu.")
                return None, False
            else:
                return t, True
        elif self.type == "check" or self.type == "radio":
            response = []
            layout = self.widget.layout()
            for i in range(layout.count()):
                bttn = layout.itemAt(i).widget()
                response.append((bttn.text(), bttn.isChecked()))
            return response, True
        elif self.type == "file" or self.type == "dir":
            r = self.widget.text()
            if r:
                if os.path.isdir(r) or os.path.isfile(r):
                    return r, True
                else:
                    notify("Please select a valid path.")
                    return None, False
            else:
                if self.required:
                    notify("Please enter a path.")
                    return None, False
                else:
                    return None, True
        elif self.type == "color":
            c = self.widget.getColor()
            if c is None:
                if self.required:
                    notify("Please select a color.")
                    return None, False
                else:
                    return None, True
            else:
                return c, True
        elif self.type == "shape":
            s = self.widget.getShape()
            if not s:
                if self.required:
                    notify("Please select a shape.")
                    return None, False
                else:
                    return None, True
            else:
                return s, True


class QuickDialog(QDialog):

    def __init__(self, parent, structure : list, title : str, grid=False, include_confirm=True):
        """Create a quick dialog from a given structure.
        
            Params:
                parent (QWidget): the widget containing the dialog
                structure (list): the structure of the dialog
                title (str): the title of the dialog
                grid (bool): True if structure should be grid-style
        """
        QDialog.__init__(self, parent)

        vlayout, self.inputs = self.getLayout(structure, grid)

        if include_confirm:
            self.setWindowTitle(title)
            QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            buttonbox = QDialogButtonBox(QBtn)
            buttonbox.accepted.connect(self.accept)
            buttonbox.rejected.connect(self.reject)
            vlayout.addWidget(buttonbox)
        else:
            lbl = QLabel(self, text=title)
            f = lbl.font()
            f.setBold(True)
            lbl.setFont(f)
            vlayout.insertWidget(0, lbl, alignment=Qt.AlignHCenter)

        self.setLayout(vlayout)
    
    def getLayout(self, structure : list, grid : bool):
        """Return the layout for a given structure."""
        inputs = []

        if grid:
            grid_layout = QGridLayout()
            r = 0
            c = 0
        vlayout = QVBoxLayout()
        vlayout.setSpacing(1)

        for row_structure in structure:
            if not row_structure:  # vertical layout spacer
                if grid:
                    r += 1
                else:
                    vlayout.addSpacing(5)
                continue
            
            if not grid:
                row_layout = QHBoxLayout()
                row_layout.setSpacing(4)
            for item in row_structure:
                if not item:  # Spacer
                    if grid:
                        c += 1
                    else:
                        row_layout.addStretch()
                    continue
                elif type(item) is str:  # Label
                    w = QLabel(self, text=item)
                else:
                    # checking for leading bool to mark required status
                    if type(item[0]) is bool:
                        required = item[0]
                        item = item[1:]
                    else:
                        required = False
                    widget_type = item[0]
                    params = item[1:]
                    if widget_type == "text" or widget_type == "textbox":  # Text input
                        # Params structure: str
                        text = params[0]
                        w = QLineEdit(text, self) if widget_type == "text" else QTextEdit(text.replace("\n", "<br/>"), self)
                        inputs.append(InputField(widget_type, w, required=required))
                    elif widget_type == "int" or widget_type == "float": 
                        # Params structure: int, optional: list[int]
                        n = params[0]
                        if len(params) > 1:
                            options = params[1]
                        else:
                            options = None
                        if n is None:
                            w = QLineEdit("", self)
                        elif widget_type == "int":
                            w = QLineEdit(str(n), self)
                            resizeLineEdit(w, "000000")
                        elif widget_type == "float":
                            w = QLineEdit(str(round(n, 7)), self)
                            resizeLineEdit(w, "0.00000000")
                        inputs.append(InputField(widget_type, w, options, required=required))
                    elif widget_type == "combo":
                        # Params structure: list[str], optional: str
                        options = params[0]
                        if len(params) > 1:
                            selected = params[1]
                        else:
                            selected = None
                        w = QComboBox(self)
                        if not required or selected is None:
                            w.addItem("")
                        w.addItems(list(options))
                        if selected:
                            w.setCurrentText(selected)
                        inputs.append(InputField(widget_type, w, required=required))
                    elif widget_type == "check" or widget_type == "radio":
                        # Params structure list[(str, bool)]
                        w = QWidget(self)
                        vl = QVBoxLayout()
                        vl.setSpacing(1)
                        for text, checked in params:
                            if widget_type == "check":
                                bttn = QCheckBox(text, w)
                            else:
                                bttn = QRadioButton(text, w)
                            bttn.setChecked(checked)
                            vl.addWidget(bttn)
                        w.setLayout(vl)
                        inputs.append(InputField(widget_type, w, required=required))
                    elif widget_type == "file" or widget_type == "dir":
                        # Params structure: str (default filepath), str (filter; only for file)
                        fp = params[0]
                        if widget_type == "file":
                            filter = params[1]
                        else:
                            filter = None
                        w = BrowseWidget(self, type=widget_type, default_fp=fp, filter=filter)
                        inputs.append(InputField(widget_type, w, required=required))
                    elif widget_type == "color":
                        # Params structure: tuple
                        color = params[0]
                        w = ColorButton(color, self)
                        inputs.append(InputField(widget_type, w, required=required))
                    elif widget_type == "shape":
                        # Params structure: list
                        points = params[0]
                        if not points:
                            points = []
                        w = ShapeButton(points, self)
                        inputs.append(InputField(widget_type, w, required=required))
                    
                if grid:
                    grid_layout.addWidget(w, r, c)
                    c += 1
                else:
                    row_layout.addWidget(w)

            if grid:
                r += 1
                c = 0
            else:
                vlayout.addLayout(row_layout)
        
        if grid:
            vlayout.addLayout(grid_layout)
        
        return vlayout, inputs

    def accept(self):
        """Overwritten from parent class."""
        self.responses = []
        for input in self.inputs:
            r, is_valid = input.getResponse()
            if not is_valid:
                return False
            else:
                self.responses.append(r)
        self.responses = tuple(self.responses)
        
        QDialog.accept(self)
        return True
    
    def exec(self):
        "Run the dialog."
        confirmed = super().exec()
        if confirmed:
            return self.responses, True
        else:
            return None, False
    
    def get(parent : QWidget, structure : list, title="Dialog", grid=False):
        """Create a quick dialog and return the inputs.
        
            Params:
                parent (QWidget): the parent of the input dialog
                structure (list): the structure of the input dialog
                title (str): the title of the dialog
                grid (bool): True if grid layout
        """
        return QuickDialog(parent, structure, title, grid).exec()


class QuickTabDialog(QuickDialog):

    def __init__(self, parent, structures : dict, title="Dialog", grid=False, scrollable=False):
        """Create a quick dialog and return the inputs.
        
            Params:
                parent (QWidget): the parent of the input dialog
                structure (dict): the structure of the input dialog
                title (str): the title of the dialog
                grid (bool): True if grid layout
        """
        QDialog.__init__(self, parent)

        self.setWindowTitle(title)
        
        self.inputs = {}

        self.tab_widget = QTabWidget(self)

        for n, s in structures.items():
            vlayout, inputs = self.getLayout(s, grid)
            self.inputs[n] = inputs
            w = QWidget(self)
            w.setLayout(vlayout)
            self.tab_widget.addTab(w, n)

        full_vlayout = QVBoxLayout()
        if scrollable:
            qsa = QScrollArea(self)
            qsa.setWidget(self.tab_widget)
            qsa.setHorizontalScrollBar(None)
            full_vlayout.addWidget(qsa)
        else:
            full_vlayout.addWidget(self.tab_widget)    

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttonbox = QDialogButtonBox(QBtn)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        full_vlayout.addWidget(buttonbox)

        self.setLayout(full_vlayout)
    
    def get(parent : QWidget, structures : list, title="Dialog", grid=False):
        """Create a quick dialog with tabs and return the inputs.
        
            Params:
                parent (QWidget): the parent of the input dialog
                structures (list): the structure of the input dialog
                title (str): the title of the dialog
                grid (bool): True if grid layout
        """
        return QuickTabDialog(parent, structures, title, grid).exec()

    def accept(self):
        """Overwritten from parent class."""
        self.responses = {"current_tab_text": self.tab_widget.tabText(self.tab_widget.currentIndex())}

        for tab_name, inputs in self.inputs.items():
            self.responses[tab_name] = []
            for input in inputs:
                r, is_valid = input.getResponse()
                if not is_valid:
                    return
                else:
                    self.responses[tab_name].append(r)
        
        QDialog.accept(self)

