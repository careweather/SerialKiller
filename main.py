#
# MAIN PROGRAM FOR SERIAL KILLER:
#
import subprocess
import sys
import os

from PyQt5.QtGui import QIcon 

install_directory = os.path.split(os.path.abspath(__file__))[0] # path of the install folder 

def dprint(input, *args, color="", enabled=False):
    if enabled:
        dprint.enable = True
    if dprint.enable:
        print(color, end="", flush=True)
        print(input, *args, end="", flush=True)
        print(ENDC, end="", flush=True)

dprint.enable = True

def vprint(input, *args, color="", enabled=None):
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
    print("\n\nERROR:", E)
    import installer
    print("You might be missing one of these modules:")
    for lib in installer.lib_deps:
        print("\t-", lib)
    u_in = input("Install them now? (y/n): ")
    if u_in in ['y', 'Y']:
        installer.install_dependancies()
        print("\nRe-run main.py to begin...")
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

def force_install():
    import installer
    installer.install_dependancies()
    quit()

def print_help():
    help = """
    Useage:

    -u --update     update python GUI files from the UI files
    -q --quit       quit immediately (usually run with update)
    -i --install    force install dependancies
    -h --help       show this. You're already here. 

    for other help, type "help" in the output text box
    """
    print(help)
    quit()

arg_list = {
    '-u': update_UI,
    '--update':update_UI,
    '-q':quit,
    '--quit':quit,
    '-i': force_install, 
    '--install':force_install,
    '-h': print_help,
    '--help':print_help,
}

def execute():
    print("STARTING SERIAL KILLER")
    for sysarg in sys.argv[1:]:
        if sysarg in arg_list: 
            arg_list[sysarg]()
        else: 
            dprint(f"ERROR: ARG {sysarg} INVALID\n", color='\33[31m')
        
    app = QtWidgets.QApplication([sys.argv])
    main = mainWindow.MainWindow()
    main.setWindowIcon(QIcon("img/SK_Icon.png"))
    main.resize(600, 700)
    main.show()
    status = app.exec_()
    sys.exit(status)


if __name__ == "__main__":
    execute()
