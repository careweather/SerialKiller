import glob
import json
import os
import time
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QGroupBox,
                             QLabel, QLineEdit, QPushButton, QTableWidgetItem,
                             QWidget)

# gui imports
from gui.GUI_MAIN_WINDOW import Ui_MainWindow
from serial_handler import *
from sk_commands import Command
from sk_help import *
from sk_help_popup import Help_Popup, open_help_popup
from sk_log_popup import Log_Viewer, open_log_viewer
from sk_logging import SK_Logger
from sk_scripting import ScriptSyntaxHighlighter, ScriptWorker
from sk_tools import *
from collections import OrderedDict
import re
import random
import math
import csv 
import shutil

def print_keyPress(event:QtGui.QKeyEvent):
    modifiers = {
        QtCore.Qt.NoModifier: "NONE", 
        QtCore.Qt.ShiftModifier : "SHIFT", 
        QtCore.Qt.ControlModifier : "CTRL", 
        QtCore.Qt.AltModifier: "ALT", 
        QtCore.Qt.MetaModifier: "META", 
        QtCore.Qt.KeypadModifier: "KEYPAD", 
        QtCore.Qt.GroupSwitchModifier: "GROUP", 
        QtCore.Qt.KeyboardModifierMask : "MASK", 
    }

    print(f"Key: {event.key().real} {event.key().imag} {event.key().as_integer_ratio()} Mod: {modifiers[event.modifiers()]}")

class KeyControlLineEdit(QtWidgets.QLineEdit):
    keyPress = pyqtSignal(str)
    def __init__(self, *args):
        QLineEdit.__init__(self, *args)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        
        text = event.text() 
        self.setText("")
        print(key, text)
        if key == QtCore.Qt.Key_Right:
            self.keyPress.emit("RIGHT")
            print("RIGHT")
        elif key == QtCore.Qt.Key_Left:
            self.keyPress.emit("LEFT")
            print("LEFT")
        elif key == QtCore.Qt.Key_Up:
            self.keyPress.emit("UP")
            print("UP")
        elif key == QtCore.Qt.Key_Down:
            self.keyPress.emit("DOWN")
            print("DOWN")
        elif text:
            self.keyPress.emit(text)
        return 
    

class CaptureLineEdit(QtWidgets.QLineEdit):
    keyPress = pyqtSignal(str)
    def __init__(self, *args):
        QLineEdit.__init__(self, *args)

    def focusNextPrevChild(self, next: bool) -> bool:
        return False
        return super().focusNextPrevChild(next)
    
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        self.setText("")
        text = event.text() 
        #print(key, text)
        if key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            self.keyPress.emit('\n')
            return 
        if text:
            self.keyPress.emit(text)
        return 
        try: 
            c = ord(text)
            if c == 13:
                c = ord('\n')
            print(c)
            self.keyPress.emit(c)
        except Exception as E:
            print(E)
        return 
        print("ORD: ", ord(text))
        if text.isprintable():
            self.keyPress.emit(event.text())
        else:
            print("TEXT NOT PRINTABLE: ", text)
        return 
        if key == QtCore.Qt.Key_Tab:
            self.keyPress.emit("\t")
            event.accept()
        elif key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            self.keyPress.emit("\n")
        elif key.real < 0x110000:
            self.keyPress.emit(event.text())




