import os
from datetime import date
import logging

from sk_tools import *
import traceback

DEFAULT_LOG_FORMAT = '%(port)s\t|%(asctime)s.%(msecs)03d|\t%(message)s'
DEFAULT_TIME_FORMAT = "%I:%M:%S"
DEFAULT_LOG_NAME = f"log-{DATE_TODAY}.txt"



class SK_Logger:
    def __init__(self, directory:str = None, log_name:str = None, time_fmt:str = None, log_fmt:str = None, port_name:str = None) -> None:
        self.buffer = ""
        self.port_name = port_name
        self.formatter = logging.Formatter(fmt = log_fmt, datefmt=time_fmt, validate=True)
        self.logger = logging.getLogger(__name__)
        if not log_name:
            log_name = DEFAULT_LOG_NAME
        if not directory:
            directory = DEFAULT_LOG_FOLDER
        self.directory = directory
        self.log_name = log_name
        self.file_path = self.directory + self.log_name
        self.stop()
        self.handler = logging.FileHandler(self.file_path)
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        vprint(f"Logger Started: {self.file_path}", color='green')


    def set_port(self, port_name:str = None):
        self.port_name = port_name

    def stop(self):
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

    def write(self, text: str):
        self.buffer += text.replace("\r", "")
        if '\n' not in self.buffer:
            return
        lines = self.buffer.splitlines(True)
        self.buffer = ""
        try:
            for line in lines:
                if '\n' in line:
                    self.logger.warning(line.replace("\n", ""), extra={"port": self.port_name})
                else:
                    self.buffer += line
        except Exception as E:
            eprint("Log Write Error:", E)
            eprint(f"ERR: {traceback.format_exc()}\n", color='red')
            return E

    def archive(self, new_name: str = None, extension = ".txt"):
        self.stop()
        self.handler.close()
        if new_name == None:
            new_name = self.log_name
        new_name = new_name.replace(extension, "")
        logIndex = 0
        test_name = new_name
        while (os.path.exists(self.directory + test_name + extension)):
            vprint(f"{new_name} already exists!", color='yellow')
            logIndex += 1
            test_name = new_name + f'({logIndex})'

        os.rename(self.file_path, self.directory + test_name + extension)
        
        self.__init__()
        self.write("ARCHIVED\n")
        return

"""
class SK_Logger:
    def __init__(self, file_path = None, time_fmt: str = None, log_fmt: str = None, port_name: str = None) -> None:
        self.started = False
        self.buffer = ""
        self.formatter = logging.Formatter(fmt = replace_escapes(log_fmt), datefmt=replace_escapes(time_fmt), validate=True)
        self.port_name = port_name
        
        if not file_path:
            self.file_path = f"{DEFAULT_LOG_FOLDER}log-{DATE_TODAY}.txt"
        if file_path:
            self.file_path = file_path

        vprint(self.file_path)
        self.logger = logging.getLogger(__name__)
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        self.handler = logging.FileHandler(self.file_path)
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        
    def start(self):
        return 
        try:
            if self.started:
                self.stop()
                return
            self.started = True
            logging.basicConfig(filename=self.file_path, )
            vprint("Logger Started: ", self.file_path, "\tlog_fmt: ", self.formatter,color='green')
        except Exception as E:
            eprint("Log Start Error:", E)
            eprint(f"ERR: {traceback.format_exc()}\n", color='red')
            return E

    def set_file(self, file_path:str = None):
        if not file_path:
            self.file_path = f"{DEFAULT_LOG_FOLDER}log-{DATE_TODAY}.txt"
        if file_path:
            self.file_path = file_path

        self.logger.removeHandler(self.handler)
        self.handler = logging.FileHandler(self.file_path)
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        
    def set_format(self, log_fmt:str = None, time_fmt:str = None):
        self.formatter = logging.Formatter(fmt = replace_escapes(log_fmt), datefmt=replace_escapes(time_fmt), validate=True)
        self.handler.setFormatter(self.formatter)

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
                    self.logger.warning(line.replace("\n", ""), extra={"port": self.port_name})
                else:
                    self.buffer += line
        except Exception as E:
            eprint("Log Write Error:", E)
            eprint(f"ERR: {traceback.format_exc()}\n", color='red')
            return E

"""



