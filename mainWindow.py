# run this to update from GUI> pyuic5 -o GUI_MAIN.py ui_files/SK2_MainWindow.ui ; pyuic5 -o GUI_LOG.py ui_files/logViewer.ui
import subprocess
import json
import time 
from datetime import datetime
import os
import sys
import command
from PyQt5.QtWidgets import QFileDialog
import loggingTools
from scripting import ScriptWorker
from parser_f import Parser, Command
from gui.GUI_MAIN import Ui_MainWindow  # Local
from gui.GUI_HELP import Ui_Help
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QIntValidator, QTextCursor
from PyQt5 import QtGui, QtWidgets
import serialHandler as SH

KEY_SHIFT = 33554432
KEY_UP = 16777235
KEY_DOWN = 16777237
KEY_ENTER = 16777220
KEY_ESCAPE = 16777216
KEY_C = 67
KEY_S = 83
KEY_L_ANGLE = 44
KEY_R_ANGLE = 46
MOD_CTRL = 67108864

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



CBLACK  = '\33[30m'
CRED    = '\33[31m'
CGREEN  = '\33[32m'
CYELLOW = '\33[33m'
CBLUE   = '\33[34m'
CCYAN   = '\033[96m' 
CVIOLET = '\33[35m'
CBEIGE  = '\33[36m'
CWHITE  = '\33[37m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

def dprint(input, *args, color = ""): # for debugging the program
    if debug:
        print(color + input + ENDC, *args)


def vprint(input, *args, color = ""): # verbose prints stuff to terminal 
    if verbose:
        print(color + input + ENDC, *args, end='', flush=True)

script_help = '''
**** SCRIPT HELP ****
Press ESCAPE or CTRL+C to stop a script mid-execution

ARGUMENTS:
(none)\t run script in the script tab
-o [name]\t open a script. Optional: open "name".txt
-r \t run the script you are opening
-s [name] \t save current script. Optional: as "name".txt
-n [name]\t start new script. Optional: include "name" line
-t \t jump to script tab
-ls \t display all scripts in the script dir
-h\t display this help message

SCRIPT SPECIFIC KEYWORDS:
#name=[myName]\tsave the script as "myName".txt every time it's run
#delay=[numb]\tchange the delay between lines to "numb" milliseconds
#loop=[numb]\t\tloop until endloop [numb] times. 
#endloop\t\tend loop and continue with script
#wait\t\twait for serial input before continuing
#stop\t\texit script at this line
# '''

log_help = '''LOG Help
ARGUMENTS:
(none)\topen the last log file avaliable
-o\topen a log file from the directory
-n\tstart a new log and archive the old
-h\tdisplay this help message'''

terminal_placeholder = '''***Serial from device will appear here***

Type "help" for detailed use instructions'''


def get_timestamp(): 

    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    return ts
    millis = time.time() - int(time.time())
    ts = time.strftime("%H:%M:%S", time.gmtime())
    ts + str(millis)
    ts = str(ts) + str(millis)[1:6]
    return ts
    
def add_timestamp(text:str): 
    ts = get_timestamp()
    lines = text.splitlines(True)
    print('lines: ' , str(lines), type(lines))
    ret = ""
    if len(lines) > 1: 
        for line in lines[:-1]: 
            ret = ret + ts + "| " + line 
        #ret += lines[-1]
    else: 
        for line in lines: 
            ret = ret + ts + "| " + line 
    print(ret)
    return ret