class MainWindow(QtWidgets.QMainWindow):
    auto_reconnect_to = None 
    target_port: str = None  # Port to auto-connect to.
    current_ports: dict = {}  # List of current ports
    command_char: str = None
    script_worker = None
    cmd_history = [""]
    commands = {}
    history_index = 1
    key_cmds: dict = {}
    script_thread = QThread()
    plot_started = False
    is_connected = False
    data_format = 'utf-8'
    needs_timestamp = True
    timestamp_format: str = '[%I:%M:%S.%f] '
    open_time = datetime.now()
    preference_port: str = None

    def __init__(self, parent: QtWidgets.QApplication, open_cmd=[], * args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.last_save_time = time.perf_counter()
        self.cmd_list = []
        self.current_settings = {}
        self.ui = Ui_MainWindow()

        self.app: QtWidgets.QApplication = parent

        self.ui.setupUi(self)
        self.ui.lineEdit_keyboard_control = KeyControlLineEdit(self.ui.lineEdit_keyboard_control)
        self.ui.lineEdit_keyboard_control.setPlaceholderText("Type Here")
        self.connect_ui()
        self.debug_text("No Ports Found", color=COLOR_RED)
        self.ui.lineEdit_pass = CaptureLineEdit(self.ui.lineEdit_pass)
        self.ui.lineEdit_pass.setPlaceholderText("pass")
        self.ui.lineEdit_pass.setMaximumSize(50, 1000)


        self.save_timer = QTimer()

        self.create_settings()
        self.create_commands()
        self.update_ports()
        self.start_rescan()
        self.recall_settings()
        self.script_highlighter = ScriptSyntaxHighlighter(self.ui.textEdit_script)
        self.start_logger()

        self.ui.lineEdit_input.setFocus()

        self.ui.tabWidget.setCurrentIndex(0)
        self.update_ports(get_ports())

        if open_cmd:
            for cmd in open_cmd:
                vprint("Open Command:", cmd)
                self.ui.lineEdit_input.setText(cmd)
                self.send_clicked()

        self.ui.pushButton_restart_logger.setEnabled(False)
        self.ui.lineEdit_pass.keyPress.connect(self.passTextEntered)

        self.update_status_bar()

    def update_status_bar(self, text: str = None):
        if text is not None:
            self.ui.statusbar.showMessage(text)
            return 
        text = "Port: " 
        if self.is_connected:
            text += f" {ser.port}"
        else:
            text += "None"

        text += f" Auto: {self.auto_reconnect_to}"
        self.ui.statusbar.showMessage(text)
        
        





    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        modifier = event.modifiers()

        #vprint(f"Key: {key} Mod: {modifier}")
        if self.ui.lineEdit_input.hasFocus():
            if key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
                self.send_clicked()
                return
            elif key == QtCore.Qt.Key_Up:
                self.scroll_history(scroll_down=False)
            elif key == QtCore.Qt.Key_Down:
                self.scroll_history(scroll_down=True)

        elif self.ui.comboBox_port.hasFocus():
            if key == QtCore.Qt.Key_Return:
                self.connect(port=self.ui.comboBox_port.currentText())
                self.ui.lineEdit_input.setFocus()

        if key == QtCore.Qt.Key_Escape:
            if self.ui.lineEdit_input.hasFocus() == False:
                self.ui.lineEdit_input.setFocus()
            if self.script_thread:
                self.end_script()

        if modifier == QtCore.Qt.ControlModifier:  # CTRL + ...

            if key == QtCore.Qt.Key_Period:  # CTRL + >
                current_tab = self.ui.tabWidget.currentIndex()
                if current_tab < self.ui.tabWidget.count():
                    self.ui.tabWidget.setCurrentIndex(current_tab+1)
            if key == QtCore.Qt.Key_Comma:  # CTRL + <
                current_tab = self.ui.tabWidget.currentIndex()
                if current_tab > 0:
                    self.ui.tabWidget.setCurrentIndex(current_tab-1)

            if key == QtCore.Qt.Key_P:
                self.show_ports()

            if key == QtCore.Qt.Key_N:
                self.clear_clicked()

            if key == QtCore.Qt.Key_S:
                self.start_script()

        elif modifier == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            if key == QtCore.Qt.Key_C:
                self.connect_clicked()

        return super().keyPressEvent(event)


########################################################################
#
#               UI FUNCTIONS
#
########################################################################

    def hide_groupbox(self, groupbox: QtWidgets.QGroupBox):
        #print("box is", groupbox.isChecked())
        box_title: str = groupbox.title()

        if groupbox.isChecked():
            groupbox.setTitle(box_title.replace(TRIANGLE_RIGHT, TRIANGLE_DOWN))
        else:
            groupbox.setTitle(box_title.replace(TRIANGLE_DOWN, TRIANGLE_RIGHT))

        for child in groupbox.children():
            if getattr(child, "show", None):
                if groupbox.isChecked():
                    child.show()
                else:
                    child.hide()

    def connect_ui(self):
        self.ui.action_save_script.triggered.connect(self.save_script)
        self.ui.action_save_as_script.triggered.connect(lambda: self.save_script(None, True))
        self.ui.action_open_script.triggered.connect(self.open_script)
        self.ui.action_run_script.triggered.connect(self.start_script)
        self.ui.action_open_latest_log.triggered.connect(self.open_log)
        self.ui.action_open_log.triggered.connect(lambda: self.handle_log_command(**{'-o': None}))
        self.ui.action_help.triggered.connect(self.print_help)
        self.ui.action_github_repo.triggered.connect(self.open_github_repo)

        self.ui.lineEdit_log_folder.textChanged.connect(self.log_settings_changed)
        self.ui.lineEdit_log_name.textChanged.connect(self.log_settings_changed)
        self.ui.lineEdit_time_format.textChanged.connect(self.log_settings_changed)
        self.ui.lineEdit_log_format.textChanged.connect(self.log_settings_changed)
        self.ui.pushButton_log_path_select.clicked.connect(self.set_log_folder)
        self.ui.pushButton_restart_logger.clicked.connect(self.start_logger)

        self.ui.label_log_settings_debug.setText("")

        self.ui.textEdit_terminal.setPlaceholderText(HELP_TEXT)
        self.ui.textEdit_terminal.setStyleSheet(STYLE_SHEET_TERMINAL_INACTIVE)
        self.ui.pushButton_connect.setStyleSheet(STYLE_SHEET_BUTTON_INACTIVE)
        self.ui.pushButton_send.clicked.connect(self.send_clicked)
        self.ui.pushButton_clear.clicked.connect(self.clear_clicked)
        self.ui.pushButton_connect.clicked.connect(self.connect_clicked)
        self.ui.pushButton_pause_plot.clicked.connect(self.pause_plot)

        self.set_combobox_items(self.ui.comboBox_baud, baud_rates)
        self.ui.textEdit_script.setPlaceholderText(SCRIPT_SYNTAX_HELP)
        self.ui.textEdit_script.setStyleSheet(STYLE_SHEET_SCRIPT)
        self.ui.checkBox_auto_reconnect.toggled.connect(self.auto_reconnect_toggled)
        self.ui.pushButton_clear_table.clicked.connect(self.clear_key_cmds)
        self.ui.tableWidget_keys.setRowCount(1)
        self.ui.tableWidget_keys.cellChanged.connect(self.key_cmds_edited)
        #self.ui.lineEdit_keyboard_control.textChanged.connect(self.keyboard_control)
        self.ui.lineEdit_keyboard_control.keyPress.connect(self.keyboard_control)
        #self.ui.lineEdit_keyboard_control.installEventFilter()
        self.ui.pushButton_run_script.clicked.connect(self.start_script)
        self.ui.pushButton_start_plot.clicked.connect(self.start_plot_clicked)
        self.ui.pushButton_start_plot.setStyleSheet(STYLE_SHEET_BUTTON_INACTIVE)

        #self.ui.groupBox_port.toggled.connect(lambda: self.hide_groupbox(self.ui.groupBox_port))

        self.ui.groupBox_port.clicked.connect(lambda: self.hide_groupbox(self.ui.groupBox_port))
        self.ui.groupBox_plot_settings.clicked.connect(lambda: self.hide_groupbox(self.ui.groupBox_plot_settings))
        self.ui.textEdit_script.setAcceptRichText(False)
        self.ui.lineEdit_timestamp_format.textChanged.connect(self.change_timestamp_format)

        self.ui.pushButton_export_csv.clicked.connect(self.export_csv)

        self.change_timestamp_format()
        #self.ui.groupBox_adv_plot.toggled.connect(lambda: self.collapse_box(self.ui.groupBox_adv_plot))
        #self.collapse_box(self.ui.groupBox_adv_plot, True)

    def keyboard_control_keypress(self, event: QtGui.QKeyEvent):
        key = event.key()
        print(key)
        if key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            self.send_clicked()

    def scroll_history(self, scroll_down=True):
        if scroll_down:
            if len(self.cmd_history) > 0:
                self.history_index -= 1
                if self.history_index < 0:
                    self.history_index = 0
            else:
                return
        else:
            self.history_index += 1
            if (self.history_index >= len(self.cmd_history)):
                self.history_index = len(self.cmd_history)
                self.ui.lineEdit_input.clear()
                return

        self.ui.lineEdit_input.setText(self.cmd_history[self.history_index])

    def append_to_history(self, line: str):
        line = line.replace("\n", "").replace("\r", "")
        if not line:
            return
        self.history_index = 0
        if len(self.cmd_history) > 1 and line == self.cmd_history[1]:
            return
        self.cmd_history.insert(1, line)
        self.history_index = 0

    def add_text(self, *args, type: int = TYPE_RX):
        text: str = ""
        for arg in args:
            text += str(arg)

        self.ui.textEdit_terminal.moveCursor(QTextCursor.End)

        if type == TYPE_RX:  # Incoming FROM device

            if self.ui.checkBox_autolog.isChecked():
                self.log.write(text)
            if self.plot_started:
                self.ui.widget_plot.update(text)
            text = text.replace("\r", '')
            if self.ui.checkBox_timestamp.isChecked():
                if self.needs_timestamp:
                    text = self.get_time_string() + text
                if text.endswith("\n"):
                    self.needs_timestamp = True
                    text = text.replace("\n", '\n' + self.get_time_string(), text.count('\n')-1)
                else:
                    text = text.replace("\n", '\n' + self.get_time_string())
                    self.needs_timestamp = False
            self.ui.textEdit_terminal.setTextColor(COLOR_WHITE)
            self.ui.textEdit_terminal.insertPlainText(text)
            vprint(text, color="white", end="", flush=True)

        elif type == TYPE_TX:  # Outgoing TO DEVICE
            text = self.ui.lineEdit_tx_chr.text() + text

            if self.ui.checkBox_output_include_log.isChecked() and self.ui.checkBox_autolog.isChecked():
                self.log.write(text)
            if self.ui.checkBox_timestamp.isChecked():
                text = self.get_time_string() + text
            if self.ui.checkBox_output_include_terminal.isChecked():
                self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_BLUE)
                self.ui.textEdit_terminal.insertPlainText(text)
            vprint(text, color="blue", end="", flush=True)

        elif type == TYPE_INFO:
            if self.ui.checkBox_info_include_terminal.isChecked():
                text = self.ui.lineEdit_info_chr.text() + text
                self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_GREEN)
                self.ui.textEdit_terminal.insertPlainText(text)
            if self.ui.checkBox_info_include_log.isChecked() and self.ui.checkBox_autolog.isChecked():
                self.log.write(text)
            vprint(text, color="green", end="", flush=True)

        elif type == TYPE_ERROR:
            if self.ui.checkBox_error_include_terminal.isChecked():
                text = self.ui.lineEdit_err_chr.text() + text
                self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_RED)
                self.ui.textEdit_terminal.insertPlainText(text)
            if self.ui.checkBox_error_include_log.isChecked() and self.ui.checkBox_autolog.isChecked():
                self.log.write(text)
            vprint(text, color="red", end="", flush=True)

        elif type == TYPE_HELP:
            self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_YELLOW)
            self.ui.textEdit_terminal.insertPlainText(text)
            vprint(text, color="yellow", end="", flush=True)

        if self.ui.checkBox_autoscroll.isChecked():
            self.ui.textEdit_terminal.ensureCursorVisible()

    def debug_text(self, *args, color: QColor = COLOR_BLACK):
        label_text = ""
        for arg in args:
            label_text += str(arg)
        DEBUG_TEXT_LEN = 60
        if len(label_text) > DEBUG_TEXT_LEN: 
            label_text = label_text[0:DEBUG_TEXT_LEN] + "..."
            # lines = []
            # for i in range(0, len(label_text), DEBUG_TEXT_LEN):
            #     lines.append(label_text[i:i+DEBUG_TEXT_LEN])
            # label_text = '\n'.join(lines)

        self.ui.label_debug.setStyleSheet(f"color:{colorToStyleSheet(color)}")
        self.ui.label_debug.setText(label_text)
        #self.ui.label_debug.setWordWrap(True)
        vprint(label_text, color='cyan')

    def input_text_evaluate(self, text: str) -> str:
        text = text.replace("$UTS", str(int(time.time())))
        found_expressions = re.findall(r'\$\{(.*?)\}', text)
        for expression in found_expressions:
            try:
                if not expression:
                    text = text.replace("${}", "")
                    continue
                expression_resp = str(eval(expression))
                text = text.replace(f"${{{expression}}}", expression_resp, 1)
                vprint(f"EXPRESSION ${{{expression}}} = {expression_resp}", color="green")
            except Exception as E:
                eprint(E)
                self.add_text(f"ERR IN EXPR: ${{{expression}}} {str(E)}\n", type=TYPE_ERROR)
                return None
        return text

    def passTextEntered(self, val:str):
        #vprint("Pass: ", val)
        if self.is_connected:
            serial_send_string(val)
        else:
            self.add_text(val)

    def send_clicked(self, add_to_history=True):
        original_text = self.ui.lineEdit_input.text()
        if self.ui.lineEdit_input.isEnabled():
            self.ui.lineEdit_input.clear()
        if add_to_history:
            self.append_to_history(original_text)

        text = self.input_text_evaluate(original_text)
        if text == None:
            return

        text = text + replace_escapes(self.ui.lineEdit_append_to_send.text())
        if self.ui.checkBox_interpret_escape.isChecked():
            text = replace_escapes(text)
        # print(text)

        #text = original_text + replace_escapes(self.ui.lineEdit_append_to_send.text())
        cmd_result = self.interpret_command(text)
        if cmd_result != None:
            if cmd_result == "":
                return
            else:
                self.add_text(f"ERROR {cmd_result}\n", type=TYPE_ERROR)
            return
        self.add_text(text, type=TYPE_TX)
        if self.is_connected:
            serial_send_string(text)
        else:
            self.debug_text("WARN: NOT CONNECTED", color=COLOR_DARK_YELLOW)

    def clear_clicked(self):
        self.ui.textEdit_terminal.setText("")
        self.debug_text("")

