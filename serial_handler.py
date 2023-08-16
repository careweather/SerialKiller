import time
import traceback

import serial
import serial.tools.list_ports as list_ports
from serial.tools.list_ports_common import ListPortInfo
from PyQt5.QtCore import QObject, pyqtSignal
from serial.serialutil import (PARITY_EVEN, PARITY_MARK, PARITY_NONE, PARITY_ODD, PARITY_SPACE)
from sk_tools import *
baud_rates = serial.Serial.BAUDRATES
ser = serial.Serial()
parity_values = {"NONE": PARITY_NONE, "EVEN": PARITY_EVEN,
                 "ODD": PARITY_ODD, "MARK": PARITY_MARK, "SPACE": PARITY_SPACE}


def serial_get_string(output = 'utf-8') -> str:
    if not ser.isOpen():
        return None
    waiting = ser.inWaiting()
    if waiting:
        if output == 'utf-8':
            out_str = ""
            for c in ser.read(waiting):
                out_str += chr(c)
            return out_str
        elif output == 'hex':
            out_str = ""
            for c in ser.read(waiting):
                out_str += hex(c) + ' '
            return out_str
        elif output == 'bin':
            out_str = ""
            for c in ser.read(waiting):
                out_str += bin(c) + ' '
            return out_str
        elif output == 'dec':
            out_str = ""
            for c in ser.read(waiting):
                out_str += str(c) + ' '
            return out_str
    return None

def serial_get_input() -> bytes:
    if not ser.isOpen() or not ser.in_waiting:
        return None 
    return ser.read(ser.in_waiting)


def serial_send_string(input: str = ""):
    try:
        ser.flush()
        ser.write(input.encode('utf-8', errors='replace'))
    except Exception as E:
        eprint("ERROR SENDING DATA:", E, color='red')

def serial_connect(port: str, baud=115200, xonxoff=False, rtscts=False, dsrdtr=False, parity="NONE"):
    try:
        ser.baudrate = baud
        ser.setPort(port)
        ser.xonxoff = xonxoff
        ser.rtscts = rtscts
        ser.dsrdtr = dsrdtr
        if parity not in parity_values:
            return False
        ser.parity = parity_values[parity]
        ser.close()
        ser.open()
        if (ser.isOpen()):
            ser.flush()
            return True
        else:
            return False
    except Exception as E:
        eprint(f"ERROR OPENING PORT: {port} ", E)
        eprint(f"ERR: {traceback.format_exc()}\n", color='red')
        ser.port = None
        time.sleep(.05)
        return False

def serial_disconnect():
    ser.cancel_read()
    ser.cancel_write()
    time.sleep(.01)
    ser.close()

class SerialWorker(QObject):  # THIS FETCHES SERIAL DATA. ASYNC.
    out = pyqtSignal(str)
    disconnected = pyqtSignal(bool)
    format = 'utf-8'

    def __init__(self):
        super().__init__()
        self.active = True
        self.last_activity = time.perf_counter()

    def run(self):
        while self.active:
            try:
                serial_data = serial_get_input()
                if serial_data is not None:
                    self.out.emit(serial_data.decode(self.format, errors = 'replace'))
                    self.last_activity = time.perf_counter()
                elif time.perf_counter() - self.last_activity > 1:  # Throttle polling if no activity within 1 sec
                    time.sleep(.01)
            except Exception as E:
                eprint("Serial Worker Error", E)
                eprint(f"ERR: {traceback.format_exc()}\n", color='red')
                self.active = False
                self.disconnected.emit(False)

    # def run(self):
    #     while self.active:
    #         try:
    #             serial_data = serial_get_string(self.format)
    #             if serial_data is not None:
    #                 self.out.emit(serial_data)
    #                 self.last_activity = time.perf_counter()
    #             elif time.perf_counter() - self.last_activity > 1:  # Throttle polling if no activity within .5 sec
    #                 time.sleep(.005)
    #         except Exception as E:
    #             eprint("Serial Worker Error", E)
    #             eprint(f"ERR: {traceback.format_exc()}\n", color='red')
    #             self.active = False
    #             self.disconnected.emit(False)

    def stop(self):
        self.active = False


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


def get_ports() -> dict:
    '''Get the Serial Ports Availiable'''
    ports = {}
    for port in list_ports.comports():
        port:ListPortInfo
        ports[port.name] = {
            'disp' : str(port.name),
            'descr': str(port.description),
            'dev': str(port.device),
            'name':str(port.name),
            'mfgr': str(port.manufacturer),
            'hwid': str(port.hwid),
            'vid': str(port.vid),
            'pid': str(port.pid),
            's/n': str(port.serial_number),
            'prod' : str(port.product),
            'numb': get_serial_port_number(port.device),
        }

    sorted_ports = {}
    for name in sorted(ports, key=lambda x: ports[x]['numb']):
        sorted_ports[name] = ports[name]

    return sorted_ports


class RescanWorker(QObject):
    new_ports = pyqtSignal(dict)
    active = True

    def __init__(self, update_interval=.5) -> None:
        super().__init__()
        self.active = True
        self.update_interval = update_interval

    def run(self):
        while self.active:
            try:
                self.new_ports.emit(get_ports())
                time.sleep(self.update_interval)
            except Exception as E:
                eprint(f"ERR: {traceback.format_exc()}\n", color='red')

    def stop(self):
        vprint("Stopping Rescan Worker")
        self.active = False


if __name__ == "__main__":
    from sk_main_window import execute
    execute()
