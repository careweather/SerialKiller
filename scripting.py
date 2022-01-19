from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QIntValidator, QTextCursor
from PyQt5 import QtGui, QtWidgets
import time 
import os

class ScriptWorker(QObject):
    line = pyqtSignal(str)
    finished = pyqtSignal(int)
    waiting = pyqtSignal(bool)
    print_line = pyqtSignal(str)

    def __init__(self, text: str, delay = 100):
        super().__init__()
        self.update_delay(delay)
        self.script = []
        self.script = text.splitlines(False)
        self.numbLines = len(self.script)
        self.currentLine = 0
        self._active = True
        self.loopStart = 0
        self.loopNumb = 0
        self.loopActive = False
        self.totalLoops = 0
        self.inp:str = None 
        self.use_python = False

    def save(self, name:str):
        self.send(f"script -s {name}")
        
    def wait_(self, target = None, d_type = str):
        if target is not None:
            print("waiting for target: ", target)
        else: 
            print("waiting....")
        self.waiting.emit(True)
        self.inp = None
        time.sleep(.005)
        if target is not None:
            while target not in str(self.inp) and self._active:
                print("waiting for", target, f"inp({self.inp})", type(self.inp))
                time.sleep(.05)
        else:    
            while self.inp is None and self._active:
                print("waiting...")
                time.sleep(.5)
        print("INPUT TO THREAD:", self.inp)
        return self.inp
        
    def send(self, input = None): 
        time.sleep(self.delay)
        self.line.emit(input)

    def update_delay(self, delay="100"):
        delay = int(delay)
        print("updating delay",delay)
        self.delay = delay/1000
    
    def print(self, *inputs):
        print("PRINTING:", inputs)
        output = ""
        for input in inputs: 
            output += str(input)
        self.print_line.emit(output)
    
    def pause(self, milliseconds:int):
        time.sleep(milliseconds/1000) 

    def read(self, lines:list):
        program = ""
        for line in lines: 
            line = str(line)
            if ">>" in line: 
                line = line.replace(">>", "self.send(\"")
                line += "\")"
            if "send(" in line: 
                line = line.replace("send(", "self.send(")
            if "print(" in line:
                line = line.replace("print", "self.print")
            if "wait(" in line:
                line = line.replace("wait", "self.wait_", 1)
            if "delay(" in line:
                line = line.replace("delay", "self.update_delay")
            if "save(" in line:
                line = line.replace("save", "self.save")
            program += line + '\n'
        print("PROGRAM:", program)
        exec(program)

    def evaluate(self, line_input:str): 
        if line_input:
            if "@L" in line_input: 
                line_input = line_input.replace("@L", str(self.totalLoops - self.loopNumb))
            if "#" in line_input: # Command 
                cmds = line_input.split("#")[1:]
                for cmd in cmds:
                    if "#L" in line_input: 
                        line_input.replace("#L", str(self.loopNumb))
                        self.send(line_input)
                    if cmd.startswith("name="): 
                        self.line.emit(f"script -s {cmd[5:].strip()}")
                    elif cmd.startswith("delay="): 
                        self.delay = int(cmd[6:])/1000
                    elif cmd == "stop": 
                        self.finished.emit(True)
                        self._active = False
                    elif cmd.startswith("info="):
                        self.print(cmd[5:])
                    elif cmd.startswith("loop="): 
                        self.loopNumb = int(cmd[5:])
                        self.totalLoops = self.loopNumb
                        self.loopStart=self.currentLine
                    elif cmd.startswith("pause="):
                        self.pause(int(cmd[6:]))
                    elif cmd.startswith("loop"):
                            self.loopNumb = -1
                            self.loopStart = self.currentLine
                    elif cmd.startswith("endloop"): 
                        if self.loopNumb == -1:
                            self.currentLine = self.loopStart
                        else: 
                            self.loopNumb -= 1
                            if self.loopNumb: 
                                self.currentLine = self.loopStart
                    else:
                        self.line.emit(f"#{cmd}")
            elif line_input.startswith("//"): # Comment 
                print("Comment: ", line_input[2:])
            else: 
                self.send(line_input)
                

    def run(self):
        while self._active:
            if self.use_python: 
                self.read(self.script)
                self.finished.emit(True)
                return
            else:
                while self.currentLine != self.numbLines and self._active: 
                    sline = self.script[self.currentLine]
                    if sline:
                        self.evaluate(sline)
                    self.currentLine += 1
                self.finished.emit(True)
                return
                
    def stop(self):
        print("stopping script")
        self._active = False
        
if __name__ == "__main__": 
    import main
    main.execute()