########################################################################
#
#               SERIAL FUNCTIONS
#
########################################################################

    def serial_error(self):
        if self.is_connected:
            self.add_text(f"LOST {ser.port}\n", type=TYPE_ERROR)
            self.disconnect(intentional=False)
            vprint("SERIAL PORT LOST", color="red")

    def disconnect(self, intentional=True):
        if self.is_connected == False:
            if intentional:
                self.debug_text("ALREADY DISCONNECTED", color=COLOR_DARK_YELLOW)
            return

        if intentional:
            self.target_port = None
            self.auto_reconnect_to = None
            self.ui.label_port.setText(f"Ports: ({self.preference_port})")
            self.add_text(f"DISCONNECTED FROM: {ser.port}\n", type=TYPE_INFO)
            self.debug_text(f"DISCONNECTED FROM: {ser.port}")

        self.serial_worker.stop()
        self.serial_thread.exit()
        serial_disconnect()
        self.is_connected = False
        self.ui.textEdit_terminal.setStyleSheet(STYLE_SHEET_TERMINAL_INACTIVE)
        self.ui.pushButton_connect.setStyleSheet(STYLE_SHEET_BUTTON_INACTIVE)
        self.ui.pushButton_connect.setText("Connect")
        self.ui.comboBox_baud.setEnabled(True)
        self.ui.comboBox_parity.setEnabled(True)
        self.ui.checkBox_dsrdtr.setEnabled(True)
        self.ui.checkBox_rtscts.setEnabled(True)
        self.ui.checkBox_dsrdtr.setEnabled(True)
        self.ui.checkBox_xonxoff.setEnabled(True)
        self.log.set_port("NONE")
        self.update_status_bar()

    def connect(self, port: str, baud: str = "115200", xonxoff: bool = False, dsrdtr: bool = False, rtscts: str = False, parity: str = "NONE") -> bool:
        #self.ui.comboBox_port.setCurrentText(port)
        if port in self.current_ports:
            device = self.current_ports[port]["dev"]
            self.ui.comboBox_port.setCurrentText(port)

        self.is_connected = serial_connect(device, baud, xonxoff, rtscts, dsrdtr, parity)
        if not self.is_connected:
            self.debug_text(f"ERR: {port} COULD NOT CONNECT", color=COLOR_RED)
            self.add_text(f"ERR: {port} COULD NOT CONNECT \n", type=TYPE_ERROR)
            return

        self.log.set_port(port)

        self.debug_text(f"CONNECTED TO {port} at {ser.baudrate} BAUD", color=COLOR_GREEN)
        self.add_text(f"CONNECTED TO {port} at {ser.baudrate} BAUD\n", type=TYPE_INFO)

        self.preference_port = port
        if self.ui.checkBox_auto_reconnect.isChecked():
            self.target_port = port
            self.auto_reconnect_to = self.current_ports[port]['s/n']

            self.ui.label_port.setText(f"Port: Auto ({self.target_port})")

        self.ui.textEdit_terminal.setStyleSheet(STYLE_SHEET_TERMINAL_ACTIVE)
        self.ui.pushButton_connect.setStyleSheet(STYLE_SHEET_BUTTON_ACTIVE)
        self.ui.comboBox_baud.setEnabled(False)
        self.ui.comboBox_parity.setEnabled(False)
        self.ui.checkBox_dsrdtr.setEnabled(False)
        self.ui.checkBox_rtscts.setEnabled(False)
        self.ui.checkBox_dsrdtr.setEnabled(False)
        self.ui.checkBox_xonxoff.setEnabled(False)
        self.ui.pushButton_connect.setText("Disconnect")

        self.serial_thread = QThread()
        self.serial_worker = SerialWorker()
        self.serial_worker.format = self.data_format
        self.serial_worker.moveToThread(self.serial_thread)
        self.serial_thread.started.connect(self.serial_worker.run)
        self.serial_worker.out.connect(self.add_text)
        self.serial_worker.disconnected.connect(self.serial_error)
        self.serial_thread.setTerminationEnabled(True)
        self.serial_thread.start()

        vprint("Serial Connection Success")
        self.update_status_bar()
        return True

    def find_port_name(self, input: str):
        if input.startswith("#"):
            port_index = int(input[1:])
            if port_index <= len(self.current_ports):
                return list(self.current_ports)[port_index]
            else:
                return None
        if input in self.current_ports:
            return input
        for port in self.current_ports:
            print(port)
            if self.current_ports[port]['disp'] == input:
                return self.current_ports[port]['dev']
        if input.upper() in self.current_ports:
            return input.upper()
        if "COM" + input in self.current_ports:
            return "COM" + input
        if "tty" + input in self.current_ports:
            return "tty" + input
        return None

    def handle_connect(self, *args, **kwargs):
        port: str = None
        baud: str = None
        xonxoff: bool = None
        dsrdtr: bool = None
        rtscts: bool = None
        parity: str = None

        if '-h' in kwargs:
            self.add_text(CONNECT_HELP, type=TYPE_HELP)
            return

        if args:  # Port name
            port = args[0]
            if args[0] == '?':
                self.ui.comboBox_port.showPopup()
                self.ui.comboBox_port.setFocus()
                return False
            port = self.find_port_name(args[0])
            if port == None:
                self.debug_text(f"ERR: PORT {args[0]} NOT FOUND", color=COLOR_RED)
                return
            if len(args) > 1:
                kwargs["-b"] = args[1]
                return
        else:
            port = self.find_port_name(self.ui.comboBox_port.currentText())


        if '-a' in kwargs:
            self.set_auto_reconnect(True, port)

        if '-d' in kwargs:
            dsrdtr = True
            self.ui.checkBox_dsrdtr.setChecked(True)
        else:
            dsrdtr = self.ui.checkBox_dsrdtr.isChecked()

        if '-x' in kwargs:
            xonxoff = True
            self.ui.checkBox_xonxoff.setChecked(True)
        else:
            xonxoff = self.ui.checkBox_xonxoff.isChecked()

        if '-r' in kwargs:
            rtscts = True
            self.ui.checkBox_rtscts.setChecked(True)
        else:
            rtscts = self.ui.checkBox_rtscts.isChecked()

        if '-p' in kwargs:
            parity = kwargs['-p'].upper()
            if parity not in parity_values:
                self.debug_text(f"PARITY {parity} INVALID", color=COLOR_RED)
                return
            self.ui.comboBox_parity.setCurrentText(parity)
        else:
            parity = self.ui.comboBox_parity.currentText()

        if '-b' in kwargs:
            baud = kwargs['-b']
            if baud not in self.get_combobox_items(self.ui.comboBox_baud):
                self.debug_text(f"ERR: BAUD RATE {baud} INVALID", color=COLOR_RED)
                return
            self.ui.comboBox_baud.setCurrentText(baud)
        else:
            baud = self.ui.comboBox_baud.currentText()

        if self.is_connected:
            if port != ser.port or kwargs:
                self.disconnect()
                self.handle_connect(*args, **kwargs)
            else:
                self.debug_text("ERR: ALREADY CONNECTED", color=COLOR_RED)
            return

        self.connect(port, baud, xonxoff, dsrdtr, rtscts, parity)

    def connect_clicked(self):
        if self.is_connected:
            self.disconnect()
        else:
            self.handle_connect()

    def set_auto_reconnect(self, enabled: bool = True, port: str = None):
        if enabled:
            if port:
                self.target_port = port
                self.ui.label_port.setText(f"Ports: (Auto {self.target_port})")
        else:
            self.ui.label_port.setText(f"Ports:")
            self.target_port = None

    def auto_reconnect_toggled(self):
        if self.ui.checkBox_auto_reconnect.isChecked():
            if self.is_connected:
                self.target_port = ser.port
                self.ui.label_port.setText(f"Ports: (Auto {self.target_port})")
                self.auto_reconnect_to = self.current_ports[self.target_port]['s/n']
        else:
            self.ui.label_port.setText(f"Ports:")
            self.target_port = None
            self.auto_reconnect_to = None

    def start_rescan(self):
        self.rescan_thread = QThread()
        self.rescan_worker = RescanWorker()
        self.rescan_worker.moveToThread(self.rescan_thread)
        self.rescan_thread.started.connect(self.rescan_worker.run)
        self.rescan_worker.new_ports.connect(self.update_ports)
        self.rescan_thread.start()

    def update_ports(self, ports: dict = None):
        if not ports:
            return

        ports_lost = set(self.current_ports).difference(set(ports))
        ports_found = set(ports).difference(set(self.current_ports))
        self.current_ports = ports

        if self.target_port and self.is_connected == False:
            if self.target_port in self.current_ports and self.ui.checkBox_auto_reconnect.isChecked():
                self.handle_connect(self.target_port)

        if not ports_found and not ports_lost:
            return

        if ports_lost:
            p_str = "LOST PORT(s): " + str(ports_lost)
            p_str = p_str.replace("{", '').replace("}", '').replace("'", '')
            self.debug_text(p_str, color=COLOR_RED)
        elif ports_found:
            p_str = "FOUND PORT(s): " + str(ports_found)
            p_str = p_str.replace("{", '').replace("}", '').replace("'", '')
            self.debug_text(p_str, color=COLOR_GREEN)

        current_selection = self.ui.comboBox_port.currentText()

        self.set_combobox_items(self.ui.comboBox_port, self.current_ports)

        if self.preference_port:
            if self.preference_port in self.current_ports:
                self.ui.comboBox_port.setCurrentText(self.preference_port)
                return

        if current_selection in self.current_ports:
            self.ui.comboBox_port.setCurrentText(current_selection)

    def show_ports(self, *args, **kwargs):
        self.debug_text(f"PORTS: {' '.join(self.current_ports)}", color=COLOR_BLACK)

        if not self.current_ports:
            self.add_text("NO PORTS FOUND", type=TYPE_HELP)
            return
        p_str = ""
        p_str += f"--#---NAME------------DISP----------------MFGR \n"
        for index, port in enumerate(self.current_ports):
            this_port = self.current_ports[port]
            p_str += f'''({index :>3}) {port :<15} {this_port["disp"]:<20}{this_port["mfgr"]}\n'''
            if not args:
                continue
            if args and args[0] not in this_port:
                for item in this_port:
                    p_str += f"    {item}:\t{str(this_port[item])}\n"
            else:
                p_str += f"    {args[0]}:\t{str(this_port[args[0]])}\n"

        self.add_text(p_str, type=TYPE_HELP)


