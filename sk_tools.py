import os
import platform
from termcolor import cprint
import os
from datetime import date

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFileDialog

import serial.tools.list_ports as list_ports

DATE_TODAY = date.today()

USER_OS = platform.system()
INSTALL_FOLDER = os.path.realpath(__file__).replace(__name__ + ".py", "")[0:-1]
CURRENT_FOLDER = os.getcwd()

SETTINGS_FILE = INSTALL_FOLDER + "/user_settings.json"
SCRIPT_FOLDER = INSTALL_FOLDER + "/scripts/"
LOG_FOLDER = INSTALL_FOLDER + "/logs/"

COLOR_WHITE = QColor(255, 255, 255)
COLOR_LIGHT_GREY = QColor(220, 220, 220)
COLOR_GREY = QColor(155, 155, 155)
COLOR_DARK_GREY = QColor(79, 79, 79)
COLOR_BLACK = QColor(0, 0, 0)

COLOR_DARK_BLUE = QColor(0, 0, 255)
COLOR_LIGHT_BLUE = QColor(105, 207, 255)

COLOR_LIGHT_GREEN = QColor(97, 255, 142)
COLOR_GREEN = QColor(24, 160, 0)

COLOR_RED = QColor(218, 0, 0)
COLOR_LIGHT_RED = QColor(255, 110, 110)
COLOR_DARK_RED = QColor(36, 0, 0)

COLOR_LIGHT_YELLOW = QColor(248, 252, 121)
COLOR_DARK_YELLOW = QColor(138, 140, 0)

DEBUG_LEVEL = 1

TYPE_RX = 0
TYPE_TX = 1

TYPE_INFO = 2
TYPE_WARNING = 3
TYPE_ERROR = 4
TYPE_CMD = 5
TYPE_HELP = 6

def dprint(*args, color: str = "white", **kwargs):
    if DEBUG_LEVEL:
        p_string = ""
        for arg in args:
            p_string += str(arg)
        cprint(p_string, color=color, **kwargs)


def get_number(obj, return_type=float, failure_val=None, lower_limit: float = None, upper_limit: float = None):
    rval = failure_val
    if isinstance(obj, (int, float)):
        rval = return_type(obj)
    try:
        rval = return_type(obj)
    except ValueError:
        return failure_val

    if lower_limit != None and rval < lower_limit:
        return failure_val

    if upper_limit != None and rval > upper_limit:
        return failure_val

    return rval




def find_file(self, start_directory:str, file_name:str = None, file_extension:str = '.txt'):
    '''opens a popup if file_name == None. Returns "" if cancel. Returns None if no file found'''
    if file_name == None or file_name == False:
        file_path = QFileDialog.getOpenFileName(self, "Open", directory= start_directory, filter = "*"+file_extension)[0]
        return file_path
    if file_extension in file_name:
        file_name.replace(file_extension, "")
    return_path = start_directory + str(file_name) + file_extension
    if os.path.exists(return_path):
        return return_path
    else:
        return None

def colorToStyleSheet(color: QColor) -> str:
    fmtcolor = f"rgb({color.red()}, {color.green()}, {color.blue()})"
    return fmtcolor

def replace_escapes(input: str) -> str:
    return input.replace("\\n", '\n').replace('\\r', '\r').replace('\\t', '\t')

STYLE_SHEET_TERMINAL_INACTIVE = f'background-color: {colorToStyleSheet(COLOR_DARK_GREY)};color: rgb(255, 255, 255);font: 10pt "Consolas";'
STYLE_SHEET_TERMINAL_ACTIVE = f'background-color: {colorToStyleSheet(COLOR_BLACK)};color: rgb(255, 255, 255);font: 10pt "Consolas";'
STYLE_SHEET_BUTTON_INACTIVE = f"background-color: {colorToStyleSheet(COLOR_GREY)};"
STYLE_SHEET_BUTTON_ACTIVE = f"background-color: {colorToStyleSheet(COLOR_GREEN)};"
STYLE_SHEET_SCRIPT = f'background-color: {colorToStyleSheet(COLOR_DARK_RED)};color: rgb(255, 255, 255);font: 10pt "Consolas";'

