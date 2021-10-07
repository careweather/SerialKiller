from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QIntValidator, QTextCursor
from PyQt5 import QtGui, QtWidgets
import time 
import os

class ScriptWorker(QObject):
    line = pyqtSignal(str)
    saveName = pyqtSignal(dict)
    finished = pyqtSignal(int)
    waiting = pyqtSignal(bool)
    _wait = pyqtSignal(bool)
    incoming = pyqtSignal(str)
    printline = pyqtSignal(str)

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
        self.inp:str = None 
        self.use_python = False

    def subScript(self, name):
        name = name + ".txt"
        print("inserting other script", name)
        cwd = os.getcwd()
        script_path = cwd + "\scripts\\" + name
        print('script_dir: ' , str(script_path), type(script_path))
        if os.path.exists(script_path):
            with open(script_path, 'r') as File:
                newlines = File.read().splitlines()
                self.numbLines += len(newlines)
                self.script = self.script[:self.currentLine+1] + newlines + self.script[self.currentLine:]
                print("modified script:",self.script)
        else:
            print("does not exist") 

    def eval(self, line):
        print("evaluating", line)
        
    def input(self, text): 
        self.waiting = False
        print("handled from script:", text)

    def handle_eval(self, text:str):
        print("eval:", text)
        exec(text)

    def handle(self, text:str): 
        print("handling", text)
        #text = text.replace(" ", "")
        if text.startswith("delay="): 
            try: 
                self.delay = int(text[6:])/1000
            except Exception as E: 
                print("ERROR SETTING DELAY:", E)
            return True
        elif text.startswith("name="): 
            print("saving as name", text[5:])
            self.line.emit(f"script -s {text[5:]}")
            return True
        elif text.startswith("loop"):
            if len(text) == 4: 
                self.loopNumb = -1
                return True
            if text[4] == '=':
                self.loopNumb = int(text[5:])
                self.loopStart = self.currentLine
                return True
        elif text == "endloop": 
            if self.loopNumb == -1: 
                self.currentLine = self.loopStart
            if self.loopNumb > 1: 
                self.loopNumb -= 1
                self.currentLine = self.loopStart
            return True
        elif text.startswith("wait"): 
            print("waiting....")
        elif text == "stop": 
            self._active = False
            self.finished.emit(True)
        else:
            return False

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
        self.printline.emit(output)

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
                line = line.replace("wait", "self.wait_")
            if "delay(" in line:
                line = line.replace("delay", "self.update_delay")
            if "save(" in line:
                line = line.replace("save", "self.save")
            program += line + '\n'
        print("PROGRAM:", program)
        exec(program)

    def run(self):
        while self._active:
            if self.use_python: 
                self.read(self.script)
                self.finished.emit(True)
                return
            else:
                while self.currentLine != self.numbLines and self._active: 
                    sline = self.script[self.currentLine]
                    send_line = True
                    is_command = False
                    #print("line: ", sline, "line number:", self.currentLine, "send", send_line)
                    if sline:
                        if sline[0] == "#":
                            is_command = True
                            if self.handle(sline[1:]):
                                #print("is command")
                                send_line = False 
                        if sline[0] == "@":
                            exec(sline[1:])
                            send_line = False
                        elif sline[:2] == "//": # comment
                            #print("COMMENT:" ,sline[2:]) 
                            is_command = True
                            send_line = False 
                    if send_line == True:
                        self.line.emit(sline)
                    if is_command == False:
                        time.sleep(self.delay)
                        #self.currentLine += 1
                    self.currentLine += 1
                self.finished.emit(True)
                return
                
    def stop(self):
        print("stopping script")
        self._active = False
        
if __name__ == "__main__": 
    import main
    main.execute()
