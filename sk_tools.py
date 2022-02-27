import os 
import platform
from termcolor import cprint
import os
import subprocess
import sys
import time
from datetime import datetime

from PyQt5.QtGui import QColor

DEBUG_ENABLED = True
VERBOSE_ENABLED = True


## COLOR DEFINES 
############################################
USER_OS = platform.system()
INSTALL_FOLDER = os.path.realpath(__file__).replace(__name__ + ".py", "")[0:-1]
CURRENT_FOLDER = os.getcwd()

print(INSTALL_FOLDER)
print(CURRENT_FOLDER)

## COLOR DEFINES 
############################################
COLOR_WHITE = QColor(255, 255, 255)
COLOR_LIGHT_GREY = QColor(225, 225, 225)
COLOR_GREY = QColor(150, 150, 150)
COLOR_DARK_GREY = QColor(80, 80, 80)
COLOR_BLACK = QColor(0, 0, 0)

COLOR_LIGHT_BLUE = QColor(105, 207, 255)
COLOR_DARK_BLUE = QColor(0, 0, 255)

COLOR_GREEN = QColor(24, 160, 0)

COLOR_RED = QColor(218, 0, 0)
COLOR_DARK_YELLOW = QColor(138, 140, 0)

COLOR_YELLOW = QColor(166, 157, 0)

def colorPrint(*args, color = 'white', **kwargs):
    pstr = ""
    for arg in args:
        pstr += str(arg)
    cprint(pstr, color=color, **kwargs)


def dprint(*args, color='white', **kwargs):
    if DEBUG_ENABLED:
        colorPrint(*args, color = color, **kwargs)

def vprint(*args, color='white', **kwargs):
    if VERBOSE_ENABLED:
        colorPrint(*args, color = color, **kwargs)

def colorToStyleSheet(color:QColor)->str:
    fmtcolor = f"rgb({color.red()}, {color.green()}, {color.blue()})"
    return fmtcolor



terminal_placeholder = '''***Serial from device will appear here***

Type "help" for detailed use instructions'''

plot_help = '''PLOT HELP
-kv\tstart the plotter in keyword-value mode
-a\tstart the plotter in array mode
-t [targets,]\tset the graph target values
-l [length]\tset a max length of 'length'
-p\tpause the plot
-r\tresume plotting
-c\tclear the plotter (and stop the plot)
-h\tdisplay this help message'''

log_help = '''LOG Help
ARGUMENTS:
(none)\topen the last log file avaliable
-o\topen a log file from the directory
-n [name]\tset the connection name to 'name'
-a [name]\tarchive the current log. Optional: archive as 'name'
-h\tdisplay this help message'''

script_help = '''\
**** SCRIPT HELP ****
Press ESCAPE or CTRL+C to stop a script mid-execution

COMMAND ARGUMENTS:
(none)\t run script in the script tab
-o [name]\t open a script. Optional: open "name".txt
-r \t run the script you are opening
-s [name] \t save current script. Optional: as "name".txt
-d [name] \t delete a script. Optional: delete "name".txt if it exists. 
-n [name]\t start new script. Optional: include "name" line
-t \t jump to script tab
-ls \t display all scripts in the script dir
-h\t display this help message

SCRIPT SPECIFIC KEYWORDS:
//\t\t\tComment. Ignored. 
#name=[myName]\t\tsave the script as [myName].txt every time it's run.
#delay=[numb]\t\tchange the delay between lines to [numb] milliseconds
#loop=[numb]\t\t\tloop until endloop [numb] times. 
#loop\t\t\tloop forever
#endloop\t\t\tsignal the end of a loop
$LOOP\t\treplaced with the loop number
#pause=[numb]\t\tpause for [numb] milliseconds 
#stop\t\tstop script at this line
'''


script_placeholder = script_help


'''Each newline is a sent to the device. 
Lines starting with # are used for configuration
Type "script -h" for more info'''