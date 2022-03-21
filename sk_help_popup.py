from os import remove
from PyQt5 import QtCore, QtWidgets

from gui.GUI_HELP_POPUP import Ui_help_popup
from sk_tools import *

fmt_error_msg = f'''
# NOTE: This markdown translation has some issues. 
See the [github repo]({GITHUB_URL}) for correct formatting\n
'''
class Help_Popup(QtWidgets.QWidget):
    
    def __init__(self) -> None:
        super().__init__()
        vprint("OPENING LOG VIEWER", color = 'green')
        self.ui = Ui_help_popup()
        self.ui.setupUi(self)

        help_text = ""
        with open("readme.md", 'r') as file:
            file_text = file.read().split("# Usage:")[1].split("# Possible Future Features / Fixes")[0]
            file_text = remove_from_string(file_text, ['<details open>', '<details closed>', '</details>'])
            help_text = fmt_error_msg + file_text

        self.ui.textEdit_file.setMarkdown(help_text)
        
    def keyPressEvent(self, event):  # Escape key functionality
        key = event.key()
        if (key == QtCore.Qt.Key_Escape):
            self.close()

def open_help_popup(self):
    self.window = Help_Popup()
    self.window.show()
    return

