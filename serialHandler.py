import serial
import platform
from time import sleep
import os
import subprocess


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
    stream = os.popen('py -m serial.tools.list_ports -q')
    stream = subprocess.call()
    inputStream = stream.read()
    inputStream = inputStream.replace(" ", "")
    serialPorts = inputStream.rsplit('\n')
    serialPorts = list(filter(None, serialPorts))
    return serialPorts



def getPorts(): 
    if _platform == "Windows": 
        #print('_platform:' , str(_platform), type(_platform))
        r = subprocess.Popen("powershell [System.IO.Ports.SerialPort]::getportnames()", shell=True, stdout=subprocess.PIPE)
        s = r.stdout.read().decode('utf-8')
        #s = s.decode('utf-8')
        lines = s.splitlines()
        return lines
    else: 
        return getPorts_linux()
    
    




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
