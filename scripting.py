from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QIntValidator, QTextCursor
from PyQt5 import QtGui, QtWidgets
import subprocess
import json
import time 
import os
import sys
from datetime import datetime
import command


class ScriptWorker(QObject):
    line = pyqtSignal(str)
    finished = pyqtSignal(int)
    waiting = pyqtSignal(bool)
    _wait = pyqtSignal(bool)
    incoming = pyqtSignal(str)

    def __init__(self, text: str, delay = 100):
        super().__init__()
        self.update_delay(delay)
        self.script = []
        self.script = text.splitlines(False)
        self._active = True
        self.incoming.connect(self.input)
        self.waiting = False

    def input(self, text): 
        self.waiting = False
        print("handled from script:", text)

    def handle(self, text): 
        print("handling", text)
        if text[0:5] == "delay": 
            try: 
                self.delay = int(text[5:])/1000
            except Exception as E: 
                print("ERROR SETTING DELAY:", E)
            return True
        elif text == "wait": 
            self.wait()
            return True
        else:
            return False

    def wait(self, timeout = 10):
        self._active = False

    def update_delay(self, delay="100"):
        delay = int(delay)
        print("updating delay",delay)
        self.delay = delay/1000

    def run(self):
        while self._active:
            for sline in self.script:
                if sline:
                    if sline[0] == "#":
                        if self.handle(sline[1:]): continue
                if(self._active):
                    self.line.emit(sline)
                    time.sleep(self.delay)
            self._active = False
            self.finished.emit(True)

    def stop(self):
        print("stopping script")
        self._active = False
        


if __name__ == "__main__": 
    import main
    main.execute()
