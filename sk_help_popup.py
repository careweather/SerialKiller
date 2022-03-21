from PyQt5 import QtCore, QtWidgets

from gui.GUI_HELP_POPUP import Ui_help_popup
from sk_tools import *


class Help_Popup(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        dprint("OPENING LOG VIEWER", color = 'red')
        self.ui = Ui_help_popup()
        self.ui.setupUi(self)

        help_text = ""
        with open("readme.md", 'r') as file:
            file_text = file.read().split("# Usage:")[1].split("# Possible Future Features / Fixes")[0]
            help_text = "# NOTE: This markdown translation has some issues. See the github repo for correct formatting\n" + file_text

        self.ui.textEdit_file.setMarkdown(help_text)
        
    def keyPressEvent(self, event):  # Escape key functionality
        key = event.key()
        if (key == QtCore.Qt.Key_Escape):
            self.close()

def open_help_popup(self):
    self.window = Help_Popup()
    self.window.show()
    return

