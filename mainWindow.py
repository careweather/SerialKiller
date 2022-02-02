# run this to update from GUI> pyuic5 -o GUI_MAIN.py ui_files/SK2_MainWindow.ui ; pyuic5 -o GUI_LOG.py ui_files/logViewer.ui
from logging import log
import subprocess
import json
import time 
from datetime import datetime
import os
from main import vprint, dprint, install_directory
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem
import loggingTools
from scripting import ScriptWorker
from parser_f import Parser, Command
from gui.GUI_MAIN import Ui_MainWindow  # Local
from gui.GUI_HELP import Ui_Help
from PyQt5.QtCore import QObject, QThread, flush, pyqtSignal
from PyQt5.QtGui import QIntValidator, QTextCursor,QSyntaxHighlighter, QFont
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
colorDarkGrey = QtGui.QColor(79, 79, 79)
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

CBLACK  = '\33[30m'
CRED    = '\33[31m'
CGREEN  = '\33[32m'
CYELLOW = '\33[33m'
CBLUE   = '\33[34m'
CCYAN   = '\033[96m' 
CVIOLET = '\33[35m'
CBEIGE  = '\33[36m'
CWHITE  = '\33[37m'

BOLD = '\033[1m'
UNDERLINE = '\033[4m'

script_help = '''
**** SCRIPT HELP ****
Press ESCAPE or CTRL+C to stop a script mid-execution

ARGUMENTS:
(none)\t run script in the script tab
-o [name]\t open a script. Optional: open "name".txt
-r \t run the script you are opening
-s [name] \t save current script. Optional: as "name".txt
-d [name] \t delete a script. Optional: delete "name".txt if it exists. 
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
-n [name]\tset the connection name to 'name'
-a [name]\tarchive the current log. Optional: archive as 'name'
-h\tdisplay this help message'''

plot_help = '''PLOT HELP
-kv\tstart the plotter in keyword-value mode
-a\tstart the plotter in array mode
-t [targets,]\tset the graph target values
-l [length]\tset a max length of 'length'
-p\tpause the plot
-r\tresume plotting
-c\tclear the plotter (and stop the plot)
-h\tdisplay this help message'''

terminal_placeholder = '''***Serial from device will appear here***

Type "help" for detailed use instructions'''