class HelpPopup(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Help()
        self.ui.setupUi(self)
        text = open('help.html').read()
        self.ui.textBrowser.setHtml(text)
        #text = open('help.md').read()
        #self.ui.textBrowser.
        #self.ui.textBrowser.setMarkdown(text)

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
                    vprint(str(ports), color=CGREEN)
                    self.updatedPorts.emit(ports)
                time.sleep(1)
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
                #serial_data = SH.getLine()
                if serial_data:
                    vprint(serial_data, color = "")
                    self.out.emit(serial_data)
            except Exception as E:
                print("Serial Worker Error",E)
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
        
        #self.input_char = self.ui.

        self.ui.terminalport.setPlaceholderText(terminal_placeholder)
        self.ui.button_clear.clicked.connect(self.clear_terminal)
        self.ui.button_send.clicked.connect(self.send_clicked)
        self.ui.button_rescan.clicked.connect(self.update_ports)
        self.ui.checkBox_autoRescan.clicked.connect(self.auto_rescan_toggled)
        self.ui.checkbox_autoReconnect.stateChanged.connect(self.auto_reconnect_toggled)
        self.ui.button_runScript.clicked.connect(self.start_script)
        self.ui.button_loadScript.clicked.connect(lambda: self.handle_script(opens=""))
        self.ui.button_saveScript.clicked.connect(lambda: self.handle_script(save=""))
        self.ui.button_connect.clicked.connect(self.connect)
        self.ui.button_viewLogs.clicked.connect(lambda: self.handle_log(open = ""))
        for rate in baudRates:
            self.ui.combobox_baud.addItem(str(rate))
        self.ui.combobox_baud.setCurrentIndex(8)  # 115200
        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.lineEdit_input.setFocus()
        self.ui.checkbox_timestamp.setEnabled(True)
        self.ui.checkbox_timestamp.setCheckable(True)

        self.parser = Parser()
        cmd_connect = Command('com', self.connect, default_kw='target')
        cmd_connect.add_argument('?', 'show', bool, True)
        cmd_connect.add_argument('auto', 'auto', bool, True)
        self.parser.add_command(cmd_connect)
        self.parser.add_command(Command("quit", quit))
        self.parser.add_command(Command("clear", self.clear_terminal))
        self.parser.add_command(Command("help", self.open_help))
        self.parser.add_command(Command("scan", self.update_ports))
        self.parser.add_command(Command("dcon", self.disconnect))
        self.parser.add_command(Command("new", self.new_window))
        self.parser.add_command(Command("save", self.save_settings))
        self.parser.add_command(Command("auto", self.ui.checkbox_autoReconnect.toggle))
        self.parser.add_command(Command("con", self.connect))
        cmd_log = Command("log", self.handle_log, help=log_help)
        cmd_log.add_argument('n', 'name', str)
        cmd_log.add_argument('o', 'open', str, default="")
        cmd_log.add_argument('a', 'archive', str, default="")
        cmd_baud = Command("baud", self.update_baud, 'target_rate', str, default_required=True)
        cmd_script = Command("script", self.handle_script)
        cmd_script.add_argument("o", 'opens', str, default="")
        cmd_script.add_argument("r", 'run', bool, default=True)
        cmd_script.add_argument("s", 'save', str, default="")
        cmd_script.add_argument("t", 'tab', bool, default=True)
        cmd_script.add_argument("n", 'new', str, default="")
        cmd_script.add_argument("d", 'delete', str, default = "")
        cmd_script.add_argument("h", "help", bool, True)
        cmd_script.add_argument("ls", "list", bool, True)
        cmd_save = Command('saves', self.save_setting)
        cmd_save.add_argument("n", 'keyword', str)
        cmd_save.add_argument("v", 'value', str)
        self.parser.add_command(cmd_save)
        self.parser.add_command(cmd_script)
        self.parser.add_command(cmd_baud)
        self.parser.add_command(cmd_log)
        self.load_settings()
        self.input_char = self.ui.lineEdit_receivedText.text()
        self.info_char = self.ui.lineEdit_infoText.text()
        self.warning_char = self.ui.lineEdit_warningText.text()
        self.error_char = self.ui.lineEdit_errorText.text()
        self.output_char = self.ui.lineEdit_sentText.text()
        self.update_ports()
        self.command_char = self.ui.lineEdit_commandChar.text()
        self.auto_rescan_toggled()

    def keyPressEvent(self, keypress: QtGui.QKeyEvent) -> None:
        key = keypress.key()
        modifiers = int(keypress.modifiers())
        #dprint("key", key, "modifiers", modifiers)
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
        if self.script_active: 
            if (key == KEY_C and modifiers == MOD_CTRL) or key == KEY_ESCAPE:  
                self.end_script()
                self.ui.lineEdit_input.setFocus()
        elif key == KEY_ESCAPE: 
            self.ui.lineEdit_input.setFocus()
        if key == KEY_L_ANGLE and modifiers == MOD_CTRL: #Ctrl + <
            current_tab = self.ui.tabWidget.currentIndex()
            if current_tab > 0: 
                self.ui.tabWidget.setCurrentIndex(current_tab-1)
            return
        elif key == KEY_R_ANGLE and modifiers == MOD_CTRL: #Ctrl + >
            current_tab = self.ui.tabWidget.currentIndex()
            if current_tab < 3: 
                self.ui.tabWidget.setCurrentIndex(current_tab+1)
                return
        elif self.ui.combobox_port.hasFocus():
            if key == KEY_ENTER: 
                self.connect(target = self.ui.combobox_port.currentText()[3:])
                self.ui.lineEdit_input.setFocus()
                return
        elif key == KEY_S and modifiers == MOD_CTRL: 
            self.save_settings()
        
    def load_settings(self): # import and apply settings from json
        try:
            with open("user_settings.json", "r") as file:
                user_settings = json.load(file)
                self.ui.lineEdit_commandChar.setText(user_settings['commandChar'])
                self.ui.checkbox_autoscroll.setChecked(user_settings["autoscroll"])
                self.ui.checkbox_autoReconnect.setChecked(user_settings["autoreconnect"])
                all_ports = [self.ui.combobox_port.itemText(i) for i in range(self.ui.combobox_port.count())]
                self.ui.lineEdit_delay.setText(user_settings['scriptdelay'])
                self.ui.textEdit_script.setPlainText(user_settings['script'])
                self.ui.lineEdit_receivedText.setText(user_settings['input_char'])
                self.ui.lineEdit_errorText.setText(user_settings['error_char'])
                self.ui.lineEdit_infoText.setText(user_settings['info_char'])
                self.ui.lineEdit_warningText.setText(user_settings['warning_char'])
                self.ui.lineEdit_sentText.setText(user_settings['output_char'])
                if (user_settings["port"] in all_ports):
                    self.ui.combobox_port.setCurrentText(user_settings["port"])

        except Exception as E:  # needed for the first time the program is run.
            print(E)
            self.save_settings()

    def save_setting(self, keyword, value): # save a single setting
        with open("user_settings.json", "r") as file:
            user_settings = json.load(file)
            dprint("LOADED", user_settings)
        user_settings[keyword] = value 
        dprint("CHANGED TO:", user_settings)
        with open("user_settings.json", "w") as file:
            json.dump(user_settings, file)
        
    
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
        user_settings['input_char'] = self.ui.lineEdit_receivedText.text()
        user_settings['output_char'] = self.ui.lineEdit_sentText.text()
        user_settings['info_char'] = self.ui.lineEdit_infoText.text()
        user_settings['error_char'] = self.ui.lineEdit_errorText.text()
        user_settings['warning_char'] = self.ui.lineEdit_warningText.text()
        vprint("[SAVING SETTINGS]", user_settings, color=CGREEN)
        with open("user_settings.json", "w") as file:
            json.dump(user_settings, file)
        self.debug_text("All Settings Saved")

    def add_text(self, text, type=TYPE_INPUT):  # add text to terminal
        if text[0] == "#":
            text = text.replace("\n", "")
            print("ext cmd:", text[1:])
            self.cmd.check(text[1:])
            return
        self.ui.terminalport.moveCursor(QTextCursor.End)
        def add(text_to_add:str): # add subfunction
            if self.ui.checkbox_timestamp.isChecked(): 
                text_to_add = add_timestamp(text_to_add)
            self.ui.terminalport.insertPlainText(text_to_add)  # add to terminal
            if self.ui.checkbox_autoscroll.isChecked():
                self.ui.terminalport.ensureCursorVisible()
        if type == TYPE_INPUT:
            self.ui.terminalport.setTextColor(colorBlack)
            add(text)
            loggingTools.addLine(text)
            if self.script_active:
                self.script_worker.incoming.emit(text)
            if self.ui.checkBox_graphData.isChecked():
                self.ui.widget_plot.parseBulkData(text)
            return
        elif type == TYPE_OUTPUT:
            text = self.output_char + text
            vprint(text, color=CBLUE)
            self.ui.terminalport.setTextColor(colorBlue)
            add(text)
            loggingTools.addLine(text)
            return
        elif type == TYPE_INFO:
            text = self.info_char + text + "\n"
            vprint(text, color=CGREEN)
            self.ui.terminalport.setTextColor(colorGreen)
            add(text)
            return
        elif type == TYPE_ERROR:
            text = self.error_char + text + "\n"
            vprint(text, color=CRED)
            self.ui.terminalport.setTextColor(colorRed)
            add(text)
            return
        elif type == TYPE_WARNING:
            text = self.warning_char + text + "\n"
            vprint(text, color=CYELLOW)
            self.ui.terminalport.setTextColor(colorYellow)
            add(text)
            return
        
    def clear_terminal(self):
        self.ui.terminalport.clear()
        self.debug_text()
        ts = get_timestamp()
        self.add_text(f"Terminal Cleared at {ts}", type=TYPE_INFO)

    def update_history(self, line=""):
        if line and line is not self.lastLine and self.script_active == False:
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
        result = self.parser.parse(text)
        if result != "" and result != "KEYWORD INVALID": 
            self.debug_text(result, type=TYPE_ERROR)
        if result != "KEYWORD INVALID":
            return
        #if self.parser.parse(text) == "":
        #    return
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
            vprint(f"Ports: {self.all_ports}", color = CGREEN)
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
         
    def connect(self, target="", intentional=True, auto=False, show=False):
        if show: 
            self.ui.combobox_port.setFocus()
            return
        vprint("Connecting to:", target, color=CGREEN)
        if intentional:
            vprint('self.current_port: ', str(self.current_port), CGREEN)
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
                if auto:
                    self.ui.checkbox_autoReconnect.setChecked(True)
            else:
                self.debug_text(
                    "ERROR: PORT COULD NOT CONNECT!", type=TYPE_ERROR)
        elif self.current_port != self.target_port:
            vprint("Changing Ports")
            self.disconnect()
            self.connect(target=self.target_port[3:])
        else:
            self.debug_text("WARNING: Already Connected!")
            self.disconnect()

    def disconnect(self, intentional=True):
        if self.is_connected:
            if intentional: 
                self.add_text(
                    f"Disconnecting From: {self.current_port}", TYPE_WARNING)
                self.debug_text(
                    f"Disconnecting from: {self.current_port}", TYPE_WARNING)
            else: 
                self.add_text(
                    f" LOST: {self.current_port}", TYPE_ERROR)
                self.debug_text(
                    f" LOST: {self.current_port}", TYPE_ERROR)
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

    def handle_log(self, open = False, archive = None, name = None): 
        if open != False: 
            if open == "":
                loggingTools.LogViewPopup(self)
                return
            loggingTools.LogViewPopup(self,filename=open)
            return
        if name:
            if len(name) > 1: 
                print("Naming Port:", name)
                loggingTools.setPort(name)
            else: 
                print("NAME MUST BE INCLUDED")
            return
        if archive != None: 
            print("archiving log!")
            loggingTools.archiveLog(name=archive)
            return
        else: 
            loggingTools.LogViewPopup(self, latest=True)
        
    def open_log(self, *args):
        print(args, type(args))
        if len(args) == 0: 
            loggingTools.LogViewPopup(self, latest=True)
            return
        if type(args) == list or type(args) == tuple:
            arg = args[0]
        if not arg:
            loggingTools.LogViewPopup(self, latest=True)
        elif arg in ['o']:
            loggingTools.LogViewPopup(self)
            return
        elif arg in ['a']:
            self.debug_text("Archiving Log:")
            loggingTools.archiveLog()
            return
        elif arg in ['h']:
            self.add_text(log_help, type=TYPE_INFO)
            return
        elif arg in ['n']:
            if args[1]: 
                print("Naming Port:", args[1])
                loggingTools.setPort(args[1])
        elif not (loggingTools.LogViewPopup(self, filename=arg)):
            self.debug_text(f"ERROR: Log {arg} not found!", type=TYPE_ERROR)

    def get_file(self, start="", location="", title="Open"):
        options = QFileDialog.Options()
        dprint('start: ', str(start))
        files = QFileDialog.getOpenFileName(self, "OPEN", start)
        dprint(' files[0]: ', str(files[0]))
        return files[0]

    def get_filename(self, dir):
        options = QFileDialog.Options()
        files = QFileDialog.getSaveFileName(self, caption="File", directory=dir, filter='*.txt', options=options)
        print("file name", files[0])
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

    def open_help(self, *args):
        if args: 
            with open('help.md', 'r') as file: 
                text = file.read()
                print(text)
                self.ui.terminalport.moveCursor(QTextCursor.End)
                self.ui.terminalport.setMarkdown(text)
            return
        self.help = HelpPopup()
        self.help.show()

    def handle_script(self, opens = None, save = None, run = False, tab = False, new = None, delete = None, list=None, help = None): 
        if help: 
            self.add_text(script_help, TYPE_INFO)
            return
        if list: 
            #cwd = os.getcwd()
            scripts = os.listdir(self.cwd + "/scripts/")
            for script in scripts: 
                self.add_text(script, TYPE_INFO)
            return
        if opens != None: 
            if opens == '': 
                script_path = self.get_file(self.script_dir)
            else:
                script_path = self.script_dir + opens + '.txt' 
            print(script_path)
            if os.path.exists(script_path): 
                print("exists")
                with open(script_path, 'r') as File:
                    text = File.read()
                    print(text)
                    self.ui.textEdit_script.setPlainText(text)
                self.debug_text(f"Loaded: {script_path}")
                if run: 
                    self.start_script()
            else: 
                self.debug_text(f"ERROR: script {script_path} not found", TYPE_ERROR)
                return 
        if save != None: 
            if save == '': 
                script_path = self.get_filename(self.script_dir)
            else:
                script_path = self.script_dir + save + '.txt' 
            print(script_path)
            if script_path: 
                with open(script_path, 'w') as File: 
                    File.write(self.ui.textEdit_script.toPlainText())
                self.debug_text(f"Script saved to: {script_path}")
            else:
                print("Save Script Cancelled")
            return
        if tab: 
            self.ui.tabWidget.setCurrentIndex(1)
            self.ui.textEdit_script.setFocus(True)
            
        if new != None: 
            self.ui.textEdit_script.clear()
            if new != "": 
                self.ui.textEdit_script.setPlainText(f"#name={new}\n#delay=100")
            self.ui.tabWidget.setCurrentIndex(1)
            self.ui.textEdit_script.setFocus(True)
            return
        if delete != None: 
            if delete != "":
                script_path = self.script_dir + delete + '.txt'
                if os.path.exists(script_path): 
                    os.remove(script_path)
                    self.debug_text(f"Removed {script_path}")
                else: 
                    self.debug_text(f"ERROR: File {script_path} not found", type=TYPE_ERROR)
            else: 
                self.debug_text(f"ERROR: file name must be included", type=TYPE_ERROR)
            return
                     

        if not opens and not save and not tab:
            self.start_script()
                
        return

    # def handle_script(self, *args):
    #     if not args:
    #         self.start_script()
    #         return
    #     script_open = False
    #     script_save = False
    #     script_delete = False
    #     script_exists = False
    #     script_name = ""
    #     script_path = None
    #     for arg in args:
    #         vprint("\narg ", arg, '\n')
    #         if arg in ['n', 'N', "new"]: # single arg
    #             self.ui.tabWidget.setCurrentIndex(1)
    #             self.ui.textEdit_script.clear()
    #             self.ui.textEdit_script.setFocus(True)
    #             return
    #         elif arg in ['t', 'T']: # single arg
    #             self.ui.tabWidget.setCurrentIndex(1)
    #             self.ui.textEdit_script.setFocus(True)
    #             return
    #         elif arg in ['h', 'H', 'help']: # single arg
    #             self.add_text(script_help, type=TYPE_INFO)
    #             return
    #         elif arg in ['o', 'O', 'open']:
    #             script_open = True
    #             script_save = False
    #             vprint("opening Script\n")
    #         elif arg in ['save', 's', 'S']:
    #             script_save = True
    #             script_open = False
    #             vprint("saving script\n")
    #         elif arg == 'd': 
    #             script_delete = True
    #             vprint("deleting script\n")
    #         elif arg: 
    #             script_name = arg

    #     if script_name:
    #         print("script_name:",script_name)
    #         script_path = script_path = self.script_dir + script_name + '.txt'
    #         print('script_path: ' , str(script_path), type(script_path))
    #         script_exists = os.path.exists(script_path)
        
    #     if script_save: 
    #         if script_path == None: # popup no script name arg
    #             script_path = self.get_filename(self.script_dir)
    #         if script_path: 
    #             with open(script_path, 'w') as File: 
    #                 File.write(self.ui.textEdit_script.toPlainText())
    #             self.debug_text(f"Script saved to: {script_path}")
    #         else: 
    #             dprint("Script Save Cancelled\n", color=CRED)
    #             return
        
    #     elif script_open:
    #         if script_path == None: 
    #             script_path = self.get_file(self.script_dir)
    #             if not script_path:
    #                 return
    #         elif script_exists == False:
    #             self.debug_text(f"ERROR: Script {script_path} not found", TYPE_ERROR)
    #             return
    #         self.debug_text(f"Loaded: {script_path}")
    #         with open(script_path, 'r') as File:
    #             text = File.read()
    #             print(text)
    #             self.ui.textEdit_script.setPlainText(text)
    #         #if script_run: 
    #             self.start_script()
    #         return
        
        # elif script_delete: 
        #     if script_exists: 
        #         os.remove(script_path)
        #         self.debug_text(f"Removed {script_path}")
        #     else: 
        #         self.debug_text(f"ERROR: File {script_path} not found", type=TYPE_ERROR)
        #     return

        # elif script_exists:
        #     with open(script_path, 'r') as File:
        #         text = File.read()
        #         print(text)
        #         self.ui.textEdit_script.setPlainText(text)
        #     self.start_script()
        #     return
        
        # else: 
        #     self.debug_text(f"ERROR: script {script_path} not found", TYPE_ERROR)
 
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
            self.script_worker.saveName.connect(self.handle_script)
            self.script_worker.finished.connect(self.end_script)
            self.script_thread.start()
        else:
            self.debug_text("ERROR: Script already active", type=TYPE_ERROR)

    def script_line(self, line:str):
        line.replace("\n", "")
        self.ui.lineEdit_input.setText(line)
        self.send_clicked()
        self.ui.lineEdit_input.setText(line)
        self.ui.lineEdit_input.setDisabled(True)

    def script_wait(self): 
        pass

    def end_script(self):
        vprint("Ending Script")
        self.script_active = False
        self.script_worker.stop()
        self.script_thread.exit()
        self.debug_text("Script Ended")
        self.ui.lineEdit_input.setText("")
        self.ui.lineEdit_input.setDisabled(False)
        self.ui.button_send.setDisabled(False)
        self.ui.lineEdit_input.setFocus()
        self.scriptActive = False

    def update_delay(self, delay=100):
        if self.script_active:
            self.ui.lineEdit_delay.setText(str(delay))


# ***********************************************************************************************************
updateCommands = [
    "pyuic5 -o gui/GUI_MAIN.py ui_files/mainWindow.ui",
    "pyuic5 -o gui/GUI_LOG.py ui_files/logViewer.ui",
    "pyuic5 -o gui/GUI_HELP.py ui_files/helpPopup.ui"
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


# def execute():
#     print("STARTING SERIAL KILLER")
#     app = QtWidgets.QApplication([sys.argv])
#     dprint("Argument List:", str(sys.argv))
#     for sysarg in sys.argv[1:]:
#         for argument in argList:
#             if sysarg in argument['arg']:
#                 funct = argument['funct']
#                 funct()

#     main = MainWindow()
#     main.show()
#     status = app.exec_()
#     sys.exit(status)


if __name__ == "__main__":
    import main
    main.execute()
    #execute()
