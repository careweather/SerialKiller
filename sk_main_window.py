import glob
import json
import os
import time
from datetime import datetime
import re

import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtGui import QTextCharFormat, QTextCursor, QSyntaxHighlighter
# library imports
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QTextEdit

# gui imports
from gui.GUI_MAIN_WINDOW import Ui_MainWindow
from serial_handler import *
from sk_commands import Command
from sk_help import *
from sk_help_popup import Help_Popup, open_help_popup
from sk_log_popup import Log_Viewer, open_log_viewer
from sk_logging import Logger
from sk_scripting import ScriptWorker, ScriptSyntaxHighlighter
from sk_tools import *




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

    def __init__(self, * args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.last_save_time = time.perf_counter()
        self.cmd_list = []
        self.ui = Ui_MainWindow()
        self.current_settings = {}
        self.ui.setupUi(self)
        self.connect_ui()
        self.save_timer = QTimer()
        self.log = Logger(log_fmt=self.ui.lineEdit_log_format.text())
        self.create_settings()
        self.create_commands()
        self.update_ports()
        self.start_rescan()
        self.recall_settings()

        self.script_highlighter = ScriptSyntaxHighlighter(self.ui.textEdit_script)

        self.log.start()
        self.ui.lineEdit_input.setFocus()
        self.ui.tabWidget.setCurrentIndex(0)

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

        self.ui.textEdit_terminal.setPlaceholderText(HELP_TEXT)
        self.ui.textEdit_terminal.setStyleSheet(STYLE_SHEET_TERMINAL_INACTIVE)
        self.ui.pushButton_connect.setStyleSheet(STYLE_SHEET_BUTTON_INACTIVE)
        self.ui.pushButton_send.clicked.connect(self.send_clicked)
        self.ui.pushButton_clear.clicked.connect(self.clear_clicked)
        self.ui.pushButton_connect.clicked.connect(self.connect_clicked)
        self.ui.pushButton_pause_plot.clicked.connect(self.pause_plot)

        self.ui.comboBox_baud.clear()
        bauds = [str(x) for x in baud_rates]
        self.ui.comboBox_baud.addItems(bauds)
        self.ui.comboBox_baud.setCurrentText("115200")
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
        if self.script_worker != None:
            return
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

        elif type == TYPE_TX:  # Outgoing TO DEVICE
            text = self.ui.lineEdit_tx_chr.text() + text
            if self.ui.checkBox_output_include_terminal.isChecked():

                self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_BLUE)
                self.ui.textEdit_terminal.insertPlainText(text)
            if self.ui.checkBox_output_include_log.isChecked():
                self.log.write(text)

        elif type == TYPE_INFO:
            if self.ui.checkBox_info_include_terminal.isChecked():
                text = self.ui.lineEdit_info_chr.text() + text
                self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_GREEN)
                self.ui.textEdit_terminal.insertPlainText(text)
            if self.ui.checkBox_info_include_log.isChecked():
                self.log.write(text)

        elif type == TYPE_ERROR:
            if self.ui.checkBox_error_include_terminal.isChecked():
                text = self.ui.lineEdit_err_chr.text() + text
                self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_RED)
                self.ui.textEdit_terminal.insertPlainText(text)
            if self.ui.checkBox_error_include_log.isChecked():
                self.log.write(text)

        elif type == TYPE_HELP:
            self.ui.textEdit_terminal.setTextColor(COLOR_LIGHT_YELLOW)
            self.ui.textEdit_terminal.insertPlainText(text)

        if self.ui.checkBox_autoscroll.isChecked():
            self.ui.textEdit_terminal.moveCursor(QTextCursor.End)
            self.ui.textEdit_terminal.ensureCursorVisible()

    def debug_text(self, *args, color: QColor = COLOR_BLACK):
        label_text = ""
        for arg in args:
            label_text += str(arg).replace("\n", "")
        self.ui.label_debug.setStyleSheet(f"color:{colorToStyleSheet(color)}")
        self.ui.label_debug.setText(label_text)

    def send_clicked(self, text: str = None):
        if not text:
            ui_text = self.ui.lineEdit_input.text()
            text = ui_text + \
                replace_escapes(self.ui.lineEdit_append_to_send.text())
            if not self.script_worker:
                self.ui.lineEdit_input.clear()

        text = text.replace("$UTS", str(int(time.time())))

        self.append_to_history(text)

        if self.ui.checkBox_interpret_escape.isChecked():
            text = replace_escapes(text)

        cmd_result = self.interpret_command(ui_text)
        if cmd_result != None:

            if cmd_result == True:
                return
            if cmd_result.startswith("ERR:"):
                self.debug_text(str(cmd_result), color=COLOR_RED)
                self.add_text(str(cmd_result) + '\n', type=TYPE_ERROR)
            else:
                self.add_text(str(cmd_result) + '\n', type=TYPE_INFO)
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
            self.add_text(f"LOST {ser.port}", type=TYPE_ERROR)
            self.disconnect(False)

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
        if port not in self.current_ports:
            self.debug_text(f"ERR: PORT {port} NOT FOUND", color=COLOR_RED)
            return
        self.ui.comboBox_port.setCurrentText(port)
        self.is_connected = serial_connect(port, baud, xonxoff, rtscts, dsrdtr, parity)
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
        self.serial_worker.moveToThread(self.serial_thread)
        self.serial_thread.started.connect(self.serial_worker.run)
        self.serial_worker.out.connect(self.add_text)
        self.serial_worker.disconnected.connect(self.serial_error)
        self.serial_thread.setTerminationEnabled(True)
        self.serial_thread.start()
        return True

    def handle_connect(self, **kwargs):
        port: str = None
        baud: str = None
        xonxoff: bool = None
        dsrdtr: bool = None
        rtscts: bool = None
        parity: str = None

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

        if 'port' in kwargs:
            port = kwargs['port']
            if port == '-h':
                self.add_text(CONNECT_HELP, type=TYPE_HELP)
                return
            elif port == '?':
                self.ui.comboBox_port.showPopup()
                self.ui.comboBox_port.setFocus()
                return False
            elif port not in self.current_ports:
                if port.upper() in self.current_ports:
                    port = port.upper()
                elif port.isdigit():
                    if "COM" + port in self.current_ports:
                        port = "COM" + port
        else:
            port = self.ui.comboBox_port.currentText()

        if self.is_connected:
            if port in self.current_ports:
                self.disconnect()
                self.handle_connect(**kwargs)
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
            p_str = "LOST: " + str(ports_lost)
            p_str = p_str.replace("{", '').replace("}", '').replace("'", '')
            self.debug_text(p_str, color=COLOR_RED)
        elif ports_found:
            p_str = "FOUND: " + str(ports_found)
            p_str = p_str.replace("{", '').replace("}", '').replace("'", '')
            self.debug_text(p_str, color=COLOR_GREEN)

        current_selection = self.ui.comboBox_port.currentText()
        self.ui.comboBox_port.clear()
        self.ui.comboBox_port.addItems(self.current_ports)
        if current_selection in self.current_ports:
            self.ui.comboBox_port.setCurrentText(current_selection)

        if self.target_port and self.is_connected == False:
            if self.target_port in self.current_ports and self.ui.checkBox_auto_reconnect.isChecked():
                args = {'port': self.target_port}
                self.handle_connect(**args)

    def show_ports(self, **kwargs):
        p_str = "PORTS: "
        for p in self.current_ports:
            p_str += f"{p} "
        self.debug_text(p_str, color=COLOR_BLACK)
        p_str = "-----PORTS-----\n"
        if not self.current_ports:
            p_str += "NONE"
        elif '-a' not in kwargs:
            p_str += " #  NAME\t\tDESCRIPTION\n"
        
            

        for index, port in enumerate(self.current_ports):
            this_port = self.current_ports[port]
            if '-a' in kwargs:
                p_str += f'''({index}) {this_port["name"]}'''
                for item in this_port:
                    p_str += f"\t{item}:\t{str(this_port[item])}\n"
            else:
                p_str += f'''({index}) {this_port["name"]}\t\t{this_port["descr"]}\n'''
        
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
                                self.ui.lineEdit_delay]

        self.save_combo_boxes = [self.ui.comboBox_baud,
                                 self.ui.comboBox_plot_type]

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
        if (time.perf_counter() - self.last_save_time < 1):
            return

        self.save_timer.singleShot(1000, self._save_settings)
        self.last_save_time = time.perf_counter()

    def _save_settings(self):
        dprint("SAVED SETTINGS", color='green')
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
            dprint("FIRST PROGRAM LOAD", color='yellow')
            with open(SETTINGS_FILE, 'w') as file:
                pass
            self._save_settings()
            return
        try:
            with open(SETTINGS_FILE, 'r') as file:
                self.current_settings = json.load(file)
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
                print("LAST SCRIPT NAME", last_script_name)
                if last_script_name:
                    self.open_script(last_script_name)
                else:
                    self.ui.lineEdit_script_name.clear()

            self.command_char = self.ui.lineEdit_command_char.text()

        except Exception as E:
            dprint(f"\nERROR IN RECALLING SETTINGS: {E}", color='red')


