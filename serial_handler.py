import time
import traceback
from importlib import reload
from pyqtgraph.widgets.TreeWidget import TreeWidget

import serial
from PyQt5.QtCore import QObject, pyqtSignal
from serial.serialutil import (PARITY_EVEN, PARITY_MARK, PARITY_NONE,
                               PARITY_ODD, PARITY_SPACE)
from termcolor import cprint

from sk_tools import *

SER_PRINT = 1

baud_rates = serial.Serial.BAUDRATES


def serial_debug(*args, color='yellow'):
    if not SER_PRINT:
        return
    printstr = ""
    for arg in args:
        printstr += str(arg)
    cprint(printstr, color)


parity_values = {"NONE": PARITY_NONE, "EVEN": PARITY_EVEN,
                 "ODD": PARITY_ODD, "MARK": PARITY_MARK, "SPACE": PARITY_SPACE}


class SerialPort(QObject):
    incoming: pyqtSignal = pyqtSignal(str)
    error: pyqtSignal = pyqtSignal(bool)
    disconnect_signal = pyqtSignal(bool)
    ser = serial.Serial()

    def __init__(self) -> None:
        super().__init__()
        self.active = False
        self.connected = False
        self.port_name: str = None
        # self.baud_rate = 115200
        # self.xonxoff = False
        # self.dsrdtr = False
        # self.rtscts = False
        # self.parity = PARITY_NONE

        self.last_activity = 0
        self.error_message = ""

    def connect(self, port: str, baud=115200,
                xonxoff=False, rtscts=False,
                dsrdtr=False, parity:str = "NONE"):
        try:
            if self.ser.isOpen():
                self.ser.close()
            self.connected = False
            self.ser.port = port
            self.ser.baudrate = baud
            self.ser.rtscts = rtscts
            self.ser.dsrdtr = dsrdtr
            self.ser.rtscts = rtscts
            self.ser.xonxoff = xonxoff
            if parity in parity_values:
                parity = parity_values[parity]
            else: return False

            serial_debug("CONNECTING TO: ", port, " ", self.ser.get_settings(), color = 'yellow')
            self.ser.close()
            self.ser.open()
            if self.ser.isOpen():
                serial_debug("CONNECTED", color = 'green')
                self.ser.flush()
                self.connected = True
                return True
            else:
                return False
        except Exception as E:
            self.error_message = E
            return False

    def disconnect(self):
        
        self.ser.close()
        self.connected = False
        return True


    # def _connect(self):
    #     serial_debug("ATTEMPTING CONNECTION: ")
    #     try:
    #         self.ser = serial.Serial(
    #             timeout=100,
    #             baudrate=self.baud_rate,
    #             xonxoff=self.xonxoff,
    #             rtscts=self.rtscts,
    #             parity=self.parity,
    #             dsrdtr=self.dsrdtr)

    #         self.ser.port = self.port_name

    #         self.ser.close()

    #         self.ser.open()
    #         if self.ser.is_open:
    #             self.connected = True
    #             self.error_message = ""
    #             serial_debug(
    #                 "CONNECTED:", self.ser.getSettingsDict(), color='green')
    #             return True
    #         serial_debug("NOT CONNECTED:",
    #                      self.ser.getSettingsDict(), color='red')

    #     except Exception as E:
    #         serial_debug("ERROR CONNECTED:", self.ser.port,
    #                      self.ser.getSettingsDict(), "\n", E, color='red')
    #         self.error_message = E
    #     self.connected = False
    #     return False

    # def connect(self, port: str, baud=None, xonxoff: bool = None, dsrdtr: bool = None, parity: str = None, rtscts: bool = None) -> bool:
    #     if self.connected == True:
    #         serial_debug("ALREADY CONNECTED", 'red')
    #         return None

    #     self.port_name = port
    #     if baud != None:
    #         self.baud_rate = int(baud)
    #     if xonxoff != None:
    #         self.xonxoff = xonxoff
    #     if rtscts != None:
    #         self.rtscts = rtscts
    #     if dsrdtr != None:
    #         self.dsrdtr = dsrdtr
    #     if parity != None:
    #         parity: str = parity.upper()
    #         if parity not in parity_values:
    #             serial_debug("ERROR PARITY:", parity, "INVALID", color='red')
    #         else:
    #             self.parity = parity_values[parity]
    #     return self._connect()

    # def disconnect(self) -> bool:
    #     serial_debug("DISCONNECTING", self.ser.get_settings(), color='yellow')
    #     self.ser.close()
    #     self.connected = False
    #     print("IS OPEN:", self.ser.isOpen())

    #     return True

    def port_lost(self):
        serial_debug("PORT LOST", color='red')
        #self.active = False
        self.connected = False
        self.disconnect_signal.emit(True)

    def send_text(self, text: str = None):
        if self.connected:
            serial_debug("->" + text, color='blue')
            self.ser.write(text.encode('utf-8'))
        else:
            serial_debug(f'NOT CONNECTED ->', text, color='red')

    def get_text(self) -> str:
        if not self.ser.isOpen():
            print(self.ser.isOpen())
            self.ser.close()
            time.sleep(.5)

            self.ser.open()
            return None
        waiting = self.ser.inWaiting()
        if waiting:
            out_str = ""
            for c in self.ser.read(waiting):
                out_str += chr(c)
            return out_str
        return None

    def run(self):
        self.active = True
        while self.active:
            try:
                text = self.get_text()
                if text != None:
                    self.last_activity = time.perf_counter()
                    self.incoming.emit(text)
                elif time.perf_counter() - self.last_activity > .5:  # Throttle polling if no activity within .5 sec
                    time.sleep(.005)
            except Exception as E:
                self.error_message = E
                dprint(f"ERR: {traceback.format_exc()}\n", color='red')
                self.port_lost()

    def stop(self):
        self.active = False


class RescanWorker(QObject):
    disconnect = pyqtSignal(bool)
    new_ports = pyqtSignal(dict)
    active = True

    def __init__(self, update_interval=2) -> None:
        super().__init__()
        self.active = True
        self.update_interval = update_interval

    def run(self):
        while self.active:
            try:
                self.current_ports = getPorts()
                self.new_ports.emit(self.current_ports)
                time.sleep(self.update_interval)
            except Exception as E:
                cprint("RESCAN WORKER ERROR:", E)
                self.active = False
                self.disconnect.emit(False)

    def stop(self):
        self.active = False

    pass


if __name__ == "__main__":
    from sk_main_window import execute
    execute()
