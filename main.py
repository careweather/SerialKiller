#
# MAIN PROGRAM FOR SERIAL KILLER: 
#

import subprocess
import sys



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






try:
    import mainWindow
    from PyQt5 import QtGui, QtWidgets
except Exception as E:
    print("ERROR", E)
    u_in = input("Install them now? (y/n):")
    if u_in in ['y', 'Y']: 
        import installer
        installer.install_dependancies()
        print("Re-run to begin...")
        quit()
    else: 
        print("EXITING...")
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

argList = [  # THIS IS ALL COMMANDS AND ARGS
    {
        'arg': ['-u', '-update'],
        'funct': update_UI,
    },
    {
        'arg': ['-q', '-quit'],
        'funct': quit,
    },
]

def execute():
    print("STARTING SERIAL KILLER")
    for sysarg in sys.argv[1:]:
        print("Argument", sysarg)
        for argument in argList:
           if sysarg in argument['arg']:
               funct = argument['funct']
               funct()
    app = QtWidgets.QApplication([sys.argv])
    main = mainWindow.MainWindow()
    main.resize(550,700)
    main.show()
    status = app.exec_()
    sys.exit(status)
    
if __name__ == "__main__":
    execute()