########################################################################
#
#               SETTINGS FUNCTIONS
#
########################################################################

    def create_settings(self):
        self.save_checkboxes = [self.ui.checkBox_auto_reconnect,
                                self.ui.checkBox_auto_save_settings,
                                self.ui.checkBox_output_include_terminal,
                                self.ui.checkBox_output_include_log,
                                self.ui.checkBox_error_include_log,
                                self.ui.checkBox_error_include_terminal,
                                self.ui.checkBox_info_include_log,
                                self.ui.checkBox_info_include_terminal,
                                self.ui.checkBox_autoscroll,
                                self.ui.checkBox_timestamp,
                                self.ui.checkBox_allow_commands,
                                self.ui.checkBox_autolog,
                                self.ui.checkBox_interpret_escape,
                                ]

        self.save_line_edits = [self.ui.lineEdit_err_chr,
                                self.ui.lineEdit_info_chr,
                                self.ui.lineEdit_max_points,
                                self.ui.lineEdit_append_to_send,
                                self.ui.lineEdit_tx_chr,
                                self.ui.lineEdit_log_format,
                                self.ui.lineEdit_command_char,
                                self.ui.lineEdit_delay,
                                self.ui.lineEdit_ref_lines,
                                self.ui.lineEdit_target_keys,
                                self.ui.lineEdit_seps,
                                self.ui.lineEdit_limits,
                                self.ui.lineEdit_timestamp_format,
                                ]

        self.log_save_line_edits = [self.ui.lineEdit_time_format,
                                    self.ui.lineEdit_log_folder,
                                    self.ui.lineEdit_log_format,
                                    self.ui.lineEdit_log_name]

        self.save_combo_boxes = [self.ui.comboBox_baud,
                                 self.ui.comboBox_plot_type,
                                 ]

        for checkbox in self.save_checkboxes:
            checkbox.stateChanged.connect(self.save_settings)

        for lineEdit in self.save_line_edits:
            lineEdit.textChanged.connect(self.save_settings)

        for comboBox in self.save_combo_boxes:
            comboBox.currentTextChanged.connect(self.save_settings)

    def save_item(self, object, filepath=SETTINGS_FILE):
        if isinstance(object, (tuple, list)):
            print("SETTING OBJECT", object)

        elif isinstance(object, QtWidgets.QComboBox):
            object: QtWidgets.QComboBox
            self.current_settings[object.objectName()] = object.currentText()
        elif isinstance(object, QtWidgets.QLineEdit):
            object: QtWidgets.QLineEdit
            self.current_settings[object.objectName()] = object.text()
        elif isinstance(object, QtWidgets.QCheckBox):
            object: QtWidgets.QCheckBox
            self.current_settings[object.objectName()] = object.isChecked()
        elif isinstance(object, QtWidgets.QTextEdit):
            object: QtWidgets.QTextEdit
            self.current_settings[object.objectName()] = object.toPlainText()
        with open(filepath, 'w') as file:
            json.dump(self.current_settings, file)

    def save_settings(self):
        '''Save Settings After One Second'''  # This is so multiple saves arent attempted for multiple edits
        if (time.perf_counter() - self.last_save_time < 1.00):
            return

        self.save_timer.singleShot(1000, self._save_settings)
        self.last_save_time = time.perf_counter()

    def _save_settings(self, filepath=SETTINGS_FILE):
        '''Actual Save Settings Here'''
        vprint("SAVED SETTINGS", color='green')
        for checkbox in self.save_checkboxes:
            self.current_settings[checkbox.objectName()] = checkbox.isChecked()
        for line_edit in self.save_line_edits:
            self.current_settings[line_edit.objectName()] = line_edit.text()
        for combo_box in self.save_combo_boxes:
            self.current_settings[combo_box.objectName()] = combo_box.currentText()
        self.command_char = self.ui.lineEdit_command_char.text()
        self.current_settings['tableWidget_keys'] = self.get_key_cmds()
        with open(filepath, 'w') as file:
            json.dump(self.current_settings, file)

    def recall_settings(self, filepath: str = SETTINGS_FILE):
        vprint(f"Loading Settings from {filepath}", color='cyan')
        if not os.path.exists(filepath):
            vprint("FIRST PROGRAM LOAD", color='yellow')
            with open(filepath, 'w') as file:
                pass
            self._save_settings()
            return
        try:
            with open(filepath, 'r') as file:
                self.current_settings = json.load(file)

                if 'port_aliases' not in self.current_settings:
                    self.current_settings['port_aliases'] = {}

            if 'lineEdit_log_folder' in self.current_settings and not self.current_settings['lineEdit_log_folder']:
                self.current_settings['lineEdit_log_folder'] = DEFAULT_LOG_FOLDER

            for checkbox in self.save_checkboxes:
                checkbox: QtWidgets.QCheckBox
                if checkbox.objectName() in self.current_settings:
                    checkbox.setChecked(self.current_settings[checkbox.objectName()])
                else:
                    self.save_item(checkbox)

            for combo_box in self.save_combo_boxes:
                combo_box: QtWidgets.QComboBox
                if combo_box.objectName() in self.current_settings:
                    combo_box.setCurrentText(
                        self.current_settings[combo_box.objectName()])
                else:
                    self.save_item(combo_box)

            for line_edit in self.save_line_edits:
                line_edit: QtWidgets.QLineEdit
                if line_edit.objectName() in self.current_settings:
                    line_edit.setText(
                        self.current_settings[line_edit.objectName()])
                else:
                    self.save_item(line_edit)

            for item in self.current_settings['tableWidget_keys']:
                self.add_key_cmd(item, self.current_settings['tableWidget_keys'][item])

            if 'lineEdit_script_name' in self.current_settings:
                last_script_name: str = self.current_settings['lineEdit_script_name']
                vprint("LAST SCRIPT NAME: ", last_script_name)
                if last_script_name:
                    self.open_script(last_script_name)
                else:
                    self.ui.lineEdit_script_name.clear()

            self.command_char = self.ui.lineEdit_command_char.text()

        except Exception as E:
            eprint(f"\nERROR IN RECALLING SETTINGS: {E}", color='red')

    def print_settings(self, filename=SETTINGS_FILE):
        vprint(f"PRINTING SETTINGS {filename}")

        filepath, exists = get_file_name(filename, SETTINGS_FOLDER, '.json')
        if not exists:
            eprint("NO FILE", filename)
            return

        settings: dict = {}
        with open(filepath, 'r') as file:
            settings: dict = json.load(file)
        self.add_text(f"{filepath}\n", type=TYPE_HELP)
        for name, value in settings.items():
            if not isinstance(value, (list, dict)):
                self.add_text(f"  {name}={value}\n", type=TYPE_HELP)

    def handle_settings_command(self, *args, **kwargs):
        if not args and not kwargs:
            #self.add_text(SETTINGS_HELP, type=TYPE_HELP)
            self.print_settings()
            return

        if '-h' in kwargs:
            self.add_text(SETTINGS_HELP, type=TYPE_HELP)
            return
        if '-p' in kwargs:
            if kwargs['-p']:
                self.print_settings(kwargs['-p'])
            else:
                self.print_settings()
            return

        if args:
            temp_filename = SETTINGS_FOLDER + '/.tmp.json'
            for arg in args:
                arg: str
                print("arg", arg)
                tokens = arg.split("=", 1)
                if len(tokens) > 1 and tokens[0] in self.current_settings:
                    print(tokens)
                    if tokens[1] == 'False':
                        tokens[1] = False
                    elif tokens[1] == 'True':
                        tokens[1] = True
                    self.current_settings[tokens[0]] = tokens[1]
                    print(self.current_settings)
                else:
                    self.add_text(f"INVALID SETTING: {tokens}\n", type=TYPE_ERROR)
                    return
            with open(temp_filename, 'w') as file:
                json.dump(self.current_settings, file)
            self.recall_settings(temp_filename)
            os.remove(temp_filename)
            self.ui.tabWidget.setCurrentIndex(0)

        if '-s' in kwargs:
            filepath = None
            if kwargs['-s']:
                filepath, exists = get_file_name(kwargs['-s'], SETTINGS_FOLDER, '.json')
            else:
                filepath = self.get_save_file(SETTINGS_FOLDER, extensions='*.json')
                if not filepath:
                    return
            self.add_text(f"Saved Settings: {filepath}\n", type=TYPE_INFO)
            self._save_settings(filepath)
            return

        if '-o' in kwargs:
            filepath = None
            if kwargs['-o']:
                filepath, exists = get_file_name(kwargs['-o'], SETTINGS_FOLDER, '.json')
                if not exists:
                    self.add_text(f"Settings File NOT FOUND:\n'{filepath}'\n", type=TYPE_ERROR)
                    return
            else:
                filepath = self.get_file(SETTINGS_FOLDER, extensions='*.json')
                if not filepath:
                    return
            self.recall_settings(filepath)
            self.add_text(f"Loaded Settings: {filepath}\n", type=TYPE_INFO)
            return


