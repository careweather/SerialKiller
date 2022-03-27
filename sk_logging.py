import os
from datetime import date
import logging
from sk_tools import *
import traceback

DEFAULT_LOG_FORMAT = '%(port)s\t|%(asctime)s.%(msecs)03d|\t%(message)s'
DEFAULT_TIME_FORMAT = "%I:%M:%S"


class Logger:
    def __init__(self, folder_path: str = None, file_name: str = None, time_fmt: str = None, log_fmt: str = None, port_name: str = None, file_extension=".txt") -> None:
        self.started = False
        self.buffer = ""
        self.port_name = port_name
        self.log_fmt = replace_escapes(log_fmt)
        self.time_fmt = time_fmt
        self.file_name = file_name
        self.file_extension = file_extension
        self.folder_path = folder_path
        if not self.folder_path:
            self.folder_path = DEFAULT_LOG_FOLDER
        if not self.file_name:
            self.file_name = f"log-{DATE_TODAY}.txt"
        if not self.time_fmt:
            self.time_fmt = DEFAULT_TIME_FORMAT
        if not self.log_fmt:
            self.log_fmt = DEFAULT_LOG_FORMAT
        if not self.port_name:
            self.port_name = None
        if self.file_name.endswith(".txt") == False:
            self.file_name += '.txt'
        self.file_path = self.folder_path + self.file_name

    def start(self):
        try:
            if self.started:
                return
            self.started = True

            logging.basicConfig(filename=self.file_path,
                                format=self.log_fmt,
                                datefmt=self.time_fmt)
            vprint("Logger Started: ", self.file_path, "\tlog_fmt: ", self.log_fmt, "\ttime_fmt: ", self.time_fmt,   color='green')
        except Exception as E:
            eprint("Log Start Error:", E)
            eprint(f"ERR: {traceback.format_exc()}\n", color='red')
            return E

    def restart(self, folder_path: str = None, file_name: str = None, time_fmt: str = None, log_fmt: str = None, port_name: str = None, file_extension=".txt"):
        self.stop()
        self.port_name = port_name
        self.log_fmt = replace_escapes(log_fmt)
        if folder_path:
            self.folder_path = DEFAULT_LOG_FOLDER
        if file_name:
            self.file_name = f"log-{DATE_TODAY}.txt"
        if time_fmt:
            self.time_fmt = time_fmt
        if log_fmt:
            self.log_fmt = log_fmt
        if port_name:
            self.port_name = port_name
        if self.file_name.endswith(".txt") == False:
            self.file_name += '.txt'
        self.file_path = self.folder_path + self.file_name
        self.start()

    def set_port(self, port_name: str):
        self.stop()
        self.port_name = port_name
        self.start()

    def stop(self):
        if not self.started:
            return
        self.started = False
        self.buffer = ""
        logging.shutdown()
        log_instance = logging.getLogger()
        for handler in log_instance.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                log_instance.removeHandler(handler)
                vprint("Logger Stopped", color='yellow')

    def archive(self, new_name: str = None):
        self.stop()
        if new_name == None:
            new_name = self.file_name
        new_name = new_name.replace(".txt", "")
        logIndex = 0
        test_name = new_name
        while (os.path.exists(self.folder_path + test_name + ".txt")):
            vprint(f"{new_name} already exists!", color='yellow')
            logIndex += 1
            test_name = new_name + f'({logIndex})'

        os.rename(self.folder_path + self.file_name, self.folder_path + test_name + ".txt")
        self.start()
        self.write("ARCHIVED\n")
        return

    def write(self, text: str):
        self.buffer += text.replace("\r", "")
        if '\n' not in self.buffer:
            return
        lines = self.buffer.splitlines(True)
        self.buffer = ""
        try:
            for line in lines:
                if '\n' in line:
                    logging.warning(line.replace("\n", ""), extra={"port": self.port_name})
                else:
                    self.buffer += line
        except Exception as E:
            eprint("Log Write Error:", E)
            eprint(f"ERR: {traceback.format_exc()}\n", color='red')
            return E
