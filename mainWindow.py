# run this to update from GUI> pyuic5 -o GUI_MAIN.py ui_files/SK2_MainWindow.ui ; pyuic5 -o GUI_LOG.py ui_files/logViewer.ui
import subprocess
import json
import time 
import os
import sys
import command

from PyQt5.QtWidgets import QFileDialog
import loggingTools
from scripting import ScriptWorker
try:
    from gui.GUI_MAIN import Ui_MainWindow  # Local
    from gui.GUI_HELP import Ui_Help
    from PyQt5.QtCore import QObject, QThread, pyqtSignal
    from PyQt5.QtGui import QIntValidator, QTextCursor
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

KEY_SHIFT = 67108864
KEY_UP = 16777235
KEY_DOWN = 16777237
KEY_ENTER = 16777220
KEY_ESCAPE = 16777216

TYPE_INPUT = 0
TYPE_OUTPUT = 1
TYPE_INFO = 2
TYPE_ERROR = 3
TYPE_WARNING = 4

colorBlack = QtGui.QColor(0, 0, 0)
colorRed = QtGui.QColor(218, 0, 0)
colorGreen = QtGui.QColor(24, 160, 0)
colorYellow = QtGui.QColor(166, 157, 0)
colorBlue = QtGui.QColor(0, 0, 255)
colorLightBlue = QtGui.QColor(105, 207, 255)
colorWhite = QtGui.QColor(255, 255, 255)
colorDarkGrey = QtGui.QColor(50, 50, 50)
colorLightGrey = QtGui.QColor(225, 225, 225)

_colorBlack = "rgb(0, 0, 0)"
_colorRed = "rgb(218, 0, 0)"
_colorGreen = "rgb(24, 160, 0)"
_colorYellow = "rgb(166, 157, 0)"
_colorBlue = "rgb(0, 0, 255)"
_colorLightBlue = "rgb(105, 207, 255)"
_colorWhite = "rgb(255, 255, 255)"
_colorDarkGrey = "rgb(50, 50, 50)"
_colorLightGrey = "rgb(225, 225, 225)"

baudRates = [1200, 1800, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 256000]

verbose = True
debug = True

def dprint(input, *args): # for debugging the program
    if debug:
        print(input, *args)


def vprint(input, *args): # verbose prints stuff to terminal 
    if verbose:
        print(input, *args)

script_help = '''
Script Help
-[name] \t run "name".txt
-o \t open script name from directory
-s \t save current script 
-s -[name] \t save current script as "name".txt
-n \t start new script
-t \t jump to script tab
'''