########################################################################
#
#               COMMAND FUNCTIONS
#
########################################################################

    def print_cmds(self):
        for cmd in self.cmd_list:
            self.add_text(cmd, type=TYPE_INFO)
        return

    def create_commands(self):
        self.cmd_list.append(Command("help", self.print_help))
        self.cmd_list.append(Command("ports", self.show_ports, 1))
        self.cmd_list.append(Command("clear", self.clear_clicked, 0))
        self.cmd_list.append(Command("quit", self.make_quit))
        self.cmd_list.append(Command("exit", self.make_quit))

        cmd_con = Command("con", self.handle_connect, 1)
        cmd_con.add_option(("-h", "--help"))
        cmd_con.add_option(("-b", "--baud"))
        cmd_con.add_option(("-d", "--dtscts"))
        cmd_con.add_option(("-x", "--xonxoff"))
        cmd_con.add_option(("-r", "--rtscts"))
        cmd_con.add_option(("-p", "--parity"))
        cmd_con.add_option(("-a", "--auto"))
        self.cmd_list.append(cmd_con)

        self.cmd_list.append(Command("dcon", self.disconnect, 0))

        cmd_script = Command("script", self.handle_script_command)
        cmd_script.add_option(("-h", "--help"))
        cmd_script.add_option(("-o", "--open"))
        cmd_script.add_option(("-t", "--tab"))
        cmd_script.add_option(("-n", "--new"))
        cmd_script.add_option(("-ls", "--list"))
        cmd_script.add_option(("-rm", "--remove"))
        cmd_script.add_option(("-s", "--save"))
        cmd_script.add_option(("-r", "--run"))
        cmd_script.add_option(("-a", "--arg"))

        self.cmd_list.append(cmd_script)

        cmd_plot = Command("plot", self.handle_plot_command, 1)
        cmd_plot.add_option(("-h", "--help"))
        cmd_plot.add_option(("-p", "--points"))
        cmd_plot.add_option(("-k", "--keys"))
        cmd_plot.add_option(("-l", "--limits"))
        cmd_plot.add_option(("-r", "--ref"))
        cmd_plot.add_option(("-s", "--seps"))
        cmd_plot.add_option(("-t", "--test"))
        cmd_plot.add_option(("csv", "export", "CSV", "--csv"))
        cmd_plot.add_option(("--round"), require_values=1)

        self.cmd_list.append(cmd_plot)

        cmd_keys = Command("key", self.handle_key_cmd, 3)
        cmd_keys.add_option(("-h", "--help"))

        self.cmd_list.append(cmd_keys)

        cmd_log = Command("log", self.handle_log_command, 0)
        cmd_log.add_option(("-h", "--help"))
        cmd_log.add_option(("-o", "--open"))
        cmd_log.add_option(("-a", "--archive"))
        cmd_log.add_option(("-ls", "--list"))
        cmd_log.add_option(("-n", '--new'))
        cmd_log.add_option(("--nfmt"))
        cmd_log.add_option(("--tfmt"))
        cmd_log.add_option(("--fmt"))
        cmd_log.add_option(("--disable"))
        cmd_log.add_option(("--enable"))
        
        #cmd_log.add_option(("--name"))
        self.cmd_list.append(cmd_log)

        cmd_cow = Command("cowsay", self.cowsay)
        cmd_cow.add_option(("-n", "--nerd"))
        cmd_cow.add_option(("-d", "--dead"))
        cmd_cow.add_option(("-l"))
        self.cmd_list.append(cmd_cow)

        self.cmd_list.append(Command("new", self.open_new_window))

        cmd_format = Command("format", self.set_format, 1)
        self.cmd_list.append(cmd_format)

        self.cmd_list.append(Command("cmd", self.print_cmds, 0))

        cmd_settings = Command("settings", self.handle_settings_command)
        cmd_settings.add_option(('-s', '--save'))
        cmd_settings.add_option(('-o', '--open'))
        cmd_settings.add_option(('-h', '--help'))
        cmd_settings.add_option(('-p', '--print'))
        self.cmd_list.append(cmd_settings)

        cmd_port_alias = Command("alias", self.port_alias)
        cmd_port_alias.add_option(("-rm", "--remove"), require_values=1)
        self.cmd_list.append(cmd_port_alias)

    def set_format(self, format: str):
        if format in ['utf-8', 'hex', 'bin', 'dec']:
            self.data_format = format
            if self.is_connected:
                self.serial_worker.format = self.data_format
        else:
            eprint("INVALID")

        vprint(format)

    def port_alias(self, *args, **kwargs):
        vprint("PORT ALIAS: ", args)
        if '-rm' in kwargs:
            if kwargs["-rm"] and kwargs['-rm'] in self.current_settings['port_aliases']:
                self.current_settings['port_aliases'].pop(kwargs['-rm'])

            return
            #self.current_settings['port_aliases'][args[0]] = args[1]

        if len(args) == 0:
            self.add_text(self.current_settings['port_aliases'], '\n', type=TYPE_INFO)
        if len(args) == 2:
            self.current_settings['port_aliases'][args[0]] = args[1]
            self.save_settings()
        pass

    def interpret_command(self, text: str):
        """execute a command. Returns NONE if no command found"""
        text = text.rstrip()
        #text = text.replace("\n", "").replace("\r", "")
        if not text:
            return None
        if not self.ui.checkBox_allow_commands.isChecked():
            return None
        if self.command_char:
            if text[0] != self.command_char:
                return None
            text = text[1:]
            vprint(f"POSSIBLE CMD: <{text}>", color='yellow')

        for cmd in self.cmd_list:
            cmd: Command
            result, error_str = cmd.execute(text)
            if result is None:
                continue
            else:
                return error_str
        return None

