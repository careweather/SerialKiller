import serial
import platform
from time import sleep
import os
import subprocess

from serial.serialutil import PARITY_EVEN, PARITY_MARK, PARITY_ODD, PARITY_SPACE


_platform = platform.system()
ser = serial.Serial(timeout=1)

def sendString(toSend=""):
    try:
        ser.flush()
        ser.write(toSend.encode('utf-8'))
    except Exception as e:
        print("Error Sending Data: ", e)

# USE THIS IF THAT ^^^ Doesnt work
def getPorts_linux():
    stream = os.popen('python3 -m serial.tools.list_ports -q')
    inputStream = stream.read()
    inputStream = inputStream.replace(" ", "")
    serialPorts = inputStream.split('\n')
    serialPorts = list(filter(None, serialPorts))
    return serialPorts

def getPorts(): 
    if _platform == "Windows": 
        stream = os.popen("wmic path Win32_SerialPort Get DeviceID")
        tokens = stream.read().splitlines()
        return_ports = []
        for token in tokens: 
            if token.startswith("COM"):
                return_ports.append(token.strip())
        return return_ports
    else: 
        return getPorts_linux()
    

def makeConnection(port=None, baud=115200, parity = "NONE", xonxoff = False, rtscts=False, dsrdtr = False):
    try:
        ser.baudrate = baud
        ser.port = port
        if parity != "NONE": 
            if parity == "EVEN":
                ser.parity = PARITY_EVEN
            elif parity == "ODD": 
                ser.parity = PARITY_ODD
            elif parity == "MARK": 
                ser.parity = PARITY_MARK
            elif parity == "SPACE": 
                ser.parity = PARITY_SPACE
        if rtscts: 
            ser.rtscts = True
        if dsrdtr: 
            ser.dsrdtr = True
        if xonxoff: 
            ser.xonxoff = True
        ser.close()
        ser.open()
        if(ser.isOpen()):
            ser.flush()
            return True
        else:
            return False
    except Exception as E:
        print(f"Error opening port: {port} ", E)
        ser.port = None
        sleep(.1)


def getLine():
    waiting = ser.inWaiting()
    if waiting > 0:
        line = ser.readline()
        line = line.decode('UTF-8')
        return line

def getSerialString():
    waiting = ser.inWaiting()
    if waiting > 0:
        returnString = ""
        buffer = []
        buffer += [chr(c) for c in ser.read(waiting)]
        return returnString.join(buffer)
    else:
        return None

def closePort():
    ser.close()

if __name__ == '__main__':
    import main
    main.execute()
