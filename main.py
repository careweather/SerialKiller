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

ENDC = '\033[0m '

def update_UI():
    print("UPDATING FROM UI FILE")
    for command in updateCommands:
        result = subprocess.call(command, shell=True)
        if not result: 
            print("Success")


_verbose = False
_debug = False




def _dprint(input, *args, color = ""): # for debugging the program
    pass
    #global _debug
    


def _vprint(input, *args, color = ""): # verbose prints stuff to terminal 
    pass
    #global _verbose
    


def dprint(input, *args, color = "", enabled = False): 
    if enabled: 
        dprint.enable = True
    if dprint.enable:
        print(color, end="", flush=True)
        print(input, *args, end="", flush=True)
        print(ENDC, end="", flush=True)

dprint.enable = True

def vprint(input, *args, color = "", enabled = None):
    if enabled: 
        vprint.enable = True
    if vprint.enable:
        print(color, end="", flush=True)
        print(input, *args, end="", flush=True)
        print(ENDC, end="", flush=True)

vprint.enable = True

def toggle_verbose(): 
    vprint.enable = True
    dprint.enable = True

print("V:", _verbose, "D:", _debug)

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
    from mainWindow import MainWindow   
    print("STARTING SERIAL KILLER")
    for sysarg in sys.argv[1:]:
        print("Argument", sysarg)
        for argument in argList:
           if sysarg in argument['arg']:
               funct = argument['funct']
               funct()
    
    print("verbose", _verbose)
    print("debug", _debug)
    app = QtWidgets.QApplication([sys.argv])
    main = MainWindow()
    main.show()
    status = app.exec_()
    sys.exit(status)
    
    


if __name__ == "__main__":
    execute()