########################################################################
#
#               COMMAND FUNCTIONS
#
########################################################################

    def create_commands(self):
        self.cmd_list.append(Command("help", self.print_help))

        cmd_ports = Command("ports", self.show_ports)
        cmd_ports.add_argument("-a", '')
        self.cmd_list.append(cmd_ports)

        cmd_clear = Command("clear", self.clear_clicked)
        self.cmd_list.append(cmd_clear)
        self.cmd_list.append(Command("quit", quit))
        self.cmd_list.append(Command("exit", quit))
        cmd_con = Command("con", self.handle_connect, "port", str)
        cmd_con.add_argument('-b', '', str, 115200)
        cmd_con.add_argument('-d', '', bool, True)
        cmd_con.add_argument('-x', '', bool, True)
        cmd_con.add_argument('-r', '', bool, True)
        cmd_con.add_argument('-p', '', str)
        cmd_con.add_argument('-h', '', bool, True)
        self.cmd_list.append(cmd_con)

        self.cmd_list.append(Command("dcon", self.disconnect))

        cmd_script = Command("script", self.handle_script_command)
        cmd_script.add_argument("-h", '')
        cmd_script.add_argument("-o", '', str)
        cmd_script.add_argument("-t", '')
        cmd_script.add_argument("-n", '', str, "")
        cmd_script.add_argument("-rm", '', str)
        cmd_script.add_argument("-s", '', str)
        cmd_script.add_argument("-r", '', str)
        cmd_script.add_argument("-d", '', int)
        cmd_script.add_argument("-a", '', str, "")
        cmd_script.add_argument("-ls")
        self.cmd_list.append(cmd_script)

        cmd_log = Command("log", self.handle_log_command)
        cmd_log.add_argument('-o', '', default="")
        cmd_log.add_argument('-a', '')
        cmd_log.add_argument('-rm', '')
        cmd_log.add_argument('-ls', '')
        cmd_log.add_argument('-h', "")
        self.cmd_list.append(cmd_log)

        cmd_plot = Command("plot", self.handle_plot_command)
        cmd_plot.add_argument("-kv", '')
        cmd_plot.add_argument("-c", "")
        cmd_plot.add_argument("-t", "")
        cmd_plot.add_argument("-l", "")
        cmd_plot.add_argument("-h", "")
        cmd_plot.add_argument("-m")
        cmd_plot.add_argument("-p")
        self.cmd_list.append(cmd_plot)

        cmd_keys = Command("key", self.handle_key_cmd)
        cmd_keys.add_argument("-k", "")
        cmd_keys.add_argument("-v", "")
        cmd_keys.add_argument("-c", "")
        cmd_keys.add_argument("-h", "")
        self.cmd_list.append(cmd_keys)

        self.cmd_list.append(Command("new", self.open_new_window))

    def interpret_command(self, text: str):
        """return none if no command found"""
        text = text.replace("\n", "").replace("\r", "")
        if not text:
            return None
        if not self.ui.checkBox_allow_commands.isChecked():
            return None
        if self.command_char:
            if text[0] != self.command_char:
                return None
            text = text[1:]
            dprint(f"POSSIBLE CMD: <{text}>", color='yellow')

        for cmd in self.cmd_list:
            cmd: Command
            result = cmd.execute(text)
            if result is None:
                continue
            else:
                return result

        return None

