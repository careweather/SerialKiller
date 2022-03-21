import shlex
import sys
import traceback

from sk_tools import *


class Command:
    def __init__(self, key: str, func, default_kw:str = None, default_type:type = str, ) -> None:
        self.key = key
        self.func = func
        self.default_arg = default_kw
        self.default_type = default_type
        self.arg_list = {}

    def add_argument(self, name: str, kw: str = None, data_type: type = str, default=None, required=False, help: str = None):
        if not kw:
            kw = name
        self.arg_list[name] = {"kw": kw,
                               "type": data_type,
                               "default": default,
                               "required": required,
                               "help": help}

    def _execute(self, input:str):
        args = {}
        tokens = shlex.split(input, posix=True)

        if tokens.pop(0) != self.key: # keyword matched 
            return None

        if self.default_arg and tokens:
            args[self.default_arg] = self.default_type(tokens.pop(0))

        while (tokens):
            token = tokens.pop(0)
            if token in self.arg_list: ## Found valid argument 
                if tokens: # tokens remaining 
                    if tokens[0] in self.arg_list: # Next token is an argument
                        args[self.arg_list[token]['kw']] = self.arg_list[token]['default']
                    else:
                        try:
                            args[self.arg_list[token]['kw']] = self.arg_list[token]['type'](tokens.pop(0))
                        except ValueError as E:
                            return f"ERR: {E}"
                else: 
                    args[self.arg_list[token]['kw']] = self.arg_list[token]['default']
            else:
                dprint(f"ERR IN CMD '{self.key}' ARG: '{token}' invalid", color = 'red')
                return f"ERR: CMD '{self.key}' ARG: '{token}' invalid"
                
        try: 
            self.func(**args)
            return True
        except Exception as E:
            dprint(f"ERR: {traceback.format_exc()} {sys.exc_info()[2]}", color = 'red')
            return f"ERR: {traceback.format_exc()} {sys.exc_info()[2]}"
    
    def execute(self, input:str):
        args = {}
        tokens = shlex.split(input, posix=True)

        if tokens.pop(0) != self.key: # keyword matched 
            return None

        if self.default_arg and tokens:
            args[self.default_arg] = tokens.pop(0)

        current_argument = ""
        current_value = []

        while (tokens):
            token = tokens.pop(0)
            if token in self.arg_list:
                current_argument = token
                args[current_argument] = []
            elif current_argument:
                args[current_argument].append(token)
            else:
                dprint(f"ERR IN CMD '{self.key}' ARG: '{token}' invalid", color = 'red')
                return f"ERR: CMD '{self.key}' ARG: '{token}' invalid"

        for arg in args:
            if len(args[arg]) == 1:
                args[arg] = str(args[arg][0])
            elif not (args[arg]):
                args[arg] = self.arg_list[arg]['default']

            
        try: 
            self.func(**args)
            return True
        except Exception as E:
            dprint(f"ERR: {traceback.format_exc()} {sys.exc_info()[2]}", color = 'red')
            return f"ERR: {traceback.format_exc()} {sys.exc_info()[2]}"
        
        