def get_timestamp(): 
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
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
                    vprint(str(ports) + "\n", color=CGREEN)
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
        self.plotter_active = False
        self.all_ports = []
        self.cwd = install_directory
        self.log_dir = "/logs/"
        self.script_dir = self.cwd + "/scripts/"
        self.current_port = ''  # Port Currently Active
        self.historyIndex = 0
        self.currentIndex = 0
        self.user_font = "Courier"
        self.lastLine = ""
        self.history = []
        self.keyCmds = {}
        self.keyboard_enabled = False
        self.connect_ui()
        self.config_commands()
        self.load_settings()
        self.ui.terminalport.setFont(QFont(self.user_font, 10))
        self.input_char = self.ui.lineEdit_receivedText.text()
        self.info_char = self.ui.lineEdit_infoText.text()
        self.warning_char = self.ui.lineEdit_warningText.text()
        self.error_char = self.ui.lineEdit_errorText.text()
        self.output_char = self.ui.lineEdit_sentText.text()
        self.update_ports()
        self.command_char = self.ui.lineEdit_commandChar.text()
        self.use_newline = self.ui.checkBox_newline.isChecked()
        self.use_return = self.ui.checkBox_return.isChecked()
        self.auto_rescan_toggled()

    def connect_ui(self): 
        self.setWindowIcon(QtGui.QIcon('img/SK_Icon.png'))
        self.ui.terminalport.setPlaceholderText(terminal_placeholder)
        self.ui.button_clear.clicked.connect(self.clear_terminal)
        self.ui.button_send.clicked.connect(self.send_clicked)
        self.ui.button_rescan.clicked.connect(self.update_ports)
        self.ui.checkBox_autoRescan.clicked.connect(self.auto_rescan_toggled)
        self.ui.checkbox_autoReconnect.stateChanged.connect(self.auto_reconnect_toggled)
        self.ui.button_runScript.clicked.connect(self.start_script)
        self.ui.button_saveSettings.clicked.connect(self.save_settings)
        self.ui.button_loadScript.clicked.connect(lambda: self.handle_script(opens=""))
        self.ui.button_saveScript.clicked.connect(lambda: self.handle_script(save=""))
        self.ui.button_connect.clicked.connect(self.connect)
        self.ui.button_viewLogs.clicked.connect(lambda: self.handle_log(open = ""))
        self.ui.button_viewLatest.clicked.connect(self.handle_log)
        self.ui.button_startGraph.clicked.connect(self.start_plot_clicked)
        self.ui.button_clearKeyboard.clicked.connect(self.clearTable)
        self.ui.label_keyboardControl.hide()
        self.ui.lineEdit_keyboard.hide()
        self.ui.lineEdit_keyboard.textEdited.connect(self.keyboardControl)
        self.ui.button_keyboard_control.clicked.connect(self.keyboard_control_clicked)
        self.ui.tableWidget_controls.itemSelectionChanged.connect(self.tableEdited)
        self.ui.tableWidget_controls.setRowCount(1)
        self.ui.tableWidget_controls.setColumnWidth(0,50)
        self.ui.button_browse.clicked.connect(self.set_log_path)
        self.ui.fontComboBox.currentFontChanged.connect(lambda: self.save_setting("font", self.ui.fontComboBox.currentFont().family()))
        
        for rate in baudRates:
            self.ui.combobox_baud.addItem(str(rate))
        self.ui.combobox_baud.setCurrentIndex(8)  # 115200
        self.ui.tabWidget.setCurrentIndex(0) # set focus to terminal
        self.ui.lineEdit_input.setFocus()
        #self.ui.checkbox_timestamp.setEnabled(True)
        self.ui.checkbox_timestamp.setCheckable(True) # disable for now

    def config_commands(self): 
        self.parser = Parser()
        cmd_connect = Command('com', self.connect, default_kw='target')
        cmd_connect.add_argument('baud', 'baud', str)
        cmd_connect.add_argument('parity', 'parity', str, default="NONE")
        cmd_connect.add_argument("xonxoff", 'xonxoff', bool, True)
        cmd_connect.add_argument("rtscts", 'rtscts', bool, True)
        cmd_connect.add_argument("dsrdtr", 'dsrdtr', bool, True)
        cmd_connect.add_argument('?', 'show', bool, True)
        cmd_connect.add_argument('auto', 'auto', bool, True)
        self.parser.add_command(cmd_connect)
        self.parser.add_command(Command("quit", quit))
        self.parser.add_command(Command("keystart", lambda: self.keyboard_control_clicked(force = 1)))
        self.parser.add_command(Command("keyclear", self.clearTable))
        self.parser.add_command(Command("clear", self.clear_terminal))
        self.parser.add_command(Command("help", self.open_help))
        self.parser.add_command(Command("scan", self.update_ports))
        self.parser.add_command(Command("dcon", self.disconnect))
        self.parser.add_command(Command("new", self.new_window))
        self.parser.add_command(Command("save", self.save_settings))
        self.parser.add_command(Command("auto", self.ui.checkbox_autoReconnect.toggle))
        cmd_connect_numb = Command("con", self.connect, default_kw='target')
        self.parser.add_command(cmd_connect_numb)
        self.parser.add_command(Command("con", self.connect))
        cmd_log = Command("log", self.handle_log)
        cmd_log.add_argument('n', 'name', str)
        cmd_log.add_argument('o', 'open', str, default="")
        cmd_log.add_argument('a', 'archive', str, default="")
        cmd_log.add_argument('h', "help", bool, True)
        cmd_baud = Command("baud", self.update_baud, 'target_rate', str, default_required=True)
        cmd_script = Command("script", self.handle_script)
        cmd_script.add_argument("o", 'opens', str, default="")
        cmd_script.add_argument("r", 'run', bool, default=True)
        cmd_script.add_argument("s", 'save', str, default="")
        cmd_script.add_argument("t", 'tab', bool, default=True)
        cmd_script.add_argument("n", 'new', str, default="")
        cmd_script.add_argument("d", 'delete', str, default = "")
        cmd_script.add_argument("h", 'help', bool, True)
        cmd_script.add_argument("ls", "list", bool, True)
        cmd_save = Command('saves', self.save_setting)
        cmd_save.add_argument("n", 'keyword', str)
        cmd_save.add_argument("v", 'value', str)
        self.parser.add_command(cmd_save)
        self.parser.add_command(cmd_script)
        self.parser.add_command(cmd_baud)
        self.parser.add_command(cmd_log)
        
        cmd_plot = Command("plot", self.handle_plot)
        cmd_plot.add_argument('l', 'len', int)
        cmd_plot.add_argument("kv", 'kv', bool, default=True)
        cmd_plot.add_argument("a", 'array', bool, default=True)
        cmd_plot.add_argument("e", 'end', bool, True)
        cmd_plot.add_argument("c", 'clear', bool, True)
        cmd_plot.add_argument("h", 'help', bool, True)
        cmd_plot.add_argument("r", 'resume', bool, True)
        cmd_plot.add_argument("p", 'pause', bool, True)
        cmd_plot.add_argument("t", 'targets', str)
        self.parser.add_command(cmd_plot)

        cmd_table_add = Command("key", self.addTableItem, default_kw='key', default_required=True)
        cmd_table_add.add_argument("s", "send", type=str, required=True)
        self.parser.add_command(cmd_table_add)

        cmd_key_clear = Command("keyclear", self.clearTable)
        self.parser.add_command(cmd_key_clear)

        self.parser.add_command(Command("keyctrl", self.keyboard_control_clicked))

        

    def keyPressEvent(self, keypress: QtGui.QKeyEvent) -> None:
        key = keypress.key()
        if self.ui.tableWidget_controls.hasFocus():
            print("table focus:", key)
        modifiers = int(keypress.modifiers())
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
            if current_tab < 4: 
                self.ui.tabWidget.setCurrentIndex(current_tab+1)
                return
        elif self.ui.combobox_port.hasFocus():
            if key == KEY_ENTER: 
                self.connect(target = self.ui.combobox_port.currentText())
                self.ui.lineEdit_input.setFocus()
                return
        elif key == KEY_S and modifiers == MOD_CTRL: 
            self.save_settings()
        return super().keyPressEvent(keypress)

    def tableEdited(self): 
        if self.ui.tableWidget_controls.currentRow() == self.ui.tableWidget_controls.rowCount()-1:
            self.ui.tableWidget_controls.setRowCount(self.ui.tableWidget_controls.rowCount()+1)
        self.keyCmds = self.getKeyCmds()

    def clearTable(self): 
        self.ui.tableWidget_controls.setRowCount(0)
        self.ui.tableWidget_controls.setRowCount(1)

    def addTableItem(self, key, send): 
        dprint("key:", key, "send", send, "\n")
        indx = self.ui.tableWidget_controls.rowCount() - 1 
        self.ui.tableWidget_controls.setRowCount(indx + 2)
        self.ui.tableWidget_controls.setItem(indx, 0, QTableWidgetItem(str(key)))
        self.ui.tableWidget_controls.setItem(indx, 1, QTableWidgetItem(str(send)))
      
    def keyboard_control_clicked(self, force = 0): 
        dprint("keyboard_en", self.keyboard_enabled)
        if force: 
            dprint("KEYBOARD FORCE")
            self.keyboard_enabled = False
        if self.keyboard_enabled == False: 
            self.keyboard_enabled = True
            self.ui.button_keyboard_control.setText("Enabled")
            self.ui.button_keyboard_control.setStyleSheet(f"background-color:{_colorGreen}")
            self.ui.label_keyboardControl.show()
            self.ui.lineEdit_keyboard.show()
            self.ui.lineEdit_keyboard.setFocus()
        elif self.keyboard_enabled == True: 
            self.keyboard_enabled = False
            self.ui.button_keyboard_control.setText("Disabled")
            self.ui.button_keyboard_control.setStyleSheet(f"background-color:{_colorYellow}")
            self.ui.lineEdit_input.setFocus()
            self.ui.label_keyboardControl.hide()
            self.ui.lineEdit_keyboard.hide()

    def getKeyCmds(self):
        keyCmds = {}
        for row in range(self.ui.tableWidget_controls.rowCount()):
            if self.ui.tableWidget_controls.item(row,0) is not None: 
                if self.ui.tableWidget_controls.item(row,1) is not None: 
                    keyCmds[self.ui.tableWidget_controls.item(row,0).text()] = self.ui.tableWidget_controls.item(row,1).text()
        #print(keyCmds)
        return keyCmds

    def keyboardControl(self):
        key = self.ui.lineEdit_keyboard.text()
        cmds = self.getKeyCmds()
        self.ui.lineEdit_keyboard.clear()
        if key in cmds: 
            cmd = cmds[key]
            if cmd: 
                print("key:", key, "cmd:", cmds[key])
                self.ui.lineEdit_input.setText(cmds[key])
                self.send_clicked()
            
    def load_settings(self): # import and apply settings from json
        try:
            with open("user_settings.json", "r") as file:
                user_settings = json.load(file)
                self.ui.lineEdit_commandChar.setText(user_settings['commandChar'])
                if os.path.exists(user_settings['logpath']): 
                    loggingTools.setLogPath(user_settings['logpath'])
                    new_log_path = user_settings['logpath']
                else: 
                    new_log_path = loggingTools.log_path
                self.ui.lineEdit_logPath.setText(new_log_path)
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
                self.ui.checkBox_return.setChecked(user_settings['use_return'])
                self.ui.checkBox_newline.setChecked(user_settings['use_newline'])
                self.user_font = user_settings['font']
                self.ui.fontComboBox.setCurrentText(self.user_font)
                if (user_settings["port"] in all_ports):
                    self.ui.combobox_port.setCurrentText(user_settings["port"])
                keys = user_settings['keys']
                for key in keys: 
                    self.addTableItem(key, keys[key])

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
        user_settings['use_newline'] = self.ui.checkBox_newline.isChecked()
        user_settings['use_return'] = self.ui.checkBox_return.isChecked()
        user_settings['keys'] = self.getKeyCmds()
        user_settings['font'] = self.ui.fontComboBox.currentFont().family()
        vprint("[SAVING SETTINGS]\n", user_settings, color=CGREEN)
        with open("user_settings.json", "w") as file:
            json.dump(user_settings, file)
        self.debug_text("All Settings Saved")

    def add_text(self, text:str, type=TYPE_INPUT):  # add text to terminal
        if text.startswith("#"):
            if type == TYPE_INPUT or type == TYPE_OUTPUT: 
                lines = text.splitlines()
                print("possible CMD: ", lines)
                for line in lines: 
                    if line.startswith("#"): 
                        self.parser.parse(line[1:])
                    return
        self.ui.terminalport.moveCursor(QTextCursor.End)
        def add(text_to_add:str): # add subfunction
            if self.ui.checkbox_timestamp.isChecked(): 
                text_to_add = add_timestamp(text_to_add)
            self.ui.terminalport.insertPlainText(text_to_add)  # add to terminal
            if self.ui.checkbox_autoscroll.isChecked():
                self.ui.terminalport.ensureCursorVisible()
        if type == TYPE_INPUT:
            self.ui.terminalport.setTextColor(colorWhite)
            add(text)
            loggingTools.addLine(text)
            if self.plotter_active: 
                self.ui.widget_plot.update(text)
            if self.script_active and len(text) > 2:
                self.script_worker.inp = text.strip()
            return
        elif type == TYPE_OUTPUT:
            if self.plotter_active: 
                self.ui.widget_plot.update(text)
            text = self.output_char + text
            vprint(text, color=CBLUE)
            self.ui.terminalport.setTextColor(colorLightBlue)
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
        if line and self.script_active == False:
            if line != self.lastLine:
                self.lastLine = line
                self.history.append(line)
                self.historyIndex += 1
            self.currentIndex = self.historyIndex

    def send_clicked(self):
        text = self.ui.lineEdit_input.text()
        self.ui.lineEdit_input.clear()

        self.update_history(text)
        if ("$UTS") in text:
            text = text.replace("$UTS", str(int(time.time())))
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
            self.add_text(result, type=TYPE_ERROR)
        if result != "KEYWORD INVALID":
            return
        if self.ui.checkBox_return.isChecked():
            text += '\r'
            #print("return")
        if self.ui.checkBox_newline.isChecked():
            text += '\n'
        #print(repr(text))
        if self.is_connected:
            SH.sendString(text)
        else:
            self.debug_text("WARNING: NOT CONNECTED", type=TYPE_ERROR)
        self.add_text(text, type=TYPE_OUTPUT)

    def new_window(self):
        import platform
        if platform.system() == 'Windows':
            subprocess.call(f'start pythonw.exe .\main.py', shell=True)
        elif platform.system() == 'Linux':
            subprocess.call(f'python3 {install_directory}/main.py', shell=True) 

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
            vprint(f"Ports: {self.all_ports}\n", color = CGREEN)
            self.debug_text(f"Found Ports: {self.all_ports}")
        self.ui.combobox_port.clear()
        for port in self.all_ports:
            self.ui.combobox_port.addItem(port)
        if self.target_port in self.all_ports:
            self.ui.combobox_port.setCurrentText(self.target_port)
            if self.reconnect_active and not self.is_connected: 
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
            self.active_baud = baud
        else: 
            self.debug_text(f"Baud Rate {baud} Invalid!")
         
    def connect(self, target:str="", baud = None, parity = None, xonxoff = None, dsrdtr = None, rtscts = None, intentional=True, auto=False, show=False):
        if parity == None:
            parity = self.ui.comboBox_parity.currentText() 
        if xonxoff == None: 
            xonxoff = self.ui.checkBox_xonxoff.isChecked()
        if dsrdtr == None: 
            dsrdtr = self.ui.checkBox_dsrdtr.isChecked()
        if rtscts == None:
            rtscts = self.ui.checkBox_rtscts.isChecked()
        if show: 
            self.ui.combobox_port.setFocus()
            return
        if baud: 
            self.update_baud(baud)
        self.ui.checkBox_rtscts.setChecked(rtscts)
        self.ui.checkBox_xonxoff.setChecked(xonxoff)
        self.ui.checkBox_dsrdtr.setChecked(dsrdtr)
        self.ui.comboBox_parity.setCurrentText(parity)
        vprint("Connecting to:", target, color=CGREEN)
        if intentional:
            vprint('self.current_port: ', str(self.current_port), CGREEN)
            if target:
                print(f"TARGET: ({target})")
                if target in self.all_ports: 
                    pass 
                elif target.isnumeric():
                    if "COM" + target in self.all_ports: 
                        target = "COM" + target
                    elif int(target) <= len(self.all_ports):
                        target = self.all_ports[int(target)]
                elif target == '?': 
                    self.ui.combobox_port.showPopup()
                    self.ui.combobox_port.setFocus()
                    return
                elif target[0] == "#" and target[1:].isnumeric(): 
                    target = self.all_ports[int(target[1:])]
                    print("TARGET NUMBER", target)
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
            if (SH.makeConnection(port=self.target_port, baud=self.active_baud, parity = parity, xonxoff=xonxoff, rtscts=rtscts, dsrdtr=dsrdtr)):
                self.is_connected = True
                self.current_port = self.target_port
                self.debug_text(f"Connected to {self.target_port}", TYPE_INFO)
                self.add_text(
                    f"Connected to {self.target_port} baud:{self.active_baud} parity:{parity}", TYPE_INFO)
                self.ui.combobox_port.setCurrentText(self.target_port)
                self.ui.terminalport.setEnabled(True)
                self.ui.terminalport.setStyleSheet(
                    f"background-color:{_colorBlack}")
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
        elif not auto:
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
                f"background-color: {_colorDarkGrey}")
            if intentional:
                self.ui.checkbox_autoReconnect.setChecked(False)
        else:
            self.debug_text("WARNING: Already Disconnected!", TYPE_WARNING)
            vprint("ERROR: NOT CONNECTED")

    def handle_log(self, open = False, archive = None, name = None, help=False):
        if help == True: 
            self.add_text(log_help, TYPE_INFO) 
            return
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

    def set_log_path(self): 
        log_path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
        print("New Log Path:", log_path)
        if log_path: 
            loggingTools.setLogPath(log_path)
            self.ui.lineEdit_logPath.setText(log_path)
            self.save_setting("logpath", log_path)
        else: 
            print("NO LOG PATH FOUND")
        return

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

    def open_help(self):
        self.help = HelpPopup()
        self.help.show()

    def handle_script(self, opens = None, save = None, run = False, tab = False, new = None, delete = None, list=None, help = None): 
        if help: 
            self.add_text(script_help, TYPE_INFO)
            return
        if list: 
            scripts = os.listdir(self.cwd + "/scripts/")
            for script in scripts: 
                self.add_text(script, TYPE_INFO)
            return
        if opens != None:
            if opens == '': 
                script_path = self.get_file(self.script_dir)
                if script_path == "": 
                    return
            else:
                script_path = self.script_dir + opens + '.txt' 
            print(script_path)
            if os.path.exists(script_path): 
                with open(script_path, 'r') as File:
                    text = File.read()
                    print(text)
                    self.ui.textEdit_script.setPlainText(text)
                self.debug_text(f"Loaded: scripts/{opens}.txt")
                if run: 
                    self.start_script()
                else: 
                    self.ui.tabWidget.setCurrentIndex(1)
                    self.ui.textEdit_script.setFocus(True)
                    return
            else: 
                self.debug_text(f"ERROR: scripts/{opens}.txt not found", TYPE_ERROR)
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
            self.script_worker.print_line.connect(self.script_print)
            self.script_worker.waiting.connect(self.script_wait)
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
    
    def script_print(self, line:str):
        print("script print:", line)
        self.add_text(line, TYPE_INFO)

    def script_wait(self, val): 
        #self.script_thread.wait(5000)
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

    def start_plot_clicked(self): 
        if self.plotter_active: 
            self.handle_plot(clear=True)
            return
        else: 
            size = self.ui.lineEdit_size.text()
            try: 
                size = int(size)
            except: 
                size = 100 
            targets = self.ui.lineEdit_keys.text()
            if self.ui.comboBox_type.currentText() == "Key-Value": 
                self.handle_plot(kv=True, targets=targets, len=size)
            if self.ui.comboBox_type.currentText() == "Array": 
                self.handle_plot(array=True, targets=targets, len=size)

    def handle_plot(self, help = False, kv = False, array = False, targets = None, end = False, len = 100, pause = False, clear = False, resume = False):
        if help:
            self.add_text(plot_help, TYPE_INFO)
            self.add_text("")
            return
        if len: 
            self.ui.lineEdit_size.setText(str(len))
        if kv or array: 
            self.ui.button_startGraph.setStyleSheet(f"background-color:{_colorGreen}")
            self.ui.lineEdit_size.setEnabled(False)
            self.ui.lineEdit_keys.setEnabled(False)
            self.ui.comboBox_type.setEnabled(False)
            self.ui.lineEdit_keys.setText(str(targets))
            self.ui.tabWidget.setCurrentIndex(3)
            self.ui.button_startGraph.setText("Stop Graph")
            self.plotter_active = True
        if kv: 
            self.debug_text(f"Started Plot in Key-Value mode")
            self.ui.comboBox_type.setCurrentText("Key-Value")
            self.ui.widget_plot.add_kv_graph(targets=targets, len=len)
            return
        if array: 
            self.ui.comboBox_type.setCurrentText("Array")
            self.ui.lineEdit_keys.setText(str(targets))
            self.ui.widget_plot.add_array_graph(targets=targets, len=len)
            return
        if clear: 
            self.ui.button_startGraph.setStyleSheet(f"")
            self.ui.button_startGraph.setText("Start Graph")
            self.ui.lineEdit_size.setEnabled(True)
            self.ui.lineEdit_keys.setEnabled(True)
            self.ui.comboBox_type.setEnabled(True)
            self.ui.comboBox_type.setCurrentText("None")
            self.ui.lineEdit_keys.setText("")
            self.plotter_active = False
            self.ui.widget_plot.clear_plot()
        if pause: 
            self.plotter_active = False
            self.ui.widget_plot.pause()
        if resume: 
            self.ui.widget_plot.resume()

    def start_plot(self, size = 200): 
        self.ui.tabWidget.setCurrentIndex(2)
        if self.plotter_active == False: 
            self.ui.widget_plot.clear()
            self.plotter_active = True
            self.ui.lineEdit_size.setText(str(size))
            self.ui.widget_plot.addLineGraph(size)
            return
        else: 
            vprint("PLOT ALREADY STARTED")
        
    def end_plot(self): 
        self.plotter_active = False

vprint.enabled = False
dprint.enabled = False
# ***********************************************************************************************************

if __name__ == "__main__":
    import main
    main.execute()

