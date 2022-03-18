from PyQt5 import QtCore, QtWidgets

from gui.GUI_HELP_POPUP import Ui_help_popup
from sk_tools import *


class Help_Popup(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        dprint("OPENING LOG VIEWER", color = 'red')
        self.ui = Ui_help_popup()
        self.ui.setupUi(self)
        self.ui.textEdit_file.setMarkdown(open("help.md", 'r').read())
        
    def keyPressEvent(self, event):  # Escape key functionality
        key = event.key()
        if (key == QtCore.Qt.Key_Escape):
            self.close()

def open_help_popup(self):
    self.window = Help_Popup()
    self.window.show()
    return

