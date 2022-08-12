import shlex
import sys
import traceback

from sk_tools import vprint, eprint, DEBUG_LEVEL



class CLFunction:
    def __init__(self, name: str, function, max_args=None) -> None:
        self.name = name
        self.func = function
        self.options = {}
        self.max_args = max_args
        pass

    def add_option(self, keys: tuple, name: str = None, val_type=str, require_values=0):
        if isinstance(keys, str):
            keys = tuple(keys)

        if name == None:
            name = keys[0]

        self.options[keys] = {"name": name,
                              "type": val_type,
                              "required": require_values}

        pass

    def execute(self, input: str) -> tuple:
        if not (input.split(" ")[0] == self.name):  # keyword matched
            return None, ""
        try:
            tokens = shlex.split(input, posix=True)[1:]
        except Exception as E:
            eprint(f"CMD <{input}> '{E}'", color='red')
            return False, f"<{input}> {E}"

        args = []
        kw_args = {}
        current_option = None
        for token in tokens:
            is_kw = False
            for arg in self.options:
                if token in arg:
                    current_option = self.options[arg]
                    kw_args[self.options[arg]["name"]] = None
                    is_kw = True
                    break
            if is_kw:
                continue
            if current_option != None:
                if kw_args[current_option["name"]] == None:
                    kw_args[current_option["name"]] = current_option["type"](token)
                
            elif self.max_args == None or len(args) < self.max_args:
                args.append(token)
            else:
                print(f"<{self.name}> ARG: '{token}' invalid")
                return False, f"<{self.name}> ARG: '{token}' invalid"
        try:
            vprint("func: <", self.name, ">\targs: ", args, "\tkwargs: ", kw_args, color='yellow')
            self.func(*args, **kw_args)
            return True, ""
        except Exception as E:
            error_type, value, tb = sys.exc_info()
            tb_lines = traceback.format_tb(tb)
            eprint(traceback.format_exc())
            error = f"CMD <{input}>\n{tb_lines[-1]}\n{value}\n"
            return False, error


def test_commands():
    
    import sk_tools 
    sk_tools.DEBUG_LEVEL = 2

    def echo(*args, **kwargs):
        p_str = ""
        for arg in args:
            p_str += str(arg)

        for kwarg in kwargs:
            if kwarg == "-u":
                p_str = p_str.upper()
            elif kwarg == "-l":
                p_str = p_str.lower()
            elif kwarg == "-b":
                bck_val = int(kwargs['-b'])
                p_str = p_str[:-bck_val]

        print("ECHOING: ", p_str)

    def add(*args, **kwargs):
        sum = 0
        p_str = "("
        for arg in args:
            arg = float(arg)
            p_str += f"{arg} + "
            sum += arg

        for kw in kwargs:
            if kw == "-m":
                mult = float(kwargs[kw])
                p_str += f" * {mult}"
                sum *= mult
            if kw == "-d":
                div = float(kwargs[kw])
                p_str += f" / {div}"
                sum /= div
        
        p_str += f" = {sum}"
        print(p_str[:])

    cmd_echo = CLFunction("echo", echo, max_args=2)
    cmd_echo.add_option(("-u", "--upper"))
    cmd_echo.add_option(("-l", "--lower"))
    cmd_echo.add_option(("-b", "--back"))

    cmd_add = CLFunction("add", add)
    cmd_add.add_option(("-m", "--mult"), val_type=float)
    cmd_add.add_option(("-d", "--div"))

    cmd_list = [cmd_echo, cmd_add]

    user_str = "hi"
    while user_str:
        user_str = input("->")
        for cmd in cmd_list:
            result, error = cmd.execute(user_str)
            if result == False:
                print(error)

    pass


if __name__ == '__main__':
    test_commands()
