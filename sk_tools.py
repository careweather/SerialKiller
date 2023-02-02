import os
import platform
from tracemalloc import start
from termcolor import cprint
from datetime import date, datetime

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFileDialog

DATE_TODAY = date.today()

USER_OS = platform.system()
INSTALL_FOLDER = os.path.realpath(__file__).replace(__name__ + ".py", "").removesuffix("\\").replace("\\", "/")
CURRENT_FOLDER = os.getcwd()

print(INSTALL_FOLDER)

SETTINGS_FOLDER = INSTALL_FOLDER + '/settings'
SETTINGS_FILE = INSTALL_FOLDER + "/user_settings.json"
SCRIPT_FOLDER = INSTALL_FOLDER + "/scripts/"
DEFAULT_LOG_FOLDER = INSTALL_FOLDER + "/logs/"

# COLORS
COLOR_WHITE = QColor(255, 255, 255)
COLOR_LIGHT_GREY = QColor(220, 220, 220)
COLOR_GREY = QColor(155, 155, 155)
COLOR_MED_DARK_GREY = QColor(100, 100, 100)
COLOR_DARK_GREY = QColor(79, 79, 79)
COLOR_BLACK = QColor(0, 0, 0)

COLOR_DARK_BLUE = QColor(0, 0, 255)
COLOR_LIGHT_BLUE = QColor(105, 207, 255)
COLOR_LAVENDER = QColor(171, 195, 255)


COLOR_LIGHT_GREEN = QColor(97, 255, 142)
COLOR_GREEN = QColor(24, 160, 0)

COLOR_RED = QColor(218, 0, 0)
COLOR_LIGHT_RED = QColor(255, 110, 110)
COLOR_DARK_RED = QColor(36, 0, 0)

COLOR_LIGHT_YELLOW = QColor(248, 252, 121)
COLOR_DARK_YELLOW = QColor(138, 140, 0)


ARROW_LEFT = "L"
ARROW_RIGHT = "R"
ARROW_DOWN = "D"
ARROW_UP = "U"

ARROW_UP = '↑'
ARROW_DOWN = '↓'
ARROW_RIGHT = "→"
ARROW_LEFT = "←"

TRIANGLE_DOWN = "▼"
TRIANGLE_RIGHT = "▶"

TYPE_RX = 0
TYPE_TX = 1

TYPE_INFO = 2
TYPE_WARNING = 3
TYPE_ERROR = 4
TYPE_CMD = 5
TYPE_HELP = 6

GITHUB_URL = "https://github.com/Alaraway/SerialKiller"

DEFAULT_SCRIPT_DELAY = 200

global DEBUG_LEVEL
DEBUG_LEVEL = 1  # Default to debug prints and error prints only.


def eprint(*args, color: str = "red", **kwargs):
    '''ERROR print debugging. Always Active'''
    p_string = ""
    for arg in args:
        p_string += str(arg)
    cprint(p_string, color=color, **kwargs)

# def dprint(*args, color: str = "white", **kwargs):
#     '''DEBUG print debugging. DEBUG_LEVEL 1+'''
#     if DEBUG_LEVEL:
#         p_string = ""
#         for arg in args:
#             p_string += str(arg)
#         cprint(p_string, color=color, **kwargs)


def vprint(*args, color: str = "white", **kwargs):
    '''VERBOSE print debugging. If debug level 2+'''
    if DEBUG_LEVEL > 1:
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


def get_timestamp():
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


def find_file(self, start_directory: str, file_name: str = None, file_extension: str = '.txt'):
    '''opens a popup if file_name == None. Returns "" if cancel. Returns None if no file found'''
    if file_name == None or file_name == False:
        file_path = QFileDialog.getOpenFileName(
            self, "Open", directory=start_directory, filter="*"+file_extension)[0]
        return file_path
    file_name = file_name.replace(file_extension, "")
    return_path = start_directory + str(file_name) + file_extension
    if os.path.exists(return_path):
        return return_path
    else:
        return None


def colorToStyleSheet(color: QColor) -> str:
    fmtcolor = f"rgb({color.red()}, {color.green()}, {color.blue()})"
    return fmtcolor


def get_cow(*args, **kwargs):
    from sk_help import COW_BORED, COW_DEAD, COW_BUBBLES, COW_NERD, COW_IN_LOVE
    if not args and not kwargs:
        return COW_BORED
    cow = COW_BUBBLES
    p_str = ""

    for arg in args:
        p_str += arg + " "

    if "-n" in kwargs:
        cow = COW_NERD
    
    if '-d' in kwargs:
        cow = COW_DEAD
    
    if '-l' in kwargs:
        cow = COW_IN_LOVE

    top = "_"
    for x in range(len(p_str)):
        top += "_"

    if not p_str:
        return cow

    cow_str = f"""\
 {top}
/ {p_str}\\
\\{top}/"""

    return cow_str + cow


def remove_from_string(input: str, removes=[]):
    for item in removes:
        input = input.replace(item, "")
    return input

def get_between(input:str, start:str, end:str) -> list:
    
    pass 

def get_file_name(input:str, start_folder:str, extension:str = None):
    if not input.endswith(extension): 
        input += extension
    if os.path.exists(input):
        return input, True
    input = start_folder + '/' + input
    if os.path.exists(input):
        return input, True
    return input, False

def replace_escapes(input: str) -> str:
    input = input.replace("\\\\n", '^n^').replace('\\\\r', '^r^').replace('\\\\t', '^t^')  # Temporary change any \\n, ,etc
    input = input.replace("\\n", '\n').replace('\\r', '\r').replace('\\t', '\t')
    return input.replace("^n^", '\\n').replace('^r^', '\\r').replace('^t^', '\\t')  # Replace any \\n, etc


STYLE_SHEET_TERMINAL_INACTIVE = f'background-color: {colorToStyleSheet(COLOR_DARK_GREY)};color: rgb(255, 255, 255);font: 10pt "Consolas";'
STYLE_SHEET_TERMINAL_ACTIVE = f'background-color: {colorToStyleSheet(COLOR_BLACK)};color: rgb(255, 255, 255);font: 10pt "Consolas";'
STYLE_SHEET_BUTTON_INACTIVE = f"background-color: {colorToStyleSheet(COLOR_GREY)};"
STYLE_SHEET_BUTTON_ACTIVE = f"background-color: {colorToStyleSheet(COLOR_GREEN)};"
STYLE_SHEET_SCRIPT = f'background-color: {colorToStyleSheet(COLOR_DARK_RED)};color: rgb(255, 255, 255);font: 10pt "Consolas";'
