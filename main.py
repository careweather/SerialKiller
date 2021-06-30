# run this to update from GUI> pyuic5 -o GUI_MAIN.py ui_files/SK2_MainWindow.ui ; pyuic5 -o GUI_LOG.py ui_files/logViewer.ui

from re import T
from PyQt5.QtGui import QIntValidator, QTextCursor
import subprocess
import json
import time 
import os
import sys
from datetime import datetime

import command

from PyQt5.QtWidgets import QFileDialog, QTableWidget, QTableWidgetItem
import loggingTools
import getopt
try:
    import serialHandler as SH
    import scripting
    from GUI_MAIN import Ui_MainWindow  # Local
    from GUI_HELP import Ui_Help
    from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer
    from PyQt5 import QtGui, QtWidgets
    import serialHandler as SH
except Exception as E:
    print('''
    -- ERROR --
    Missing some Lib Dependancies!''')
    print(E)
    print('''
    Make sure the following packages are installed:
    pyqt5       - pip install pyqt5
    pyqt5-tools - pip install pyqt5-tools
    pySerial    - pip install pyserial''')
    quit()


KEY_UP = 16777235
KEY_DOWN = 16777237
KEY_ENTER = 16777220

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

open_words = ['o', 'O', 'Open', 'open']
new_words = ['n', 'N', 'new', 'New']


verbose = True
debug = True


def dprint(input, *args):
    if debug:
        print("DEBUG: ", input, *args, sep='')


def vprint(input, *args):
    if verbose:
        print(input, *args, sep='')

    def stop(self):
        self._active = False
        # self.finished.emit(True)


class ScriptWorker(QObject):
    line = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, text, delay=100):
        super().__init__()
        self.update_delay(delay)
        self.script = []
        self.script = text.splitlines(False)
        self._active = True
        self.sleepTime = 0

    def update_delay(self, delay="100"):
        delay = int(delay)
        self.delay = delay/1000

    def run(self):
        for sline in self.script:
            if(self._active):
                self.line.emit(sline)
                time.sleep(self.delay)                
            else:
                self.finished.emit(True)
        self.finished.emit(True)

    def stop(self):
        self._active = False
        # self.finished.emit(True)


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
    needUpdate = pyqtSignal(bool)

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
                    print(ports)
                    self.needUpdate.emit(True)
                time.sleep(.5)
            except Exception as E:
                print(E)
                self.disconnected.emit(False)

    def stop(self):
        pass
        #self._active = False


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
                self.disconnected.emit(False)

    def stop(self):
        self._active = False


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.is_connected = False
        self.target_port = "COM0"  # Target Port to Connect to
        self.active_baud = 115200
        self.script_active = False
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
        self.load_settings()
        self.update_ports()

    def open_help(self):
        self.help = HelpPopup()
        self.help.show()


    def keyPressEvent(self, event):
        key = event.key()
        modifiers = int(event.modifiers())
        if self.ui.lineEdit_input.hasFocus():
            # print(key)
            if key == KEY_ENTER:  # send
                self.send_clicked()
            elif key == KEY_UP:
                print(self.currentIndex)
                print(self.historyIndex)
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

    def load_settings(self):
        pass

    def save_setting(self, keyword, value):
        pass

    def save_settings(self):  # Save ALL settings
        pass

    def add_text(self, text, type=TYPE_INPUT):  # add text to terminal
        self.ui.terminalport.moveCursor(QTextCursor.End)
        if type == TYPE_OUTPUT:
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
            print('command_char: ', str(command_char))
            if text[0] == command_char:
                if self.cmd.check(text[0:]):
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
        text = self.output_char + text
        self.add_text(text, type=TYPE_OUTPUT)

    def debug_text(self, text="", type=TYPE_INFO):
        if type == TYPE_WARNING:
            self.ui.label_debug.setStyleSheet(f"color:{_colorYellow}")
        if type == TYPE_INFO:
            self.ui.label_debug.setStyleSheet(f"color:{_colorBlack}")
        if type == TYPE_ERROR:
            self.ui.label_debug.setStyleSheet(f"color:{_colorRed}")
        self.ui.label_debug.setText(text)

    def update_ports(self, auto=False):
        self.all_ports = SH.getPorts()
        if not auto:
            vprint(f"Ports: {self.all_ports}")
            self.debug_text(f"Found Ports: {self.all_ports}")
        for port in self.all_ports:
            self.ui.combobox_port.addItem(port)
        if self.target_port in self.all_ports:
            self.ui.combobox_port.setCurrentText(self.target_port)

    def connect(self, target="", intentional=True, auto=False):
        vprint("Connecting to:", target)
        args = []
        if intentional:
            print('self.current_port: ', str(self.current_port))
            if target:
                if target.isnumeric():
                    target = "COM" + target
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
            print("Changing Ports")
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
            if arg in ['o', 'O', 'open']:
                script_open = True
                script_save = False
                vprint("opening Script")
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
        
    def start_script(self, text = ""):
        if text == "":
            text = self.ui.textEdit_script.toPlainText()
        if self.script_active == False:
            self.script_active = True
            self.ui.tabWidget.setCurrentIndex(0)
            self.ui.lineEdit_input.setDisabled(True)
            self.ui.button_send.setDisabled(True)
            self.script_thread = QThread()
            self.script_worker = ScriptWorker(text=text)
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
        if line[0:4] == "wait":
            self.script_worker.update_delay(int(line[4:]))
        self.send_clicked()

    def end_script(self):
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
        subprocess.call(command, shell=True)


argList = [  # THIS IS ALL COMMANDS AND ARGS
    {
        'arg': ['-u', '-update'],
        'funct': update_UI,
    },
]


def execute():
    app = QtWidgets.QApplication([sys.argv])
    print("Argument List:", str(sys.argv))
    for sysarg in sys.argv[1:]:
        for argument in argList:
            if sysarg in argument['arg']:
                funct = argument['funct']
                funct()

    main = MainWindow()
    main.show()
    app.exec_()


if __name__ == "__main__":
    execute()
