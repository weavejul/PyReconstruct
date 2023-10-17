from PySide6.QtWidgets import (
    QWidget, 
    QDialog, 
    QDialogButtonBox, 
    QHBoxLayout, 
    QLabel, 
    QVBoxLayout, 
    QComboBox, 
    QPushButton, 
    QInputDialog
)

from modules.datatypes import ObjGroupDict


class ObjectGroupDialog(QDialog):

    def __init__(self, parent : QWidget, objgroupdict : ObjGroupDict, new_group=True):
        """Create an object group dialog.
        
            Params:
                parent (QWidget): the parent widget
                objgroupdict (ObjGroupDict): object containing information on object groups
                new_group (bool): whether or not to include new group button
        """
        super().__init__(parent)

        self.setWindowTitle("Group")

        group_row = QHBoxLayout()
        group_text = QLabel(self, text="Group:")
        self.group_input = QComboBox(self)
        self.group_input.addItem("")
        self.group_input.addItems(sorted(objgroupdict.getGroupList()))
        self.group_input.resize(self.group_input.sizeHint())
        group_row.addWidget(group_text)
        group_row.addWidget(self.group_input)
        if new_group:
            newgroup_bttn = QPushButton(self, "new_group", text="New Group...")
            newgroup_bttn.clicked.connect(self.newGroup)
            group_row.addWidget(newgroup_bttn)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttonbox = QDialogButtonBox(QBtn)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        self.vlayout = QVBoxLayout()
        self.vlayout.setSpacing(10)
        self.vlayout.addLayout(group_row)
        self.vlayout.addSpacing(10)
        self.vlayout.addWidget(buttonbox)

        self.setLayout(self.vlayout)
    
    def newGroup(self):
        """Add a new group to the list."""
        new_group_name, confirmed = QInputDialog.getText(self, "New Object Group", "New group name:")
        if not confirmed:
            return
        self.group_input.addItem(new_group_name)
        self.group_input.setCurrentText(new_group_name)
        self.group_input.resize(self.group_input.sizeHint())
        
    def exec(self):
        """Run the dialog."""
        confirmed = super().exec()
        text = self.group_input.currentText()
        if confirmed and text:
            return self.group_input.currentText(), True
        else:
            return "", False
