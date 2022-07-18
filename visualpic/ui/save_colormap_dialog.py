"""
This file is part of VisualPIC.

The module contains the class for the Qt dialog for saving a colormap to file.

Copyright 2016-2020, Angel Ferran Pousa.
License: GNU GPL-3.0.
"""


import sys
import os

from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import (QDialogButtonBox, QMessageBox, QPushButton,
                             QFileDialog)

from visualpic.visualization.volume_appearance import VolumeStyleHandler


if getattr(sys, 'frozen', False):
    # we are running in a bundle
    bundle_dir = sys._MEIPASS
else:
    # we are running in a normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
guipath = os.path.join(bundle_dir, 'save_colormap_dialog.ui')
Ui_SaveColormapDialog, QSaveColormapDialog = loadUiType(guipath)


class SaveColormapDialog(QSaveColormapDialog, Ui_SaveColormapDialog):
    def __init__(self, fld_val, r_val, g_val, b_val, parent=None):
        super(SaveColormapDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Save colormap')
        self.vs_handler = VolumeStyleHandler()
        self.fld_val = fld_val
        self.r_val = r_val
        self.g_val = g_val
        self.b_val = b_val
        self.setup_ui()
        self.register_ui_events()

    def setup_ui(self):
        self.location_lineEdit.setText(self.vs_handler.cmaps_folder_path)
        self.save_button = QPushButton("Save")
        self.close_button = QPushButton("Close")
        self.buttonBox.addButton(self.close_button,
                                 QDialogButtonBox.RejectRole)
        self.buttonBox.addButton(self.save_button, QDialogButtonBox.ApplyRole)

    def register_ui_events(self):
        self.save_button.clicked.connect(self.save_to_file)
        self.browse_pushButton.clicked.connect(self.browse_folder)

    def browse_folder(self):
        folder_path = str(QFileDialog.getExistingDirectory(
            self, "Save file to:", self.location_lineEdit.text()))
        if folder_path != "":
            self.location_lineEdit.setText(folder_path)

    def save_to_file(self):
        cmap_name = self.cmap_name_lineEdit.text()
        folder_path = self.location_lineEdit.text()
        if self.vs_handler.save_cmap(cmap_name, self.fld_val, self.r_val,
                                     self.g_val, self.b_val, folder_path):
            QMessageBox.information(
                self, 'Save colormap', 'Colormap succesfully saved to file.')
