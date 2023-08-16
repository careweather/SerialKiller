from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QTextCharFormat, QTextCursor, QSyntaxHighlighter
from PyQt5.QtWidgets import QTextEdit
import time

from sk_tools import *


class ScriptSyntaxHighlighter(QSyntaxHighlighter):
    cmd_format = QTextCharFormat()
    cmd_format.setForeground(COLOR_LIGHT_GREEN)

    comment_format = QTextCharFormat()
    comment_format.setForeground(COLOR_MED_DARK_GREY)

    var_format = QTextCharFormat()
    var_format.setForeground(COLOR_LIGHT_BLUE)

    def __init__(self, parent: QTextEdit = None):
        super().__init__(parent)

    def highlightBlock(self, input: str) -> None:
        text = input.split("//")[0]
        command_sections = []
        block_start = None

        if text.strip().startswith("#"):
            command_sections.append([0, len(text)])
        for section in command_sections:
            self.setFormat(section[0], section[1] - section[0] + 1, self.cmd_format)

        comment_sections = []
        if '//' in input:
            block_start = input.index("//")
            if '\n' in input:
                comment_sections.append([block_start, input.index('\n')])
            else:
                comment_sections.append([block_start, len(input)])
        for section in comment_sections:
            self.setFormat(section[0], section[1] - section[0] + 1, self.comment_format)
        
        var_sections = []
        if '$ARG' in input:
            block_start = input.index("$ARG")
            var_sections.append([block_start, block_start + 4])
        if '$LOOP' in input:
            block_start = input.index("$LOOP")
            var_sections.append([block_start, block_start + 5])
        if '${' in input and '}' in input:
            block_start = input.index("${")
            block_stop = input.index("}")
            if block_start < block_stop:
                var_sections.append([block_start, block_stop])
        for section in var_sections:
            self.setFormat(section[0], section[1] - section[0] + 1, self.var_format)
            


class ScriptWorker(QObject):
    line = pyqtSignal(list)
    finished = pyqtSignal(bool)

    def __init__(self, text: str, delay: int = DEFAULT_SCRIPT_DELAY, arg_str: str = "") -> None:
        super().__init__()
        self.on_exit_str = ""
        self.arg_str = arg_str
        self.delay = delay
        vprint("SCRIPT DELAY:", self.delay, " SCRIPT COMMAND: ", self.arg_str)
        self.lines: list = text.splitlines(False)
        self.active = False
        self.line_total = len(self.lines)
        self.current_line_number = 0
        self.loop_counter = 0
        self.loop_start_line = None
        self.loop_total = 0

    def send(self, text: str = None, type=TYPE_TX):
        self.line.emit([text, type])
        if type == TYPE_TX:
            time.sleep(self.delay / 1000)

    def start_loop(self, loop_str: str):
        loop_str = loop_str.replace("loop", "")
        self.loop_start_line = self.current_line_number
        if not loop_str:
            self.loop_total = None
            return
        elif not loop_str.startswith("="):
            return
        l_number = get_number(loop_str[1:], int)
        if l_number == None:
            self.loop_start_line = None
            eprint(f"LOOP NUMBER {loop_str[1:]} INVALID")
            self.loop_counter = 0
            self.loop_total = 0
            return
        if l_number < 0:
            self.loop_counter = l_number
            self.loop_total = 0
            return
        else:
            self.loop_total = l_number
            self.loop_counter = 0

    def end_loop(self):
        if self.loop_start_line == None:
            return
        if self.loop_total != None:
            if self.loop_counter == self.loop_total - 1:
                return
        self.current_line_number = self.loop_start_line
        self.loop_counter += 1
        pass

    def handle_command(self, text: str = None):
        if not text:
            return None

        cmds = text.split("#")

        for cmd in cmds:
            if not cmd:
                continue
            cmd = cmd.strip()

            if cmd.startswith("exit="):
                self.on_exit_str = cmd[5:]

            elif cmd.startswith("delay="):
                self.delay = get_number(cmd[6:], int, self.delay)

            elif cmd.startswith("info="):
                self.send(cmd[5:] + "\n", TYPE_INFO)

            elif cmd.startswith("error="):
                self.send(cmd[6:] + "\n", TYPE_ERROR)

            elif cmd.startswith("pause="):
                time.sleep(get_number(cmd[6:]) / 1000)
            
            elif cmd.startswith("arg="):
                if self.arg_str == "":
                    self.arg_str = cmd[4:]

            elif cmd.startswith("loop"):
                self.start_loop(cmd)

            elif cmd.startswith("endloop"):
                self.end_loop()

            elif cmd.startswith("end"):
                self.finished.emit(True)
                time.sleep(.01)

            else:
                self.send(cmd, TYPE_CMD)

    def evaluate(self, line: str):
        if "//" in line:  # Comment
            line = line.split("//")[0]
            if not line.replace(" ", ""):
                return
        line = line.replace("$LOOP", str(abs(self.loop_counter))).replace("$ARG", self.arg_str)

        if line.strip().startswith("#"):
            return self.handle_command(line)

        self.send(line)
        return

    def run(self):
        self.active = True
        while self.active and self.current_line_number != self.line_total:
            self.evaluate(self.lines[self.current_line_number])
            self.current_line_number += 1
        self.finished.emit(True)

    def stop(self):
        if self.on_exit_str:
            self.handle_command(self.on_exit_str)
        self.active = False
        vprint("SCRIPT DONE")
