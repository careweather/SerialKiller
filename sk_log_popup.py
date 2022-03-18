import datetime
import os
from datetime import datetime

from PyQt5 import QtCore, QtWidgets

from gui.GUI_LOG_POPUP import Ui_logViewer



class Log_Viewer(QtWidgets.QWidget):
    def __init__(self, log_file:str) -> None:
        super().__init__()
        
        self.log_file = log_file
        self.ui = Ui_logViewer()
        self.ui.setupUi(self)
        
        last_modified = datetime.fromtimestamp(os.path.getmtime(log_file)).strftime("%m/%d/%Y %H:%M:%S")
        self.ui.label_last_updated.setText(last_modified)
        self.ui.label_log_name.setText(self.log_file)

        text = open(self.log_file).read()
        
        self.ui.textEdit_file.insertPlainText(text)
        self.ui.textEdit_file.ensureCursorVisible()

        self.ui.textEdit_file.ensureCursorVisible()
        self.ui.label_debugText.setText("")
        
    def keyPressEvent(self, event):  # Escape key functionality
        key = event.key()
        if (key == QtCore.Qt.Key_Escape):
            self.close()

def open_log_viewer(self, log_file):
    
    self.window = Log_Viewer(log_file)
    
    self.window.resize(800,600)
    self.window.show()
    return


    


