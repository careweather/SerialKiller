import shlex
import sys
import traceback

from sk_tools import *


class Command:
    def __init__(self, name: str, func, numb_args = 0, kw_options = []) -> None:
        self.name = name
        self.func = func
        self.numb_args = numb_args
        self.kw_options = kw_options
        if isinstance(kw_options, str):
            self.kw_options = [kw_options]
        
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
            if token in self.kw_options:
                current_option = token
                kw_args[current_option] = None
            elif current_option and kw_args[current_option] == None:
                kw_args[current_option] = token
                current_option = None 
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
