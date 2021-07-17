import serial
from time import sleep
import os

ser = serial.Serial(timeout=1)

def sendString(toSend=""):
    try:
        ser.flush()
        ser.write(toSend.encode('utf-8'))
    except Exception as e:
        print("Error Sending Data: ", e)


def getPorts():
    stream = os.popen('py -m serial.tools.list_ports -q')
    inputStream = stream.read()
    inputStream = inputStream.replace(" ", "")
    serialPorts = inputStream.rsplit('\n')
    serialPorts = list(filter(None, serialPorts))
    #print("Found Ports: ", serialPorts)
    return serialPorts


def makeConnection(port=None, baud=115200):
    try:
        ser.baudrate = baud
        ser.port = port
        #print(f'Connecting to: {port} at baud rate {baud}')
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