# class SK_Logger:
#     def __init__(self, folder_path: str = None, file_name: str = None, time_fmt: str = None, log_fmt: str = None, port_name: str = None, file_extension=".txt") -> None:
#         self.started = False
#         self.buffer = ""
#         self.port_name = port_name
#         self.log_fmt = replace_escapes(log_fmt)
#         self.time_fmt = time_fmt
#         self.file_extension = file_extension
#         self.folder_path = folder_path
#         self.file_name = file_name
#         if not self.folder_path:
#             self.folder_path = DEFAULT_LOG_FOLDER
#         if not file_name:
#             self.file_name = DEFAULT_FILE_NAME
#         else:
#             self.file_name = file_name.split(".")[0]
#         if not self.time_fmt:
#             self.time_fmt = DEFAULT_TIME_FORMAT
#         if not self.log_fmt:
#             self.log_fmt = DEFAULT_LOG_FORMAT
#         if not self.port_name:
#             self.port_name = None
#         self.file_path = self.folder_path + self.file_name + file_extension

#     def start(self):
#         try:
#             if self.started:
#                 return
#             self.started = True
#             logging.basicConfig(filename=self.file_path,
#                                 format=self.log_fmt,
#                                 datefmt=self.time_fmt)
#             vprint("Logger Started: ", self.file_path, "\tlog_fmt: ", self.log_fmt, "\ttime_fmt: ", self.time_fmt,   color='green')
#         except Exception as E:
#             eprint("Log Start Error:", E)
#             eprint(f"ERR: {traceback.format_exc()}\n", color='red')
#             return E

#     def restart(self, folder_path: str = None, file_name: str = None, time_fmt: str = None, log_fmt: str = None, port_name: str = None, file_extension=".txt"):
#         self.stop()
#         self.port_name = port_name
#         self.log_fmt = replace_escapes(log_fmt)
#         if folder_path:
#             self.folder_path = DEFAULT_LOG_FOLDER
#         if file_name:
#             self.file_name = f"log-{DATE_TODAY}.txt"
#         if time_fmt:
#             self.time_fmt = time_fmt
#         if log_fmt:
#             self.log_fmt = log_fmt
#         if port_name:
#             self.port_name = port_name
#         if self.file_name.endswith(".txt") == False:
#             self.file_name += '.txt'
#         self.file_path = self.folder_path + self.file_name
#         self.start()

#     def set_port(self, port_name: str):
#         self.stop()
#         self.port_name = port_name
#         self.start()

#     def stop(self):
#         if not self.started:
#             return
#         self.started = False
#         self.buffer = ""
#         logging.shutdown()
#         log_instance = logging.getLogger()
#         for handler in log_instance.handlers[:]:
#             if isinstance(handler, logging.FileHandler):
#                 log_instance.removeHandler(handler)
#                 vprint("Logger Stopped", color='yellow')

#     def archive(self, new_name: str = None):
#         self.stop()
#         if new_name == None:
#             new_name = self.file_name
#         new_name = new_name.replace(".txt", "")
#         logIndex = 0
#         test_name = new_name
#         while (os.path.exists(self.folder_path + test_name + ".txt")):
#             vprint(f"{new_name} already exists!", color='yellow')
#             logIndex += 1
#             test_name = new_name + f'({logIndex})'

#         os.rename(self.folder_path + self.file_name, self.folder_path + test_name + ".txt")
#         self.start()
#         self.write("ARCHIVED\n")
#         return

#     def write(self, text: str):
#         self.buffer += text.replace("\r", "")
#         if '\n' not in self.buffer:
#             return
#         lines = self.buffer.splitlines(True)
#         self.buffer = ""
#         try:
#             for line in lines:
#                 if '\n' in line:
#                     logging.warning(line.replace("\n", ""), extra={"port": self.port_name})
#                 else:
#                     self.buffer += line
#         except Exception as E:
#             eprint("Log Write Error:", E)
#             eprint(f"ERR: {traceback.format_exc()}\n", color='red')
#             return E


