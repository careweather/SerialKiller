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

    def __init__(self, text: str, delay = 100):
        super().__init__()
        self.update_delay(delay)
        self.script = []
        self.script = text.splitlines(False)
        self.numbLines = len(self.script)
        self.currentLine = 0
        print(self.script)
        print("n lines:", self.numbLines)
        
        self._active = True
        self.incoming.connect(self.input)
        self.waiting = False
        self.loopStart = 0
        self.loopNumb = 0
        self.loopActive = False


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


    def input(self, text): 
        self.waiting = False
        print("handled from script:", text)

    def handle(self, text:str): 
        print("handling", text)
        text = text.replace(" ", "")
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
        elif text == "wait": 
            self.wait()
            return True
        elif text.startswith("loop="): 
            self.loopNumb = int(text[5:])
            self.loopStart = self.currentLine
            print("looping: ", self.loopNumb)
            return True
        elif text == "endloop": 
            print("loop numb:", self.loopNumb)
            if self.loopNumb > 1: 
                self.loopNumb -= 1
                self.currentLine = self.loopStart
            return True
        elif text == "stop": 
            self._active = False
            self.finished.emit(True)
        else:
            return False


    def update_delay(self, delay="100"):
        delay = int(delay)
        print("updating delay",delay)
        self.delay = delay/1000

    def run(self):
        while self._active:
            while self.currentLine != self.numbLines and self._active: 
                sline = self.script[self.currentLine]
                send = True
                is_command = False
                print("line: ", sline, "line number:", self.currentLine, "send", send)
                if sline:
                    if sline[0] == "#":
                        is_command = True
                        if self.handle(sline[1:]):
                            print("is command")
                            send = False 
                    elif sline[:2] == "//": # comment
                        print("COMMENT:" ,sline[2:]) 
                        is_command = True
                        send = False 
                
                if send == True:
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