########################################################################
#
#               SCRIPT FUNCTIONS
#
########################################################################

    def handle_script_command(self, *args, **kwargs):
        delay = None
        arg_str = ""
        run_script = True
        run_script_name = None

        args = list(args)

        if '-h' in kwargs:
            self.add_text(SCRIPT_HELP + SCRIPT_SYNTAX_HELP, type=TYPE_HELP)
            return
        if '-f' in kwargs:
            self.open_folder_location(SCRIPT_FOLDER)
            return
        if "-a" in kwargs:
            arg_str = kwargs['-a']
        for arg in args: 
            arg_str += arg + " "
        if '-ls' in kwargs:
            self.list_files(SCRIPT_FOLDER)
            return
        if '-rm' in kwargs:
            if isinstance(kwargs['-rm'], list):
                for i in kwargs['-rm']:
                    self.delete_script(i)
            else:
                self.delete_script(kwargs['-rm'])
            return

        if '-n' in kwargs:
            self.ui.textEdit_script.clear()
            self.ui.tabWidget.setCurrentIndex(1)
            self.ui.textEdit_script.setFocus()
            self.ui.lineEdit_script_name.clear()
            if kwargs['-n']:
                self.ui.lineEdit_script_name.setText(
                    kwargs["-n"].replace(".txt", ""))
            return
        if "-t" in kwargs:
            self.ui.tabWidget.setCurrentIndex(1)
            self.ui.textEdit_script.setFocus()
            return
        if '-o' in kwargs:
            if not self.open_script(kwargs['-o']):
                return
            run_script = False
        if '-s' in kwargs:
            self.save_script(kwargs['-s'])
            return
        if '-r' in kwargs:
            run_script = True

        if '-d' in kwargs:
            if kwargs['-d']:
                delay = get_number(kwargs['-d'])
            else:
                self.debug_text(f"Script ARG '-d' requires value")
                return

        if run_script:
            self.start_script(run_script_name, delay, arg_str)

    def open_script(self, file_name: str = None):
        file_path = find_file(self, SCRIPT_FOLDER, file_name)
        if file_path == "" or file_path == False:
            return False
        if file_path == None:
            self.debug_text(f"ERR: file '{file_name}' not found", color=COLOR_RED)
            return False
        vprint(f"OPENING SCRIPT {file_name}", color='blue')
        with open(file_path, 'r') as file:
            self.ui.textEdit_script.setPlainText(file.read())
        self.ui.lineEdit_script_name.setText(file_path.split('/')[-1].replace('.txt', ''))
        self.ui.tabWidget.setCurrentIndex(1)
        self.ui.textEdit_script.setFocus()
        return True

    def delete_script(self, file_name: str = None):
        file_path = find_file(self, SCRIPT_FOLDER, file_name)
        if file_path == "":
            return
        if file_path == None:
            self.add_text(f"COULD NOT REMOVE {file_name}\n", type == TYPE_ERROR)
            return
        if not (file_path.endswith(".txt")):
            self.add_text(f"INVALID FILE {file_name}\n", type == TYPE_ERROR)
            return
        if self.ui.lineEdit_script_name.text() == file_name:
            self.ui.lineEdit_script_name.clear()
            self.ui.textEdit_script.clear()
        self.add_text(f"REMOVED: {file_path}\n", type=TYPE_INFO)
        os.remove(file_path)

    def save_script(self, file_name: str = None, save_as=False):
        file_path: str = None
        if save_as:
            file_path = self.get_save_file(INSTALL_FOLDER + '/scripts', "*.txt", "Save Script")
            file_name = file_path.split('/')[-1]
            if not file_path:
                return
        if not file_name:
            if self.ui.lineEdit_script_name.text():
                file_name = self.ui.lineEdit_script_name.text() + ".txt"
                file_path = file_path = INSTALL_FOLDER + "/scripts/" + file_name
            else:
                file_path = self.get_save_file(INSTALL_FOLDER + '/scripts', "*.txt", "Save Script")
                file_name = file_path.split('/')[-1]
            if not file_path:
                return
        else:
            if file_name.endswith(".txt") == False:
                file_name += '.txt'
            if '/' not in file_name and '\\' not in file_name:
                file_path = INSTALL_FOLDER + "/scripts/" + file_name
            else:
                file_path = file_name
        with open(file_path, 'w') as file:
            file.write(self.ui.textEdit_script.toPlainText())
        self.ui.lineEdit_script_name.setText(file_name.replace(".txt", ""))
        self.debug_text(f"Saved '{file_name}'", color=COLOR_GREEN)

    def script_line(self, line: list):
        if line[1] == TYPE_TX:
            self.ui.lineEdit_input.setText(line[0])
            self.send_clicked(add_to_history=False)
        elif line[1] == TYPE_CMD:
            line[0] = self.input_text_evaluate(line[0])
            self.interpret_command(line[0])
        else:
            self.add_text(self.input_text_evaluate(line[0]), type=line[1])
        return

    def start_script(self, file_name: str = None, delay=None, arg_str=""):
        if delay == None:
            delay = get_number(self.ui.lineEdit_delay.text(), int, DEFAULT_SCRIPT_DELAY)
        text: str = None
        if not file_name:
            text = self.ui.textEdit_script.toPlainText()
            file_name = self.ui.lineEdit_script_name.text()
        else:
            if not file_name.endswith(".txt"):
                file_name += ".txt"
            text = self.read_file(INSTALL_FOLDER + "/scripts/" + file_name)
            if text == None:
                self.add_text(f"Script '{file_name}' NOT FOUND\n", type=TYPE_ERROR)
        if not text:
            return

        if file_name:
            self.save_item(self.ui.lineEdit_script_name)
            self.save_script(file_name)

        self.debug_text("SCRIPT STARTED")

        self.ui.lineEdit_input.setDisabled(True)
        self.ui.lineEdit_keyboard_control.setDisabled(True)
        self.ui.pushButton_send.setDisabled(True)
        self.ui.tabWidget.setCurrentIndex(0)

        self.script_thread = QThread()
        self.script_worker = ScriptWorker(text, delay, arg_str)
        self.script_worker.moveToThread(self.script_thread)
        self.script_thread.started.connect(self.script_worker.run)
        self.script_worker.line.connect(self.script_line)
        self.script_worker.finished.connect(self.end_script)
        self.script_thread.start()

        vprint("RUNNING SCRIPT: ", text, color='yellow')

    def end_script(self):
        if self.script_worker is None:
            return

        self.ui.lineEdit_input.clear()
        self.ui.lineEdit_input.setDisabled(False)
        self.ui.lineEdit_keyboard_control.setDisabled(False)
        self.ui.pushButton_send.setDisabled(False)
        self.ui.lineEdit_input.setFocus()
        self.script_thread.exit()
        self.script_worker.stop()
        self.script_worker = None
        self.debug_text("SCRIPT ENDED", color=COLOR_GREEN)
        return