########################################################################
#
#               SCRIPT FUNCTIONS
#
########################################################################

    def handle_script_command(self, **kwargs):
        delay = None
        arg_str = ""
        run_script = True
        run_script_name = None
        if '-h' in kwargs:
            self.add_text(SCRIPT_HELP, type=TYPE_HELP)
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
            self.open_script(kwargs['-o'])
            run_script = False

        if '-s' in kwargs:
            self.save_script(kwargs['-s'])
            return

        if '-r' in kwargs:
            run_script = True
            if kwargs['-r']:
                run_script_name = kwargs['-r']

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
            return
        if file_path == None:
            self.debug_text(f"ERR: file '{file_name}'.txt not found", color=COLOR_RED)
            return
        dprint(f"OPENING SCRIPT {file_name}", color='blue')
        with open(file_path, 'r') as file:
            self.ui.textEdit_script.setPlainText(file.read())
        self.ui.lineEdit_script_name.setText(file_path.split('/')[-1].replace('.txt', ''))
        self.ui.tabWidget.setCurrentIndex(1)
        self.ui.textEdit_script.setFocus()

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
        return

    def script_line(self, line: list):
        if line[1] == TYPE_TX:
            self.ui.lineEdit_input.setText(line[0])
            self.send_clicked()
        elif line[1] == TYPE_CMD:
            self.interpret_command(line[0])
        else:
            self.add_text(line[0], type=line[1])
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
        self.ui.pushButton_send.setDisabled(True)
        self.ui.tabWidget.setCurrentIndex(0)

        self.script_thread = QThread()
        self.script_worker = ScriptWorker(text, delay, arg_str)
        self.script_worker.moveToThread(self.script_thread)
        self.script_thread.started.connect(self.script_worker.run)
        self.script_worker.line.connect(self.script_line)
        self.script_worker.finished.connect(self.end_script)
        self.script_thread.start()

        dprint("RUNNING SCRIPT: ", text, color='yellow')

    def end_script(self):
        if self.script_worker is None:
            return

        self.ui.lineEdit_input.clear()
        self.ui.lineEdit_input.setDisabled(False)
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
        if '-h' in kwargs:
            self.add_text(LOG_HELP, type=TYPE_HELP)
            return

        if '-o' in kwargs:
            if kwargs['-o']:
                log_file = LOG_FOLDER + kwargs["-o"]
                if not log_file.endswith(".txt"):
                    log_file += ".txt"
                if not os.path.exists(log_file):
                    self.add_text(f"Log file {log_file} not found", type=TYPE_ERROR)
                    return
            else:
                log_file = self.get_file(LOG_FOLDER)
            if log_file:
                self.open_log(log_file)
            return

        if '-ls' in kwargs:
            self.list_files(LOG_FOLDER)
            return

        if '-a' in kwargs:
            self.log.archive(kwargs['-a'])
            return

        self.open_log()

    def open_log(self, log_file=None):
        if not log_file:
            log_file = self.get_latest_file(LOG_FOLDER)
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
            self.start_plot("Key-Value")

    def handle_plot_command(self, **kwargs):
        if '-h' in kwargs:
            self.add_text(PLOT_HELP, type=TYPE_HELP)
        plot_type = None
        targets = None
        max_points = None
        limits = "Window"
        if '-m' in kwargs:
            limits = "Max"
        if '-c' in kwargs:
            self.ui.widget_plot.reset()
            return
        if '-t' in kwargs:
            targets = kwargs['-t']
        if '-l' in kwargs:
            max_points = int(kwargs['-l'])
        if '-kv' in kwargs:
            plot_type = "Key-Value"
            self.start_plot(plot_type, targets, max_points, limits)
        if '-p' in kwargs:
            self.pause_plot()
            return

    def start_plot(self, type=None, targets=None, max_points=None, limits=None):
        if not limits:
            limits = self.ui.comboBox_limits.currentText()
        elif limits in ['Max', 'Window']:
            self.ui.comboBox_limits.setCurrentText(limits)

        if self.plot_started:
            self.end_plot()

        if type == None:
            type = self.ui.comboBox_plot_type.currentText()

        if targets:
            self.ui.lineEdit_target_keys.setText(targets)
        elif self.ui.lineEdit_target_keys.text():
            targets = self.ui.lineEdit_target_keys.text()

        if max_points:
            max_points = int(max_points)
            self.ui.lineEdit_max_points.setText(str(max_points))
        elif self.ui.lineEdit_max_points.text():
            max_points = int(self.ui.lineEdit_max_points.text())
        else:
            max_points = 100

        self.plot_started = True
        self.ui.pushButton_start_plot.setText("Stop Plot")
        self.ui.pushButton_start_plot.setStyleSheet(STYLE_SHEET_BUTTON_ACTIVE)
        self.ui.pushButton_pause_plot.setText("Pause Plot")
        self.ui.pushButton_start_plot.setStyleSheet(STYLE_SHEET_BUTTON_ACTIVE)
        self.ui.tabWidget.setCurrentIndex(2)
        self.ui.widget_plot.begin(type, targets, max_points, limits)

    def pause_plot(self):
        if self.ui.widget_plot.paused:
            self.ui.widget_plot.resume()
            self.ui.pushButton_pause_plot.setText("Pause Plot")
        else:
            self.ui.pushButton_pause_plot.setText("Resume Plot")
            self.ui.widget_plot.pause()

    def end_plot(self):
        self.ui.pushButton_start_plot.setText("Start Plot")
        self.ui.pushButton_start_plot.setStyleSheet(
            STYLE_SHEET_BUTTON_INACTIVE)
        self.ui.widget_plot.reset()
        self.plot_started = False

