#
# MAIN PROGRAM FOR SERIAL KILLER:
#
import subprocess
import sys
import os

try:
    from sk_tools import *
    from PyQt5.QtGui import QIcon
    import mainWindow
    from PyQt5 import QtGui, QtWidgets
except Exception as E:
    colorPrint("\nERROR", E, color='red')
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

gui_update_commands = [
    "pyuic5 -o gui/GUI_MAIN.py ui_files/mainWindow.ui",
    "pyuic5 -o gui/GUI_LOG.py ui_files/logViewer.ui",
    "pyuic5 -o gui/GUI_HELP.py ui_files/helpPopup.ui"
]


def update_UI():
    print("UPDATING FROM UI FILE")
    for command in gui_update_commands:
        cprint(f"{command}", 'white', end="  \t", flush=True)
        result = subprocess.call(command, shell=True)
        if not result:
            cprint("SUCCESS", 'green')


def force_install():
    import installer
    installer.install_dependancies()
    quit()


cl_args = {}

def print_help():
    print("Useage:")

    for arg in cl_args:
        print(f"\t{arg}\t{cl_args[arg]['help']}")
    
    quit()


cl_args = {
    '-u': {
        'func': update_UI,
        'help': "update from the latest .ui files"
    },
    '-q': {
        'func': quit,
        'help': 'quit immediately'
    },
    '-i': {
        'func': force_install,
        'help': 'force install all dependancies'
    },
    '-h': {
        'func': print_help,
        'help': 'print this help message'
    }
}

# arg_list = {
#     '-u': update_UI,
#     '--update': update_UI,
#     '-q': quit,
#     '--quit': quit,
#     '-i': force_install,
#     '--install': force_install,
#     '-h': print_help,
#     '--help': print_help,
# }


def execute():
    print("STARTING SERIAL KILLER")


    for arg in sys.argv[1:]:
        if arg in cl_args:
            this_arg = cl_args[arg]
            if 'func' in this_arg:
                this_arg['func']()
        else:
            cprint(f"\nERROR: CL ARG '{arg}' NOT VALID", 'red')
            quit()

    app = QtWidgets.QApplication([sys.argv])
    main = mainWindow.MainWindow()
    main.setWindowIcon(QIcon("img/SK_Icon.png"))
    main.resize(600, 700)
    main.show()
    status = app.exec_()
    sys.exit(status)


if __name__ == "__main__":
    execute()
