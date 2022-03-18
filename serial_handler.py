import time
import traceback
from importlib import reload
from numpy.core.fromnumeric import sort
from pyqtgraph.widgets.TreeWidget import TreeWidget

import serial
from PyQt5.QtCore import QObject, pyqtSignal
from serial.serialutil import (PARITY_EVEN, PARITY_MARK, PARITY_NONE,
                               PARITY_ODD, PARITY_SPACE)
from termcolor import cprint

from pprint import pprint

import serial.tools.list_ports as list_ports

from sk_tools import *

SER_PRINT = 1

baud_rates = serial.Serial.BAUDRATES

ser = serial.Serial()


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
    active = True
    connected = False

    def __init__(self) -> None:
        super().__init__()
        self.last_activity = 0
        self.error_message = ""
        self.connected = False
        self.active = True

    def connect(self,port: str,baud=115200,xonxoff=False,rtscts=False,dsrdtr=False,parity="NONE") -> bool:
        if ser.isOpen():
            ser.close()
        
        try:
            self.connected = False
            ser.port = port
            ser.baudrate = baud
            ser.rtscts = rtscts
            ser.dsrdtr = dsrdtr
            ser.rtscts = rtscts
            ser.xonxoff = xonxoff
            if parity in parity_values:
                ser.parity = parity_values[parity]
            else:
                self.error_message = "INVALID PARIRY"
                return False

            ser.close()
            ser.open()

            if ser.isOpen():
                self.connected = True
                self.error_message = ""
                ser.flush()
                return True
            return False
        except Exception as E:
            self.error_message = E
            ser.port = None
            time.sleep(.1)


    def disconnect(self) -> bool:
        ser.close()
        if not ser.isOpen():
            self.connected = False
            return True
        return True


    def send_text(self, text: str = None):
            if self.connected:
                serial_debug("->" + text, color='blue')
                ser.write(text.encode('utf-8'))
            else:
                serial_debug(f'NOT CONNECTED ->', text, color='red')

    def get_text(self) -> str:
        waiting = ser.inWaiting()
        if waiting:
            out_str = ""
            for c in ser.read(waiting):
                out_str += chr(c)
            return out_str
        return None

    def run(self):
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
                self.disconnect_signal.emit(False)

    def stop(self):
        self.active = False        

# class SerialPort(QObject):
#     incoming: pyqtSignal = pyqtSignal(str)
#     error: pyqtSignal = pyqtSignal(bool)
#     disconnect_signal = pyqtSignal(bool)

#     def __init__(self) -> None:
#         super().__init__()
#         self.active = False
#         self.connected = False
#         self.port_name: str = None
#         self.last_activity = 0
#         self.error_message = ""

#     def connect(self, port: str, baud=115200,
#                 xonxoff=False, rtscts=False,
#                 dsrdtr=False, parity: str = "NONE"):
#         try:
#             if self.ser.isOpen():
#                 self.ser.close()
#             self.connected = False
#             self.ser.port = port
#             self.ser.baudrate = baud
#             self.ser.rtscts = rtscts
#             self.ser.dsrdtr = dsrdtr
#             self.ser.rtscts = rtscts
#             self.ser.xonxoff = xonxoff
#             if parity in parity_values:
#                 parity = parity_values[parity]
#             else:
#                 return False

#             serial_debug("CONNECTING TO: ", port, " ",
#                          self.ser.get_settings(), color='yellow')
#             self.ser.close()
#             self.ser.open()
#             if self.ser.isOpen():
#                 serial_debug("CONNECTED", color='green')
#                 self.ser.flush()
#                 self.connected = True
#                 return True
#             else:
#                 return False
#         except Exception as E:
#             self.error_message = E
#             return False

#     def disconnect(self):
#         self.ser.close()
#         self.connected = False
#         return True

#     def port_lost(self):
#         serial_debug("PORT LOST", color='red')
#         #self.active = False
#         self.connected = False
#         self.disconnect_signal.emit(True)

#     def send_text(self, text: str = None):
#         if self.connected:
#             serial_debug("->" + text, color='blue')
#             self.ser.write(text.encode('utf-8'))
#         else:
#             serial_debug(f'NOT CONNECTED ->', text, color='red')

#     def get_text(self) -> str:
#         if not self.ser.isOpen():
#             print(self.ser.isOpen())
#             self.ser.close()
#             time.sleep(.25)

#             self.ser.open()
#             return None
#         waiting = self.ser.inWaiting()
#         if waiting:
#             out_str = ""
#             for c in self.ser.read(waiting):
#                 out_str += chr(c)
#             return out_str
#         return None

#     def run(self):
#         self.active = True
#         while self.active:
#             try:
#                 text = self.get_text()
#                 if text != None:
#                     self.last_activity = time.perf_counter()
#                     self.incoming.emit(text)
#                 elif time.perf_counter() - self.last_activity > .5:  # Throttle polling if no activity within .5 sec
#                     time.sleep(.005)
#             except Exception as E:
#                 self.error_message = E
#                 dprint(f"ERR: {traceback.format_exc()}\n", color='red')
#                 self.port_lost()

#     def stop(self):
#         self.active = False


def get_serial_port_number(input: str) -> int:
    port_numb = 0
    if "COM" in input:
        try:
            port_numb = int(input.replace("COM", ""))
        except:
            port_numb = -1
    if "dev/ttyS" in input:
        try:
            port_numb = int(input.split("dev/ttyS")[1])
        except:
            port_numb = -1

    return port_numb


def sort_ports(input: dict) -> dict:
    result = {}
    return sorted(input, key=lambda x: input[x]['numb'])


def get_ports() -> dict:
    '''Get the Serial Ports Availiable'''
    ports = {}
    for port in list_ports.comports():
        ports[port.device] = {
            'descr': str(port.description),
            'name': str(port.name),
            'mfgr': str(port.manufacturer),
            'hwid': str(port.hwid),
            'vid': str(port.vid),
            'pid': str(port.pid),
            's/n': str(port.serial_number),
            'numb': get_serial_port_number(port.device)
        }

    sorted_ports = {}
    for name in sorted(ports, key=lambda x: ports[x]['numb']):
        sorted_ports[name] = ports[name]

    return sorted_ports


class RescanWorker(QObject):
    new_ports = pyqtSignal(dict)
    active = True

    def __init__(self, update_interval=1.00) -> None:
        super().__init__()
        self.active = True
        self.update_interval = update_interval

    def run(self):
        while self.active:
            try:
                self.new_ports.emit(get_ports())
                time.sleep(self.update_interval)
            except Exception as E:
                dprint(f"ERR: {traceback.format_exc()}\n", color='red')

    def stop(self):
        self.active = False


if __name__ == "__main__":
    from sk_main_window import execute
    execute()
