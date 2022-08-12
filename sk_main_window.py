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

import re 
import random
import math



class MainWindow(QtWidgets.QMainWindow):
    target_port: str = None  # Port to auto-connect to.
    current_ports: dict = {}  # List of current ports
    command_char: str = None
    script_worker = None
    cmd_history = [""]
    commands = {}
    history_index = 1
    target_port: str = None
    key_cmds: dict = {}
    script_thread = QThread()
    plot_started = False
    is_connected = False
    data_format = 'utf-8'

    def __init__(self, parent: QtWidgets.QApplication, open_cmd="", * args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.last_save_time = time.perf_counter()
        self.cmd_list = []
        self.current_settings = {}
        self.ui = Ui_MainWindow()

        self.app: QtWidgets.QApplication = parent

        self.ui.setupUi(self)
        self.connect_ui()
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
            vprint("Has Open Command:", open_cmd)
            self.ui.lineEdit_input.setText(open_cmd)
            self.send_clicked()

        self.ui.pushButton_restart_logger.setEnabled(False)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        modifier = event.modifiers()

        #print(key, modifier)
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
        self.ui.lineEdit_keyboard_control.textChanged.connect(self.keyboard_control)
        self.ui.pushButton_run_script.clicked.connect(self.start_script)
        self.ui.pushButton_start_plot.clicked.connect(self.start_plot_clicked)
        self.ui.pushButton_start_plot.setStyleSheet(STYLE_SHEET_BUTTON_INACTIVE)
        #self.ui.groupBox_adv_plot.toggled.connect(lambda: self.collapse_box(self.ui.groupBox_adv_plot))
        #self.collapse_box(self.ui.groupBox_adv_plot, True)

    # def collapse_box(self, groupBox: QGroupBox, force_close=False):
    #     children = groupBox.findChildren((QLineEdit, QLabel, QComboBox, QCheckBox, QPushButton))
    #     if force_close == True:
    #         groupBox.setChecked(False)
    #         return
    #     if groupBox.isChecked():  # Expand
    #         groupBox.setTitle(groupBox.title().replace(ARROW_RIGHT, ARROW_DOWN))
    #         groupBox.setContentsMargins(1, 15, 1, 1)
    #         vprint("EXPAND Box:", groupBox.objectName())
    #         for item in children:
    #             item: QWidget
    #             item.show()
        # else:
        #     vprint("Collapsing Box:", groupBox.objectName())
        #     groupBox.setTitle(groupBox.title().replace(ARROW_DOWN, ARROW_RIGHT))
        #     groupBox.setContentsMargins(0, 0, 0, 0)
        #     for item in children:
        #         item: QWidget
        #         item.hide()

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

        if type == TYPE_RX:  # Incoming FROM device
            self.ui.textEdit_terminal.setTextColor(COLOR_WHITE)
            self.ui.textEdit_terminal.insertPlainText(text)
            self.log.write(text)
            if self.plot_started:
                self.ui.widget_plot.update(text)
            vprint(text, color="white", end="", flush=True)

        elif type == TYPE_TX:  # Outgoing TO DEVICE
            text = self.ui.lineEdit_tx_chr.text() + text
            if self.ui.checkBox_output_include_terminal.isChecked():
                self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_BLUE)
                self.ui.textEdit_terminal.insertPlainText(text)
            if self.ui.checkBox_output_include_log.isChecked():
                self.log.write(text)
            vprint(text, color="blue", end="", flush=True)

        elif type == TYPE_INFO:
            if self.ui.checkBox_info_include_terminal.isChecked():
                text = self.ui.lineEdit_info_chr.text() + text
                self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_GREEN)
                self.ui.textEdit_terminal.insertPlainText(text)
            if self.ui.checkBox_info_include_log.isChecked():
                self.log.write(text)
            vprint(text, color="green", end="", flush=True)

        elif type == TYPE_ERROR:
            if self.ui.checkBox_error_include_terminal.isChecked():
                text = self.ui.lineEdit_err_chr.text() + text
                self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_RED)
                self.ui.textEdit_terminal.insertPlainText(text)
            if self.ui.checkBox_error_include_log.isChecked():
                self.log.write(text)
            vprint(text, color="red", end="", flush=True)

        elif type == TYPE_HELP:
            self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_YELLOW)
            self.ui.textEdit_terminal.insertPlainText(text)
            vprint(text, color="yellow", end="", flush=True)

        if self.ui.checkBox_autoscroll.isChecked():
            self.ui.textEdit_terminal.moveCursor(QTextCursor.End)
            self.ui.textEdit_terminal.ensureCursorVisible()

    def debug_text(self, *args, color: QColor = COLOR_BLACK):
        label_text = ""
        for arg in args:
            label_text += str(arg)
        self.ui.label_debug.setStyleSheet(f"color:{colorToStyleSheet(color)}")
        self.ui.label_debug.setText(label_text)
        vprint(label_text, color='cyan')

    def input_text_evaluate(self, text:str)-> str:
        text = text.replace("$UTS", str(int(time.time())))
        found_expressions = re.findall(r'\$\{(.*?)\}', text)
        for expression in found_expressions:
            try: 
                if not expression:
                    text = text.replace("${}", "")
                    continue
                expression_resp = str(eval(expression))
                text = text.replace(f"${{{expression}}}", expression_resp, 1)
                vprint(f"EXPRESSION ${{{expression}}} = {expression_resp}", color = "green")
            except Exception as E:
                eprint(E)
                self.add_text(f"ERR IN EXPRESSION: ${{{expression}}} {str(E)}\n", type=TYPE_ERROR)
                return None 
        return text 

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
        #print(text)

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
            self.disconnect(False)
            vprint("SERIAL PORT LOST", color="red")

    def disconnect(self, intentional=True):
        if self.is_connected == False:
            if intentional:
                self.debug_text("ALREADY DISCONNECTED", color=COLOR_DARK_YELLOW)
            return

        if intentional:
            self.target_port = None
            self.ui.label_port.setText("Ports:")
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

    def connect(self, port: str, baud: str = "115200", xonxoff: bool = False, dsrdtr: bool = False, rtscts: str = False, parity: str = "NONE") -> bool:
        self.ui.comboBox_port.setCurrentText(port)
        if port in self.current_ports:
            device = self.current_ports[port]["dev"]

        self.is_connected = serial_connect(device, baud, xonxoff, rtscts, dsrdtr, parity)
        if not self.is_connected:
            self.debug_text(f"ERR: {port} COULD NOT CONNECT", color=COLOR_RED)
            self.add_text(f"ERR: {port} COULD NOT CONNECT \n", type=TYPE_ERROR)
            return

        self.log.set_port(port)

        self.debug_text(f"CONNECTED TO {port} at {ser.baudrate} BAUD", color=COLOR_GREEN)
        self.add_text(f"CONNECTED TO {port} at {ser.baudrate} BAUD\n", type=TYPE_INFO)

        if self.ui.checkBox_auto_reconnect.isChecked():
            self.target_port = port
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
        else:
            port = self.ui.comboBox_port.currentText()

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

    def auto_reconnect_toggled(self):
        if self.ui.checkBox_auto_reconnect.isChecked():
            if self.is_connected:
                self.target_port = ser.port
                self.ui.label_port.setText(f"Ports: (Auto {self.target_port})")
        else:
            self.ui.label_port.setText(f"Ports:")
            self.target_port = None

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
        if not ports_found and not ports_lost:
            return
        self.current_ports = ports
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
        if current_selection in self.current_ports:
            self.ui.comboBox_port.setCurrentText(current_selection)

        if self.target_port and self.is_connected == False:
            if self.target_port in self.current_ports and self.ui.checkBox_auto_reconnect.isChecked():
                self.handle_connect(self.target_port)

    def show_ports(self, *args, **kwargs):
        self.debug_text(f"PORTS: {' '.join(self.current_ports)}", color=COLOR_BLACK)
        
        if not self.current_ports:
            self.add_text("NO PORTS FOUND", type=TYPE_HELP)
            return 
        p_str = "-----PORTS-----\n #  NAME\n"
        for index, port in enumerate(self.current_ports):
            this_port = self.current_ports[port]
            p_str += f'''({index}) {port}\t{this_port["descr"]}\n'''
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
                                self.ui.checkBox_error_include_log,
                                self.ui.checkBox_error_include_terminal,
                                self.ui.checkBox_info_include_log,
                                self.ui.checkBox_info_include_terminal,
                                self.ui.checkBox_autoscroll,
                                self.ui.checkBox_timestamp,
                                self.ui.checkBox_allow_commands
                                ]

        self.save_line_edits = [self.ui.lineEdit_err_chr,
                                self.ui.lineEdit_info_chr,
                                self.ui.lineEdit_max_points,
                                self.ui.lineEdit_append_to_send,
                                self.ui.lineEdit_tx_chr,
                                self.ui.lineEdit_log_format,
                                self.ui.lineEdit_command_char,
                                self.ui.lineEdit_delay,
                                ]

        self.log_save_line_edits = [self.ui.lineEdit_time_format,
                                    self.ui.lineEdit_log_folder,
                                    self.ui.lineEdit_log_format,
                                    self.ui.lineEdit_log_name]

        self.save_combo_boxes = [self.ui.comboBox_baud,
                                 self.ui.comboBox_plot_type,
                                 self.ui.comboBox_limits,
                                 ]

        for checkbox in self.save_checkboxes:
            checkbox.stateChanged.connect(self.save_settings)

        for lineEdit in self.save_line_edits:
            lineEdit.textChanged.connect(self.save_settings)

        for comboBox in self.save_combo_boxes:
            comboBox.currentTextChanged.connect(self.save_settings)

    def save_item(self, object):
        if isinstance(object, QtWidgets.QComboBox):
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
        with open(SETTINGS_FILE, 'w') as file:
            json.dump(self.current_settings, file)

    def save_settings(self):
        '''Save Settings After One Second'''  # This is so multiple saves arent attempted for multiple edits
        if (time.perf_counter() - self.last_save_time < 1.00):
            return

        self.save_timer.singleShot(1000, self._save_settings)
        self.last_save_time = time.perf_counter()

    def _save_settings(self):
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
        with open(SETTINGS_FILE, 'w') as file:
            json.dump(self.current_settings, file)

    def recall_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            vprint("FIRST PROGRAM LOAD", color='yellow')
            with open(SETTINGS_FILE, 'w') as file:
                pass
            self._save_settings()
            return
        try:
            with open(SETTINGS_FILE, 'r') as file:
                self.current_settings = json.load(file)

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