########################################################################
#
#               KEYBOARD FUNCTIONS
#
########################################################################

    def handle_key_cmd(self, **kwargs):
        key = ""
        value = ""
        if "-h" in kwargs:
            self.add_text(KEY_HELP, type=TYPE_HELP)
            return
        if '-c' in kwargs:
            self.clear_key_cmds()
            return
        if '-k' in kwargs:
            key = kwargs['-k']
        if '-v' in kwargs:
            value = kwargs['-v']
        if key or value:
            self.add_key_cmd(key, value)
        else:
            self.ui.lineEdit_keyboard_control.setFocus()

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
        #cprint(key, color='green', end='\t')
        #cprint(key_cmds, color='red')
        if key in key_cmds:
            self.ui.lineEdit_input.setText(key_cmds[key])
            self.send_clicked()
        else:
            self.debug_text(f"KEY {key} not in Keyboard commands", color=COLOR_RED)

########################################################################
#
#               MISC FUNCTIONS
#
########################################################################

    def open_github_repo(self):
        import webbrowser
        self.debug_text("OPENING GITHUB REPO", color=COLOR_GREEN)
        webbrowser.open(GITHUB_URL)

    def open_new_window(self):
        import platform
        import subprocess
        if platform.system() == 'Windows':
            cmd = f'start pythonw.exe {INSTALL_FOLDER}/serial_killer.py'
        elif platform.system() == 'Linux':
            cmd = f'python3 {INSTALL_FOLDER}/serial_killer.py'
        subprocess.call(cmd, shell=True)

    def get_latest_file(self, directory: str):
        list_of_files = glob.glob(directory + "*.txt")
        latest_file = max(list_of_files, key=os.path.getmtime)
        return latest_file

    def list_files(self, directory: str):
        files = os.listdir(directory)
        files_str = ""
        for file in files:
            file_timestamp = os.path.getmtime(directory + file)
            last_t = datetime.fromtimestamp(file_timestamp)
            last_modified = last_t.strftime("%m/%d/%Y %H:%M:%S")
            files_str += str(last_modified) + "\t" + file + "\n"
        self.add_text(files_str, type=TYPE_HELP)

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

    def print_help(self):
        open_help_popup(self)
        return

    def get_combobox_items(self, combobox: QtWidgets.QComboBox) -> list:
        return [combobox.itemText(i) for i in range(combobox.count())]


if __name__ == "__main__":
    from serial_killer import execute
    execute()
