import shlex
import sys
import traceback

from sk_tools import *


class Command:
    def __init__(self, name: str, func, numb_args = 0, options = []) -> None:
        self.name = name
        self.func = func
        self.numb_args = numb_args
        self.options = options
        if isinstance(options, str):
            self.options = [options]
        

    def add_option(self, name: str, kw: str = None, data_type: type = str, default=None):
        pass 

    def execute(self, input: str):
        if not (input.split(" ")[0] == self.name):  # keyword matched
            return None
        try:
            tokens = shlex.split(input, posix=True)
        except Exception as E:
            return f"ERR: <{input}> {E}"

        args = []
        kw_args = {}
        tokens.pop(0)

        current_option = None

        while tokens:
            token = tokens.pop(0)
            if token in self.options:
                current_option = token
                kw_args[current_option] = None
            elif current_option:
                kw_args[current_option] = token
            elif len(args) < self.numb_args:
                args.append(token)
            else:
                vprint(f"ERR IN CMD '{self.name}' ARG: '{token}' invalid", color='red')
                return f"ERR: CMD '{self.name}' ARG: '{token}' invalid"

        vprint("cmd: ", self.name,"\targs: ", args, "\tkwargs: ", kw_args, color = 'yellow')

        try:
            self.func(*args, **kw_args)
            return True
        except Exception as E:
            eprint(f"ERR: {traceback.format_exc()} {sys.exc_info()[2]}", color='red')
            return f"ERR: {traceback.format_exc()} {sys.exc_info()[2]}"