########################################################################
#
#               LOGGING FUNCTIONS
#
########################################################################

    def handle_log_command(self, **kwargs):
        if not kwargs:
            self.open_log()

        if '-h' in kwargs or "--help" in kwargs:
            self.add_text(LOG_HELP, type=TYPE_HELP)
            return
        if '-f' in kwargs:
            self.open_folder_location(DEFAULT_LOG_FOLDER)
            return
        if '-o' in kwargs or '--open' in kwargs:
            if kwargs['-o']:
                log_file = DEFAULT_LOG_FOLDER + kwargs["-o"]
                if not log_file.endswith((".txt", ".csv")):
                    log_file += ".txt"
                if not os.path.exists(log_file):
                    self.add_text(f"Log file {log_file} not found", type=TYPE_ERROR)
                    return
            else:
                log_file = self.get_file(DEFAULT_LOG_FOLDER)
            if log_file:
                self.open_log(log_file)
            return
        if '-ls' in kwargs:
            self.list_files(DEFAULT_LOG_FOLDER)
            return
        if '-a' in kwargs:
            self.log.archive(kwargs['-a'], self.ui.comboBox_log_name_extension.currentText())
            return
        if '-n' in kwargs:
            self.start_logger(kwargs['-n'])
            return
        if '--nfmt' in kwargs:
            self.ui.lineEdit_log_name.setText(kwargs['--name'])
        if '--tfmt' in kwargs:
            self.ui.lineEdit_time_format.setText(kwargs['--tfmt'])
        if '--fmt' in kwargs:
            self.ui.lineEdit_log_format.setText(kwargs['--fmt'])
        if '--enable' in kwargs:
            self.ui.checkBox_autolog.setChecked(True)
        if '--disable' in kwargs:
            self.ui.checkBox_autolog.setChecked(False)

    def set_log_folder(self, log_folder: str = None):
        if not log_folder:
            log_folder = self.get_directory(DEFAULT_LOG_FOLDER)
        self.ui.lineEdit_log_folder.setText(log_folder)

    def log_settings_changed(self):
        self.ui.pushButton_restart_logger.setEnabled(True)
        self.ui.pushButton_restart_logger.setStyleSheet(STYLE_SHEET_BUTTON_ACTIVE)
        pass

    def start_logger(self, filename:str = None):
        folder_path = self.ui.lineEdit_log_folder.text()

        file_extension = self.ui.comboBox_log_name_extension.currentText()
        file_name = time.strftime(self.ui.lineEdit_log_name.text())

        if filename is not None:
            toks = filename.split('.')
            file_name = toks[0]
            if len(toks) > 1:
                file_extension = '.' + toks[-1]

        
        log_fmt = replace_escapes(self.ui.lineEdit_log_format.text())
        time_fmt = replace_escapes(self.ui.lineEdit_time_format.text())
        if not (os.path.isdir(folder_path)):
            folder_path = DEFAULT_LOG_FOLDER
            self.ui.lineEdit_log_folder.setText(folder_path)
        port_name = None
        if self.is_connected:
            port_name = ser.port
        self.log = SK_Logger(folder_path, file_name + file_extension, time_fmt, log_fmt, port_name)
        self.ui.pushButton_restart_logger.setEnabled(False)
        self.ui.pushButton_restart_logger.setStyleSheet(STYLE_SHEET_BUTTON_INACTIVE)

    def open_log(self, log_file=None):
        if not log_file:
            log_file = self.log.file_path
        open_log_viewer(self, log_file)


########################################################################
#
#               PLOT FUNCTIONS
#
########################################################################

    def start_plot_clicked(self):
        if self.plot_started:
            self.end_plot()
        else:
            self.start_plot()

    def handle_plot_command(self, *args, **kwargs):
        plot_type = None
        targets = None
        max_points = None
        reference_lines = None
        limits = None
        separators = None

        for arg in args:
            if arg == "pause" or arg == "p":
                self.pause_plot()
                return
            if arg == "resume" or arg == 'r':
                self.pause_plot()
                return
            elif arg == "clear" or arg == "c":
                self.end_plot()
                return
            elif arg == "kv" or arg.upper() == "KEY-VALUE":
                plot_type = "Key-Value"
            elif arg == "sa" or arg.upper() == "SINGLE-ARRAY":
                plot_type = "Single-Array"
            elif arg == "ka" or arg.upper() == "KEY-ARRAY":
                plot_type = "Key-Array"
            elif arg == "sv" or arg.upper() == "SINGLE-VALUE":
                plot_type = "Single-Value"

            elif arg == "k3d" or arg.upper() == "KEY-3D":
                plot_type = "Key-3D"



        if 'csv' in kwargs: 
            if '--round' in kwargs: 
                round_to = float(kwargs["--round"])
                if abs(round_to) > 1.00:
                    round_to = round_to / 1000
                self.export_csv(kwargs['csv'], round_to)
            else: 
                self.export_csv(kwargs['csv'])
            return 

        if '-h' in kwargs or '--help' in kwargs:
            self.add_text(PLOT_HELP, type=TYPE_HELP)
            return

        if '-t' in kwargs:
            print(kwargs['-t'])
            if self.plot_started:
                self.ui.widget_plot.update(kwargs['-t'], False)

        if '-s' in kwargs:
            separators = kwargs['-s']
            if not separators:
                separators = ""

        if '-r' in kwargs:
            reference_lines = kwargs['-r']
            if not reference_lines:
                reference_lines = ""

        if '-l' in kwargs:
            limits = kwargs['-l']

        if '-k' in kwargs:
            targets = kwargs['-k']
            self.ui.lineEdit_target_keys.setText(kwargs['-k'])

        if '-p' in kwargs:
            max_points = kwargs['-p']

        if limits:
            self.ui.lineEdit_limits.setText(str(limits))

        if reference_lines != None:
            self.ui.lineEdit_ref_lines.setText(reference_lines)

        if targets != None:
            self.ui.lineEdit_target_keys.setText(targets)

        if max_points != None:
            self.ui.lineEdit_max_points.setText(max_points)

        if separators != None:
            self.ui.lineEdit_seps.setText(separators)

        if plot_type:
            self.ui.comboBox_plot_type.setCurrentText(plot_type)
            self.start_plot()

    def start_plot(self):
        if self.plot_started:
            self.end_plot()
            self.start_plot()

        limits = self.lineEdit_to_numbers(self.ui.lineEdit_limits, ',')
        # print(limits)
        type = self.ui.comboBox_plot_type.currentText()
        targets = self.ui.lineEdit_target_keys.text()
        max_points = self.lineEdit_to_numbers(self.ui.lineEdit_max_points)

        if max_points == None:
            max_points = 100

        ref_lines = self.lineEdit_to_numbers(self.ui.lineEdit_ref_lines, separator=',')
        seps = [char for char in replace_escapes(self.ui.lineEdit_seps.text())]

        self.plot_started = True
        self.ui.pushButton_start_plot.setText("Stop Plot")
        self.ui.pushButton_start_plot.setStyleSheet(STYLE_SHEET_BUTTON_ACTIVE)
        self.ui.pushButton_pause_plot.setText("Pause Plot")
        self.ui.pushButton_start_plot.setStyleSheet(STYLE_SHEET_BUTTON_ACTIVE)
        self.ui.tabWidget.setCurrentIndex(2)
        self.ui.widget_plot.begin(type, targets, max_points, limits, seps, ref_lines)

    def pause_plot(self):
        if self.ui.widget_plot.paused:
            self.ui.widget_plot.resume()
            self.ui.pushButton_pause_plot.setText("Pause Plot")
        else:
            self.ui.pushButton_pause_plot.setText("Resume Plot")
            self.ui.widget_plot.pause()

    def end_plot(self):
        self.ui.pushButton_start_plot.setText("Start Plot")
        self.ui.pushButton_start_plot.setStyleSheet(STYLE_SHEET_BUTTON_INACTIVE)
        self.ui.widget_plot.reset()
        self.plot_started = False

    def export_csv(self, filename: str = None, round_to = .025):
        if not self.ui.widget_plot.elements:
            vprint("No data to export", color='red')
            self.debug_text("No data to export", color=COLOR_RED)
            return
        if not filename:
            filename = self.get_save_file(os.path.join(INSTALL_FOLDER, "logs"), "*.csv", "Export CSV")
        if not filename:
            vprint("Export CSV Cancelled", color='red')
            return
        if not filename.endswith(".csv"):
            filename += ".csv"

        if not os.path.isabs(filename):
            filename = os.path.join(INSTALL_FOLDER, "logs", filename)
        vprint("EXPORT CSV: ", filename, color = "green")

        backup = get_backup_filename(filename)

        print("backup:", backup)
        if backup: 
            shutil.copy2(filename, backup)
            self.add_text(f"CSV File exists, backing up to:\n\t{backup}\n", type=TYPE_INFO)

        keys = ["SECONDS"]
        keys += list(self.ui.widget_plot.elements.keys())

        empty = {}
        for key in keys: 
            empty[key] = None 
        #print(keys)
        elements = self.ui.widget_plot.elements
        data = {}
        for element in elements:
            vprint(f"CSV COL {element} Len: {len(elements[element]['x'])} {round_to}", color = "green")
            for index,timestamp in enumerate(elements[element]['x']):
                timestamp = discrete_round(timestamp, round_to)
                
                if timestamp not in data: 
                    #print(timestamp, round_to < 0)
                    data[timestamp] = empty.copy()
                    data[timestamp]["SECONDS"] = timestamp 
                data[timestamp][element] = float(elements[element]['y'][index])

        data = dict(sorted(data.items(), reverse = round_to < 0))

        with open(filename, 'w+', newline='', encoding='utf-8') as file: 
            writer = csv.DictWriter(file, keys)
            writer.writeheader()
            for element in data: 
                writer.writerow(data[element])
                #print(element, data[element])
                #print(index, timestamp)

        self.add_text(f"Wrote CSV to:\n\t{filename}\n", type = TYPE_INFO)
        self.debug_text(f"Wrote CSV", color = COLOR_GREEN)


