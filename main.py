import subprocess
import sys
try:
    from PyQt5 import QtGui, QtWidgets
    import serialHandler as SH
except Exception as E:
    print('''
    -- ERROR --
    Missing some Lib Dependancies!''')
    print(E)
    print('''
    Make sure the following packages are installed:
    pyqtgraph   - pip install pyqtgraph
    pyqt5       - pip install pyqt5
    pyqt5-tools - pip install pyqt5-tools
    pySerial    - pip install pyserial''')
    quit()

updateCommands = [
    "pyuic5 -o gui/GUI_MAIN.py ui_files/mainWindow.ui",
    "pyuic5 -o gui/GUI_LOG.py ui_files/logViewer.ui",
    "pyuic5 -o gui/GUI_HELP.py ui_files/helpPopup.ui"
]

def update_UI():
    print("UPDATING FROM UI FILE")
    for command in updateCommands:
        print(command, end=" ", flush=True)
        result = subprocess.call(command, shell=True)
        if not result: 
            print("Success")

def toggle_verbose():
    global verbose, debug
    verbose = False
    debug = False
    
argList = [  # THIS IS ALL COMMANDS AND ARGS
    {
        'arg': ['-u', '-update'],
        'funct': update_UI,
    },
     {
        'arg': ['-v', '-verbose'],
        'funct': toggle_verbose,
    },
    {
        'arg': ['-q', '-quit'],
        'funct': quit,
    },
]

def execute():
    print("STARTING SERIAL KILLER")
    for sysarg in sys.argv[1:]:
       for argument in argList:
           if sysarg in argument['arg']:
               funct = argument['funct']
               funct()
    from mainWindow import MainWindow           
    app = QtWidgets.QApplication([sys.argv])
    main = MainWindow()
    main.show()
    status = app.exec_()
    sys.exit(status)
    
    
    #dprint("Argument List:", str(sys.argv))
    

if __name__ == "__main__":
    execute()