class HelpPopup(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        self.ui = Ui_Help()
        self.ui.setupUi(self)
        text = open('help.md').read()
        self.ui.textBrowser.setMarkdown(text)
        #self.ui.button_repo.clicked.connect(goToRepo)

    def keyPressEvent(self, event):
        if event.key():
            self.close()

class RescanWorker(QObject):  # THIS RESCANS FOR CHANGING PORTS. ASYNC
    disconnected = pyqtSignal(bool)
    updatedPorts = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._active = True

    def run(self):
        lastPorts = ""
        while self._active:
            try:
                ports = SH.getPorts()
                if(ports != lastPorts):
                    lastPorts = ports
                    vprint(ports)
                    self.updatedPorts.emit(ports)
                time.sleep(.5)
            except Exception as E:
                print("Rescan worker Error", E)
                self.disconnected.emit(False)

    def stop(self):
        self._active = False


class SerialWorker(QObject):  # THIS FETCHES SERIAL DATA. ASYNC.
    out = pyqtSignal(str)
    disconnected = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._active = True

    def run(self):
        while self._active:
            try:
                serial_data = SH.getSerialString()
                if(serial_data):
                    dprint(serial_data)
                    self.out.emit(serial_data)
            except Exception as E:
                print(E)
                self._active = False
                self.disconnected.emit(False)

    def stop(self):
        self._active = False

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.is_connected = False
        self.target_port = "COMx"  # Target Port to Connect to
        self.active_baud = 115200
        self.script_active = False
        self.reconnect_active = False
        self.rescan_active = False
        self.all_ports = []
        self.cwd = os.getcwd()
        self.log_dir = "\\logs\\"
        
        self.script_dir = self.cwd + "\\scripts\\"
        self.current_port = ''  # Port Currently Active
        self.historyIndex = 0
        self.currentIndex = 0
        self.lastLine = ""
        self.history = []
        self.output_char = self.ui.lineEdit_sentText.text()
        self.ui.button_clear.clicked.connect(self.clear_terminal)
        self.ui.button_send.clicked.connect(self.send_clicked)
        self.ui.button_rescan.clicked.connect(self.update_ports)
        self.ui.checkBox_autoRescan.clicked.connect(self.auto_rescan_toggled)
        self.ui.checkbox_autoReconnect.stateChanged.connect(self.auto_reconnect_toggled)
        self.ui.button_runScript.clicked.connect(self.start_script)
        self.ui.button_loadScript.clicked.connect(lambda: self.handle_script('o'))
        self.ui.button_saveScript.clicked.connect(lambda: self.handle_script('s'))
        for rate in baudRates:
            self.ui.combobox_baud.addItem(str(rate))
        self.ui.combobox_baud.setCurrentIndex(8)  # 115200
        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.lineEdit_input.setFocus()
        self.cmd = command.commands()
        self.cmd.add_command("con", self.connect, "connect")
        self.cmd.add_command("dcon", self.disconnect, "disconnect")
        self.cmd.add_command("quit", quit, "quit")
        self.cmd.add_command("clear", self.clear_terminal, "clear")
        self.cmd.add_command("com", self.connect, "clear", parse="none")
        self.cmd.add_command("log", self.open_log, "", parse="dash")
        self.cmd.add_command("script", self.handle_script, "start script", parse="dash")
        self.cmd.add_command("auto", self.ui.checkbox_autoReconnect.toggle)
        self.cmd.add_command("help", self.open_help)
        self.cmd.add_command("scan", self.update_ports)
        self.cmd.add_command("new", self.new_window)
        self.cmd.add_command("save", self.save_settings)
        self.cmd.add_command("load", self.load_settings)
        self.cmd.add_command("baud", self.update_baud, parse="none")
        self.cmd.add_command("terminal", lambda: self.ui.tabWidget.setCurrentIndex(0))
        self.load_settings()
        self.update_ports()
        self.command_char = self.ui.lineEdit_commandChar.text()
        self.auto_rescan_toggled()

    def startPlot(self):
        self.ui.widget_plot.startLineGraph()

    def updatePlot(self): 
        self.ui.widget_plot.updateLineData()
    
    def testPlot(self):
        self.ui.widget_plot.testUpdate()

    def open_help(self):
        self.help = HelpPopup()
        self.help.show()

    def keyPressEvent(self, keypress: QtGui.QKeyEvent) -> None:
        key = keypress.key()
        modifiers = int(keypress.modifiers())
        if self.script_active and key == KEY_ESCAPE:
            self.end_script()
       
        dprint("key", key, "modifiers", modifiers)
        if self.ui.lineEdit_input.hasFocus():
            if key == KEY_ENTER:  # send
                self.send_clicked()
                return
            elif key == KEY_UP:
                
                if len(self.history) > 0:
                    self.currentIndex -= 1
                    if (self.currentIndex < 0):
                        self.currentIndex = 0
                    self.ui.lineEdit_input.setText(
                        self.history[self.currentIndex])
            elif key == KEY_DOWN:
                self.currentIndex += 1
                if (self.currentIndex >= self.historyIndex):
                    self.currentIndex = self.historyIndex
                    self.ui.lineEdit_input.clear()
                else:
                    self.ui.lineEdit_input.setText(
                        self.history[self.currentIndex])
        elif key == KEY_ESCAPE: 
            if self.script_active:
                self.end_script()
            self.ui.lineEdit_input.setFocus()
        if key == 44 and modifiers == 67108864: #Ctrl + <
            current_tab = self.ui.tabWidget.currentIndex()
            if current_tab > 0: 
                self.ui.tabWidget.setCurrentIndex(current_tab-1)
            return
        elif key == 46 and modifiers == 67108864: #Ctrl + >
            current_tab = self.ui.tabWidget.currentIndex()
            if current_tab < 3: 
                self.ui.tabWidget.setCurrentIndex(current_tab+1)
                return
        elif self.ui.combobox_port.hasFocus():
            if key == KEY_ENTER: 
                self.connect(target = self.ui.combobox_port.currentText()[3:])
                self.ui.lineEdit_input.setFocus()
                pass
        



       

    def load_settings(self):
        try:
            with open("user_settings.json", "r") as file:
                user_settings = json.load(file)
                self.ui.lineEdit_commandChar.setText(user_settings['commandChar'])
                self.ui.checkbox_autoscroll.setChecked(user_settings["autoscroll"])
                self.ui.checkbox_autoReconnect.setChecked(user_settings["autoreconnect"])
                all_ports = [self.ui.combobox_port.itemText(i) for i in range(self.ui.combobox_port.count())]
                self.ui.lineEdit_delay.setText(user_settings['scriptdelay'])
                self.ui.textEdit_script.setPlainText(user_settings['script'])
                self.target_port = user_settings['port']
                if (user_settings["port"] in all_ports):
                    self.ui.combobox_port.setCurrentText(user_settings["port"])

        except Exception as E:  # needed for the first time the program is run.
            print(E)
            self.save_settings()

    def save_setting(self, keyword, value):
        pass

    def save_settings(self):  # Save ALL settings
        user_settings = {} 
        user_settings['logpath'] = self.ui.lineEdit_logPath.text()
        user_settings['port'] = self.ui.combobox_port.currentText()
        user_settings['baud'] = self.ui.combobox_baud.currentText()
        user_settings['commandChar'] = self.ui.lineEdit_commandChar.text()
        user_settings['autoscroll'] = self.ui.checkbox_autoscroll.isChecked()
        user_settings['autoreconnect'] = self.ui.checkbox_autoReconnect.isChecked()
        user_settings['autolog'] = self.ui.checkbox_autoLog.isChecked()
        user_settings['scriptdelay'] = self.ui.lineEdit_delay.text()
        user_settings['script'] = self.ui.textEdit_script.toPlainText()
        vprint("[SAVING SETTINGS]", user_settings)
        with open("user_settings.json", "w") as file:
            json.dump(user_settings, file)

    def add_text(self, text, type=TYPE_INPUT):  # add text to terminal
        if text[0] == "#":
            print("ext cmd:",text[1:-1])
            self.cmd.check(text[1:-1])
            return
        self.ui.terminalport.moveCursor(QTextCursor.End)
        if type == TYPE_OUTPUT:
            text = self.output_char + text
            self.ui.terminalport.setTextColor(colorBlue)
        elif type == TYPE_INFO:
            text = "[" + text + "]\n"
            self.ui.terminalport.setTextColor(colorGreen)
        elif type == TYPE_ERROR:
            text = "[" + text + "]\n"
            self.ui.terminalport.setTextColor(colorRed)
        elif type == TYPE_WARNING:
            text = "[" + text + "]\n"
            self.ui.terminalport.setTextColor(colorYellow)
        else:
            self.ui.terminalport.setTextColor(colorBlack)
            if self.script_active:
                self.script_worker.incoming.emit(text)
            if self.ui.checkBox_graphData.isChecked():
                self.ui.widget_plot.parseBulkData(text)
        self.ui.terminalport.insertPlainText(text)  # add to terminal
        vprint(text)
        loggingTools.addLine(text)
        if self.ui.checkbox_autoscroll.isChecked():
            self.ui.terminalport.ensureCursorVisible()

    def clear_terminal(self):
        self.ui.terminalport.clear()
        self.debug_text()
        self.add_text("Terminal Cleared", type=TYPE_INFO)

    def update_history(self, line=""):
        if line and line is not self.lastLine:
            self.lastline = line
            self.history.append(line)
            self.historyIndex += 1
            self.currentIndex = self.historyIndex

    def send_clicked(self):
        text = self.ui.lineEdit_input.text()
        self.ui.lineEdit_input.clear()
        self.update_history(text)
        command_char = self.ui.lineEdit_commandChar.text()
        if command_char and text:
            vprint('command_char: ', str(command_char))
            if text[0] == command_char:
                if self.cmd.check(text[1:]):
                    return
                else:
                    self.debug_text(
                        f"ERROR: INVALID COMMAND: {text[1:]}", type=TYPE_ERROR)
                    return
        elif self.cmd.check(text):
            return
        text += '\n'
        if self.is_connected:
            SH.sendString(text)
        else:
            self.debug_text("WARNING: NOT CONNECTED", type=TYPE_ERROR)
        self.add_text(text, type=TYPE_OUTPUT)

    def new_window(self):
        subprocess.call('start pythonw.exe .\main.py', shell=True)

    def debug_text(self, text="", type=TYPE_INFO):
        if type == TYPE_WARNING:
            self.ui.label_debug.setStyleSheet(f"color:{_colorYellow}")
        if type == TYPE_INFO:
            self.ui.label_debug.setStyleSheet(f"color:{_colorBlack}")
        if type == TYPE_ERROR:
            self.ui.label_debug.setStyleSheet(f"color:{_colorRed}")
        self.ui.label_debug.setText(text)

    def update_ports(self, ports = ""):
        if ports:
            lost = set(self.all_ports).difference(set(ports))
            added = set(ports).difference(set(self.all_ports))
            if lost: 
                self.debug_text(f"Lost: {lost}")
            if added:
                self.debug_text(f"Found: {added}")
            self.all_ports = ports
        else: 
            self.all_ports = SH.getPorts()
            vprint(f"Ports: {self.all_ports}")
            self.debug_text(f"Found Ports: {self.all_ports}")
       
        self.ui.combobox_port.clear()
        for port in self.all_ports:
            self.ui.combobox_port.addItem(port)
        if self.target_port in self.all_ports:
            self.ui.combobox_port.setCurrentText(self.target_port)
            if self.reconnect_active: 
                self.connect(self.target_port[3:])

    def auto_reconnect_toggled(self):
        if self.ui.checkbox_autoReconnect.isChecked():
            dprint("Auto Reconnect On")
            self.reconnect_active = True
            self.ui.portsLabel.setText(f"Ports: (Auto {self.target_port})")
        else: 
            self.ui.portsLabel.setText(f"Ports:")
            self.reconnect_active = False
            dprint("Auto off")

    def auto_rescan_toggled(self): 
        if self.ui.checkBox_autoRescan.isChecked():
            self.rescan_active = True
            self.rescan_thread = QThread()
            self.rescan_worker = RescanWorker()
            self.rescan_worker.moveToThread(self.rescan_thread)
            self.rescan_thread.started.connect(self.rescan_worker.run)
            self.rescan_worker.updatedPorts.connect(self.update_ports)
            self.rescan_thread.start()
        else:
            if self.rescan_active: 
                self.rescan_worker.stop()

    def update_baud(self, target_rate = "115200"):
        baud = int(target_rate)
        vprint("Updating Baud Rate:",baud)
        if baud in baudRates: 
            self.debug_text(f"Baud Set to {baud}")
            self.ui.combobox_baud.setCurrentText(str(baud))
        else: 
            self.debug_text(f"Baud Rate {baud} Invalid!")
        
        
    def connect(self, target="", intentional=True):
        vprint("Connecting to:", target)
        if intentional:
            vprint('self.current_port: ', str(self.current_port))
            if target:
                if target.isnumeric():
                    target = "COM" + target
                elif target == '?': 
                    self.ui.combobox_port.showPopup()
                    self.ui.combobox_port.setFocus()
                    return
                else:
                    self.debug_text(
                        f"ERROR: Invalid Port Name: COM{target}", TYPE_ERROR)
                    return
                if target in self.all_ports:
                    self.target_port = target
                else:
                    self.debug_text(
                        f"ERROR: Port {target} Not Found", TYPE_ERROR)
                    return
            else:
                self.target_port = self.ui.combobox_port.currentText()
                dprint("Port from Dropdown:", self.target_port)

        if self.is_connected == False:
            if (SH.makeConnection(port=self.target_port, baud=self.active_baud)):
                self.is_connected = True
                self.current_port = self.target_port
                self.debug_text(f"Connected to {self.target_port}", TYPE_INFO)
                self.add_text(
                    f"Connected To {self.target_port} at {self.active_baud}", TYPE_INFO)
                self.ui.combobox_port.setCurrentText(self.target_port)
                self.ui.terminalport.setEnabled(True)
                self.ui.terminalport.setStyleSheet(
                    f"background-color:{_colorWhite}")
                self.ui.button_connect.setStyleSheet(
                    f"background-color:{_colorGreen}")
                self.ui.button_connect.setText("Disconnect")
                loggingTools.setPort(self.target_port)
                loggingTools.startLogger()
                self.serial_thread = QThread()
                self.serial_worker = SerialWorker()
                self.serial_worker.moveToThread(self.serial_thread)
                self.serial_thread.started.connect(self.serial_worker.run)
                self.serial_worker.out.connect(self.add_text)
                self.serial_worker.disconnected.connect(self.disconnect)
                self.serial_thread.setTerminationEnabled(True)
                self.serial_thread.start()
            else:
                self.debug_text(
                    "ERROR: PORT COULD NOT CONNECT!", type=TYPE_ERROR)
        elif self.current_port != self.target_port:
            vprint("Changing Ports")
            self.disconnect()
            self.connect(target=self.target_port[3:])
        else:
            self.debug_text("WARNING: Already Connected!")

    def disconnect(self, intentional=True):
        if self.is_connected:
            self.add_text(
                f"Disconnecting From: {self.current_port}", TYPE_ERROR)
            self.debug_text(
                f"Disconnecting from: {self.current_port}", TYPE_WARNING)
            self.serial_worker.stop()
            self.serial_thread.exit()
            SH.closePort()
            self.is_connected = False
            loggingTools.setPort()
            loggingTools.startLogger()
            self.ui.button_connect.setText("Connect")
            self.ui.button_connect.setStyleSheet(
                f"background-color:{_colorYellow}")
            self.ui.terminalport.setStyleSheet(
                f"background-color: {_colorLightGrey}")
            if intentional:
                self.ui.checkbox_autoReconnect.setChecked(False)
        else:
            self.debug_text("WARNING: Already Disconnected!", TYPE_WARNING)
            vprint("ERROR: NOT CONNECTED")

    def open_log(self, arg=""):
        if type(arg) == list:
            arg = arg[0]
        if not arg:
            loggingTools.LogViewPopup(self)
        elif arg in ["l", 'L', 'latest']:
            loggingTools.LogViewPopup(self, latest=True)
        elif arg in ['n', 'new', 'N']:
            self.debug_text("Archiving Log:")
            loggingTools.archiveLog()
        elif not (loggingTools.LogViewPopup(self, filename=arg)):
            self.debug_text(f"ERROR: Log {arg} not found!", type=TYPE_ERROR)

    def get_file(self, start="", location="", title="Open"):
        options = QFileDialog.Options()
        dprint('start: ', str(start))
        files = QFileDialog.getOpenFileName(self, "OPEN", start)
        dprint(' files[0]: ', str(files[0]))
        return files[0]

    def save_file(self, start, name="", content="", title="Save As", ext="*.txt"):
        vprint("file save name:", name)
        if name != "":
            file_name = start + name + ext[1:]
        else:
            options = QFileDialog.Options()
            files = QFileDialog.getSaveFileName(self, title, start, ext, options=options)
            file_name = files[0]
        try:
            vprint("Saving to: ", file_name)
            with open(file_name, 'w') as file:
                file.write(content)
                file.close()
            return file_name
        except Exception as e:
            vprint("ERROR IN SAVING FILE: ", e)
            return ""

    def handle_script(self, *args):
        vprint('args: ', str(args), type(args))
        if not args:
            self.start_script()
            return
        script_open = False
        script_save = False
        script_name = ""
        for arg in args:
            vprint("arg ", arg)
            if arg in ['n', 'N', "new"]:
                self.ui.tabWidget.setCurrentIndex(1)
                self.ui.textEdit_script.clear()
                self.ui.textEdit_script.setFocus(True)
                return
            elif arg in ['t', 'T']:
                self.ui.tabWidget.setCurrentIndex(1)
                self.ui.textEdit_script.setFocus(True)
                return
            elif arg in ['o', 'O', 'open']:
                script_open = True
                script_save = False
                vprint("opening Script")
            elif arg in ['h', 'H', 'help']:
                self.add_text(script_help, type=TYPE_OUTPUT)
                return
            elif arg in ['save', 's', 'S']:
                script_save = True
                script_open = False
                vprint("saving script")
            elif arg: 
                script_name = arg
                vprint("script name: ", script_name)
        if script_save:
            script_text = self.ui.textEdit_script.toPlainText()
            self.save_file(self.script_dir, script_name, script_text)
            return
        if script_open and script_name == "":
            script_path = self.get_file(self.script_dir)
        else: 
            script_path = self.script_dir + script_name + '.txt'
        if os.path.exists(script_path):
            print("Script Exists:", script_path)
            with open(script_path) as file: 
                text = file.read()
            self.ui.textEdit_script.setPlainText(text)
            self.start_script(text = text)
            return
        else:
            self.debug_text(f"ERROR: Script {script_path} not found!", type=TYPE_ERROR)
        
    def start_script(self, text = False):
        if text == False:
            text = self.ui.textEdit_script.toPlainText()
        if self.script_active == False:
            self.script_active = True
            wait = self.ui.lineEdit_delay.text()
            if not wait:
                wait = 420
            self.ui.tabWidget.setCurrentIndex(0)
            self.ui.lineEdit_input.setDisabled(True)
            self.ui.button_send.setDisabled(True)
            self.script_thread = QThread()
            self.script_worker = ScriptWorker(text, wait)
            self.script_worker.moveToThread(self.script_thread)
            self.script_thread.started.connect(self.script_worker.run)
            self.script_worker.line.connect(self.script_line)
            self.script_worker.finished.connect(self.end_script)
            self.script_thread.start()
        else:
            self.debug_text("ERROR: Script already active", type=TYPE_ERROR)

    def script_line(self, line):
        line.replace("\n", "")
        print("SCRIPT LINE:", line)
        self.ui.lineEdit_input.setText(line)
        self.send_clicked()
        self.ui.lineEdit_input.setText(line)

    def script_wait(self): 
        pass


    def end_script(self):
        vprint("Ending Script")
        self.script_active = False
        self.script_worker.stop()
        self.script_thread.exit()
        self.debug_text("Script Ended")
        self.ui.lineEdit_input.clear()
        self.ui.lineEdit_input.setDisabled(False)
        self.ui.button_send.setDisabled(False)
        self.ui.lineEdit_input.setFocus()
        self.scriptActive = False

    def update_delay(self, delay=100):
        if self.script_active:
            self.ui.lineEdit_delay.setText(str(delay))


# ***********************************************************************************************************
updateCommands = [
    "pyuic5 -o GUI_MAIN.py ui_files/mainWindow.ui",
    "pyuic5 -o GUI_LOG.py ui_files/logViewer.ui",
    "pyuic5 -o GUI_HELP.py ui_files/helpPopup.ui"
]

def update_UI():
    print("UPDATING FROM UI FILE")
    for command in updateCommands:
        print(command)
        subprocess.call(command, shell=True)

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
        'arg': ['-q', '-quit'],
        'funct': quit,
    },
     {
        'arg': ['-v', '-verbose'],
        'funct': toggle_verbose,
    },
]


def execute():
    print("STARTING SERIAL KILLER")
    app = QtWidgets.QApplication([sys.argv])
    dprint("Argument List:", str(sys.argv))
    for sysarg in sys.argv[1:]:
        for argument in argList:
            if sysarg in argument['arg']:
                funct = argument['funct']
                funct()

    main = MainWindow()
    main.show()
    status = app.exec_()
    sys.exit(status)


if __name__ == "__main__":
    execute()