########################################################################
#
#               COMMAND FUNCTIONS
#
########################################################################


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
        self.cmd_list.append(cmd_con)

        self.cmd_list.append(Command("dcon", self.disconnect, 0))

        cmd_script = Command("script", self.handle_script_command, 0)
        cmd_script.add_option(("-h", "--help"))
        cmd_script.add_option(("-o", "--open"))
        cmd_script.add_option(("-t", "--tab"))
        cmd_script.add_option(("-n", "--new"))
        cmd_script.add_option(("-ls", "--list"))
        cmd_script.add_option(("-rm", "--remove"))
        cmd_script.add_option(("-s", "--save"))
        cmd_script.add_option(("-r", "--run"))

        self.cmd_list.append(cmd_script)

        cmd_plot = Command("plot", self.handle_plot_command, 1)
        cmd_plot.add_option(("-h", "--help"))
        cmd_plot.add_option(("-p", "--points"))
        cmd_plot.add_option(("-k", "--keys"))
        cmd_plot.add_option(("-l", "--limits"))
        cmd_plot.add_option(("-r", "--ref"))
        cmd_plot.add_option(("-s", "--seps"))
        cmd_plot.add_option(("-t", "--test"))

        self.cmd_list.append(cmd_plot)

        cmd_keys = Command("key", self.handle_key_cmd, 3)
        cmd_keys.add_option(("-h", "--help"))

        self.cmd_list.append(cmd_keys)

        cmd_log = Command("log", self.handle_log_command, 0)
        cmd_log.add_option(("-h", "--help"))
        cmd_log.add_option(("-o", "--open"))
        cmd_log.add_option(("-a", "--archive"))
        cmd_log.add_option(("-ls", "--list"))
        cmd_log.add_option(("--name"))
        cmd_log.add_option(("--tfmt"))
        cmd_log.add_option(("--fmt"))
        self.cmd_list.append(cmd_log)

        cmd_cow = Command("cowsay", self.cowsay)
        cmd_cow.add_option(("-n", "--nerd"))
        cmd_cow.add_option(("-d"))
        cmd_cow.add_option(("-l"))
        self.cmd_list.append(cmd_cow)

        self.cmd_list.append(Command("new", self.open_new_window))

        cmd_format = Command("format", self.set_format, 1)
        self.cmd_list.append(cmd_format)

    def set_format(self, format:str):
        if format in ['utf-8', 'hex', 'bin', 'dec']:
            self.data_format = format
            if self.is_connected:
                self.serial_worker.format = self.data_format
        else:
            print("INVALID")

        print(format)
        

    def interpret_command(self, text: str):
        """execute a command. Returns NONE if no command found"""
        text = text.replace("\n", "").replace("\r", "")
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
            self.add_text(SCRIPT_HELP, type=TYPE_HELP)
            return
        if '-f' in kwargs:
            self.open_folder_location(SCRIPT_FOLDER)
            return
        if "-a" in kwargs:
            arg_str = kwargs['-a']
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
                if not log_file.endswith(".txt"):
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
        if '--name' in kwargs:
            self.ui.lineEdit_log_name.setText(kwargs['--name'])
        if '--tfmt' in kwargs:
            self.ui.lineEdit_time_format.setText(kwargs['--tfmt'])
        if '--fmt' in kwargs:
            self.ui.lineEdit_log_format.setText(kwargs['--fmt'])

    def set_log_folder(self, log_folder: str = None):
        if not log_folder:
            log_folder = self.get_directory(DEFAULT_LOG_FOLDER)
        self.ui.lineEdit_log_folder.setText(log_folder)

    def log_settings_changed(self):
        self.ui.pushButton_restart_logger.setEnabled(True)
        self.ui.pushButton_restart_logger.setStyleSheet(STYLE_SHEET_BUTTON_ACTIVE)
        pass

    def start_logger(self):
        folder_path = self.ui.lineEdit_log_folder.text()
        file_extension = self.ui.comboBox_log_name_extension.currentText()
        file_name = time.strftime(self.ui.lineEdit_log_name.text())
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
            log_file = self.get_latest_file(DEFAULT_LOG_FOLDER)
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
            if limits.upper() == "MAX":
                self.ui.comboBox_limits.setCurrentText("Max")
            elif limits.upper() == "WINDOW":
                self.ui.comboBox_limits.setCurrentText("Window")

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

        limits = self.ui.comboBox_limits.currentText()
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

    def keyboard_control(self):
        key = self.ui.lineEdit_keyboard_control.text()
        if not key:
            return
        self.ui.lineEdit_keyboard_control.clear()
        key_cmds = self.get_key_cmds()
        vprint(key, color='green', end='\t')
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
        files = QFileDialog.getSaveFileName(self, directory=start_dir, filter=extensions)
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
