import subprocess
import sys
from sk_tools import DEBUG_LEVEL

def update_ui_files():
    from sk_tools import INSTALL_FOLDER
    update_ui_commands = [
        f"pyuic5 -o {INSTALL_FOLDER}/gui/GUI_MAIN_WINDOW.py {INSTALL_FOLDER}/ui_files/serial_killer_main_window.ui",
        f"pyuic5 -o {INSTALL_FOLDER}/gui/GUI_LOG_POPUP.py {INSTALL_FOLDER}/ui_files/serial_killer_log_popup.ui",
        f"pyuic5 -o {INSTALL_FOLDER}/gui/GUI_HELP_POPUP.py {INSTALL_FOLDER}/ui_files/serial_killer_help_popup.ui"
    ]
    print("UPDATING FROM UI FILES")
    for command in update_ui_commands:
        print(command)
        error = subprocess.call(command, shell=True)
        if error:
            print("-----FAILURE")
            quit()
        else:
            print("-----SUCCESS")
    print("ALL GUI FILES UPDATED. RUN AGAIN TO START SERIAL KILLER")
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

    print(f"Auto Install Dependancies?(y/n): ", end="", flush=True)
    if input() not in ['Y', 'y']:
        print("----EXITING-----")
        quit()

    install_cmds = [
        "pip install -r requirements.txt",
        'pip install PyQt5-sip --upgrade'
    ]

    for cmd in install_cmds:
        print(cmd)
        install_result = subprocess.call(cmd, shell=True)
        if install_result:
            print("FAILURE")
            quit()
        else:
            print("SUCCESS")

    quit()


def show_help():
    help_str = '''\
Usage:
    py serial_killer.py [options]
    
Options:
  -h, --help      show this help message
  -u, --update    update python GUI files from .ui files
  -i, --install   force install library dependancies
  -v, --verbose   print verbose messages (useful for debugging)
  -x <size>       set the window X size (pixels) default: 600
  -y <size>       set the window Y size (pixels) default: 700
  -c <command>    open serial killer with a command <command>
  '''
    print(help_str)
    quit()


def execute():
    x_size = 600
    y_size = 700
    open_cmd = ""
    
    
    input_args = sys.argv[1:]
    while input_args:
        arg = input_args.pop(0)
        if arg == '-y':
            y_size = int(input_args.pop(0))
        elif arg == '-x':
            x_size = int(input_args.pop(0))
        elif arg == '-c':
            open_cmd = input_args.pop(0)
        elif arg == '-u' or arg == '--update':
            update_ui_files()
        elif arg == '-i' or arg == '--install':
            install_deps()
        elif arg == '-h' or arg == '--help':
            show_help()   
        elif arg == '-v' or arg == '--verbose':
            import sk_tools
            sk_tools.DEBUG_LEVEL = 2
        else:
            print(f"-----\nWARNING: ARGUMENT {arg} NOT RECOGNIZED\n------")
            show_help()

    run_app(x_size, y_size, open_cmd)

def run_app(size_x = 600, size_y = 700, open_cmd = ""):
    try:
        from PyQt5 import QtWidgets
        from termcolor import cprint
        import sk_main_window
        from PyQt5.QtGui import QIcon
        from sk_tools import GITHUB_URL
    except Exception as E:
        print("ERROR:", E)
        install_deps()
    from sk_help import GREETINGS_TEXT
    cprint(GREETINGS_TEXT, color='cyan')
    global app
    app = QtWidgets.QApplication(sys.argv)
    main = sk_main_window.MainWindow(open_cmd=open_cmd)
    main.setWindowIcon(QIcon("img/SK_Icon.png"))
    main.resize(size_x, size_y)
    main.show()
    status = app.exec_()
    sys.exit(status)


if __name__ == "__main__":
    execute()
