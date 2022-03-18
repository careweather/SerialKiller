import subprocess
import sys


def update_ui_files():
    update_ui_commands = [
        "pyuic5 -o gui/GUI_MAIN_WINDOW.py ui_files/serial_killer_main_window.ui",
        "pyuic5 -o gui/GUI_LOG_POPUP.py ui_files/serial_killer_log_popup.ui",
        "pyuic5 -o gui/GUI_HELP_POPUP.py ui_files/serial_killer_help_popup.ui"
    ]
    print("UPDATING FROM UI FILE")
    for command in update_ui_commands:
        print(command, 'white', end='\t', flush=True)
        result = subprocess.call(command, shell=True)
        if result:
            print("FAILURE", 'red')
        else:
            print("SUCCESS", 'green')
    quit()

def install_deps():
    lib_deps = '''\
    numpy
    PyQt5
    pyqtgraph
    pyserial
    termcolor
    '''
    print(f"The following dependancies are required:\n{lib_deps}")

    print(f"Auto Install Dependancies?(y/n): ", end = "", flush=True)
    if input() not in ['Y', 'y']:
        print("----EXITING-----")
        quit()

    install_cmds = [
        "pip install -r requirements.txt",
        'pip install PyQt5-sip --upgrade'
    ]

    install_result = 0

    for cmd in install_cmds:
        print(cmd)
        install_result =  subprocess.call(cmd, shell=True)
        if install_result:
            print("FAILURE")
            quit()
        else:
            print("SUCCESS")
        
    quit()


def execute():
    cl_args = {
        '-u': update_ui_files,
        '-i': install_deps,
    }

    for arg in sys.argv[1:]:
        print(f"ARG: {arg}", 'yellow')
        if arg in cl_args:
            cl_args[arg]()
        else:
            print(f"WARN: ARGUMENT {arg} NOT RECOGNIZED")
    
    run_app()


def run_app():
    try:
        from PyQt5 import QtWidgets
        from termcolor import cprint
        import sk_main_window
        from PyQt5.QtGui import QIcon 
    except Exception as E:
        print("ERROR:", E)
        install_deps()
    cprint("STARTING SERIAL KILLER", 'blue')
    global app
    app = QtWidgets.QApplication(sys.argv)
    main = sk_main_window.MainWindow()
    main.setWindowIcon(QIcon("img/SK_Icon.png"))
    main.resize(600, 700)
    main.show()
    status = app.exec_()
    sys.exit(status)


if __name__ == "__main__":
    execute()
