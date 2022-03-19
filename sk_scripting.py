from PyQt5.QtCore import QObject, pyqtSignal
import time 

from sk_tools import *

class ScriptWorker(QObject):
    line = pyqtSignal(list)
    finished = pyqtSignal(bool)

    def __init__(self, text:str, delay:int = 500, arg_str:str = "") -> None:
        super().__init__()
        self.arg_str = arg_str
        self.delay = delay
        self.lines:list = text.splitlines(False)
        self.active = False
        self.line_total = len(self.lines)
        self.current_line_number = 0
        self.loop_counter = 0
        self.loop_start_line = None
        self.loop_total = 0 
    
    def send(self, text:str = None, type = TYPE_TX):
        self.line.emit([text, type])
        if type == TYPE_TX:
            time.sleep(self.delay / 1000)
        
    def start_loop(self, loop_str:str):
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
            dprint(f"LOOP NUMBER {loop_str[1:]} INVALID", color= 'red')
            self.loop_counter = 0
            self.loop_total = 0
            return
        if l_number < 0:
            self.loop_counter = l_number
            self.loop_total = 0
            return
        else:
            self.loop_total = l_number
        
    def end_loop(self):
        if self.loop_start_line == None:
            return 
        if self.loop_total != None:
            if self.loop_counter == self.loop_total - 1:
                return
        self.current_line_number = self.loop_start_line
        self.loop_counter += 1
        pass 

    def handle_command(self, text:str = None):
        if not text:
            return None
        cmds = text.split("#")

        for cmd in cmds:
            if not cmd:
                continue
            cmd = cmd.strip()

            if cmd.startswith("delay="):
                #print("setting delay to:", cmd[6:])
                self.delay = get_number(cmd[6:], int, self.delay)
            
            if cmd.startswith("info="):
                self.send(cmd[5:] + "\n", TYPE_INFO)

            elif cmd.startswith("error="):
                self.send(cmd[6:]+ "\n", TYPE_ERROR)

            elif cmd.startswith("pause="):
                time.sleep(get_number(cmd[6:]) / 1000)

            elif cmd.startswith("loop"):
                self.start_loop(cmd)
            
            elif cmd.startswith("endloop"):
                self.end_loop()

            elif cmd.startswith("end"):
                self.finished.emit(True)
                time.sleep(.01)

            else:
                self.send(cmd, TYPE_CMD)

    def evaluate(self, line:str):
        if "//" in line: # Comment 
            line = line.split("//")[0]
            if not line.replace(" ", ""):
                return 
        line = line.replace("$LOOP", str(abs(self.loop_counter)))

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
        self.active = False
        print("SCRIPT DONE")



