import subprocess

from sys import platform

lib_deps = ['numpy', 'pandas', 'pyqt5', 'pyqt5-tools', 'pyqtgraph', 'pyserial', 'colorama', 'datetime']

def install_dependancies():
    if platform == "linux" or platform == "linux2": 
        clear_cmd = "clear"
    elif platform == "win32":
        clear_cmd = "cls"
    subprocess.call(clear_cmd, shell=True)
    for library in lib_deps:
        print(f"--INSTALLING {library}...")
        if subprocess.call(f"pip install {library}", shell=True):
            print(f"ERROR INSTALLING LIBRARY {library}")
            exit()
        else: 
            subprocess.call(clear_cmd, shell=True)
    print("---INSTALL COMPLETE---")

def test():
    install_dependancies()

if __name__ == "__main__": 
    test()