########################################################################
#
#               KEYBOARD FUNCTIONS
#
########################################################################
    def handle_key_cmd(self, *args, **kwargs):

        if "-h" in kwargs:
            self.add_text(KEY_HELP, type=TYPE_HELP)
            return

        args = list(args)

        if not args:
            self.ui.lineEdit_keyboard_control.setFocus()
            return

        while args:
            arg = args.pop(0)
            if arg == "clear":
                self.clear_key_cmds()
                return
            elif arg == "set":
                if len(args) < 2:
                    print("TOO FEW ARGUMENTS")
                else:
                    self.add_key_cmd(args[0], args[1])
                    return

    def get_key_cmds(self):
        key_cmds = {}
        for row in range(self.ui.tableWidget_keys.rowCount()):
            if self.ui.tableWidget_keys.item(row, 0) is not None:
                if not self.ui.tableWidget_keys.item(row, 0).text():
                    continue
                if self.ui.tableWidget_keys.item(row, 1) is not None:
                    key_cmds[self.ui.tableWidget_keys.item(row, 0).text()] = self.ui.tableWidget_keys.item(row, 1).text()
        return key_cmds

    def clear_key_cmds(self):
        self.ui.tableWidget_keys.setRowCount(0)
        self.ui.tableWidget_keys.setRowCount(1)

    def key_cmds_edited(self):
        if self.ui.tableWidget_keys.currentRow() == self.ui.tableWidget_keys.rowCount() - 1:
            if not self.ui.tableWidget_keys.currentItem():
                return
            self.ui.tableWidget_keys.setRowCount(self.ui.tableWidget_keys.rowCount()+1)
        self.key_cmds = self.get_key_cmds()
        if self.key_cmds:
            self.ui.lineEdit_keyboard_control.setEnabled(True)
        else:
            self.ui.lineEdit_keyboard_control.setEnabled(False)
        self.save_settings()

    def add_key_cmd(self, key: str, send: str):
        indx = None
        items = self.ui.tableWidget_keys.findItems(key, QtCore.Qt.MatchExactly)
        for item in items:
            if item.column() == 0:  # Item is already a key
                indx = item.row()

        if indx == None:
            indx = self.ui.tableWidget_keys.rowCount() - 1
            self.ui.tableWidget_keys.setRowCount(indx + 2)
        self.ui.tableWidget_keys.setItem(indx, 0, QTableWidgetItem(str(key)))
        self.ui.tableWidget_keys.setItem(indx, 1, QTableWidgetItem(str(send)))
        self.key_cmds_edited()

    def keyboard_control(self, key: str):
        vprint(key, color='green', end='\t')
        if not key:
            key = self.ui.lineEdit_keyboard_control.text()
        if not key:
            return
        self.ui.lineEdit_keyboard_control.clear()
        key_cmds = self.get_key_cmds()
        
        vprint(key_cmds, color='red')
        if key in key_cmds:
            self.ui.lineEdit_input.setText(key_cmds[key])
            self.send_clicked(add_to_history=False)
        else:
            self.debug_text(f"KEY {key} not in Keyboard commands", color=COLOR_RED)

########################################################################
#
#               MISC FUNCTIONS
#
########################################################################

    def change_timestamp_format(self, fmt: str = None):

        if fmt == None:
            fmt = self.ui.lineEdit_timestamp_format.text()
        fmt = replace_escapes(fmt)
        try:
            vprint(f"FMT Changed: {fmt} {self.open_time.strftime(fmt)}", color='green')
            self.timestamp_format = fmt
            self.ui.lineEdit_timestamp_format.setStyleSheet(STYLE_SHEET_LINE_EDIT_NORMAL)
            self.ui.label_timestamp_preview.setText(f"Preview:{self.open_time.strftime(fmt)}TEXT...")
        except Exception as E:
            eprint(f"FMT INVALID: {fmt} {E}", color='red')
            self.ui.lineEdit_timestamp_format.setStyleSheet(STYLE_SHEET_LINE_EDIT_ERROR)
            self.ui.label_timestamp_preview.setText(f"FORMAT INVALID")

    def get_time_string(self):
        return datetime.now().strftime(self.timestamp_format)

    def lineEdit_to_numbers(self, lineEdit: QLineEdit, separator=None):
        text = lineEdit.text().replace(" ", "")
        if not separator:
            try:
                r_val = float(text)
                return r_val
            except ValueError as E:
                eprint(f"ERROR IN LINE EDIT {lineEdit.objectName()}: {E}")
                return None
        else:
            r_vals = []
            tokens = text.split(separator)
            for token in tokens:
                if not token:
                    continue
                try:
                    val = float(token)
                    r_vals.append(val)
                except ValueError as E:
                    eprint(f"ERROR IN LINE EDIT {lineEdit.objectName()}: {E}")
                    return None
            return r_vals

    def cowsay(self, *args, **kwargs):
        self.add_text(get_cow(*args, **kwargs), type=TYPE_HELP)

    def open_folder_location(self, folder_path: str):
        if USER_OS != "Windows":
            return False
        if not os.path.isdir(folder_path):
            return False
        os.startfile(folder_path)

    def open_github_repo(self):
        import webbrowser
        self.debug_text("OPENING GITHUB REPO", color=COLOR_GREEN)
        webbrowser.open(GITHUB_URL)

    def open_new_window(self, *args):
        import platform
        import subprocess

        if platform.system() == 'Windows':
            cmd = f'start pythonw.exe {INSTALL_FOLDER}/serial_killer.py '
        elif platform.system() == 'Linux':
            cmd = f'python3 {INSTALL_FOLDER}/serial_killer.py '

        for arg in args:
            cmd += arg + " "

        print("OPENING NEW WINDOW ", cmd)
        subprocess.call(cmd, shell=True)

    def get_latest_file(self, directory: str):
        list_of_files = glob.glob(directory + "*.txt")
        latest_file = max(list_of_files, key=os.path.getmtime)
        return latest_file

    def list_files(self, directory: str):
        list_of_files = filter(lambda x: os.path.isfile(os.path.join(directory, x)),
                               os.listdir(directory))
        files = sorted(list_of_files, key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
        files_str = ""
        for file in files:
            file_timestamp = os.path.getmtime(directory + file)
            last_t = datetime.fromtimestamp(file_timestamp)
            last_modified = last_t.strftime("%m/%d/%Y %H:%M")
            file_size = os.path.getsize(directory + file)
            files_str += f"{last_modified : <15}{file_size : >10} {file : <12}\n"

        self.add_text(files_str, type=TYPE_HELP)
        return files_str

    def get_file(self, start_dir: str = None, extensions: str = None, title: str = "Open") -> str:
        files = QFileDialog.getOpenFileName(self, caption=title, directory=start_dir, filter=extensions)
        return files[0]

    def get_save_file(self, start_dir: str = None, extensions: str = None, title: str = "Save") -> str:
        files = QFileDialog.getSaveFileName(self, caption=title, directory=start_dir, filter=extensions)
        return files[0]

    def read_file(self, file_path: str = None) -> str:
        text: str = None
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r') as file:
            text = file.read()
        return text
    



    def get_directory(self, start=DEFAULT_LOG_FOLDER):
        dir = str(QFileDialog.getExistingDirectory(self, directory=start)) + "/"
        return dir

    def print_help(self):
        open_help_popup(self)
        return

    def get_combobox_items(self, combobox: QtWidgets.QComboBox) -> list:
        return [combobox.itemText(i) for i in range(combobox.count())]

    def set_combobox_items(self, combobox: QtWidgets.QComboBox, items: list) -> None:
        items_str = [str(x) for x in items]
        combobox.clear()
        combobox.addItems(items_str)

    def about_to_quit(self):
        self.rescan_worker.stop()
        self.rescan_thread.quit()
        eprint("------EXITING------", color='red')

    def make_quit(self):
        self.app.quit()


if __name__ == "__main__":
    from serial_killer import execute
    execute()
