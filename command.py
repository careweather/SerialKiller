

TYPE_EMPTY = 0
TYPE_DASH = 1
TYPE_PARENTHESIS = 2
TYPE_NONE = 3


debug = False


def dprint(*args):
    if debug:
        for arg in args:
            
            print("COMMAND DEBUG:" ,arg)


class _command():
    def __init__(self, key, funct, funct_name="function", type=TYPE_NONE, req_args=0):
        self.key = key
        self.funct = funct
        self.funct_name = funct_name
        self.type = type
        self.req_args = req_args


class commands():
    def __init__(self):
        self.commandList = []

    def add_command(self, key, funct, funct_name="function", parse="disable", req_args=0):
        dprint(key)
        myType = TYPE_EMPTY
        if parse == "paren":
            myType = TYPE_PARENTHESIS
        if parse == "dash":
            myType = TYPE_DASH
        if parse == "none":
            myType = TYPE_NONE

        new = _command(key, funct, funct_name, myType, req_args)
        self.commandList.append(new)

    def use_bracket(self, val=True):
        self.using_brackets = val

    def use_args(self, val=True):
        self.using_args = val

    def parseArgs(self, input, typeof):
        args = []
        n_args = 0
        if typeof == 0:
            return [args, n_args]
        elif typeof == TYPE_NONE:  # no other param
            args = input
            n_args = 1
            dprint('args: ', str(args))
            if args:
                return [args, n_args]
        elif typeof == TYPE_DASH:  # dashes
            input = input.replace(" ", "")
            args = input.split('-')
            args = args[1:]
            dprint('args: ', str(args))
            n_args = len(args)
            dprint('n_args: ', str(n_args))
            return [args, n_args]
        elif typeof == TYPE_PARENTHESIS:  # parse parenthesis
            if "(" not in input or ")" not in input:
                return ["", 0]
            input = input[input.find("(")+1:input.find(")")]
            dprint('input: ', str(input))
            args = input.split(',')
            n_args = len(args)
            dprint('args: ', str(args), type(args))
            return [args, n_args]
        return ""

    def compare(self, target, comparison):
        len_target = len(target)
        if comparison[:len_target] == target:
            remainder = comparison[len_target:]
            return remainder
        return -1

    def check(self, input, execute=True):
        # print(self.commandList)
        for com in self.commandList:
            result = self.compare(com.key, input)
            if result != -1:
                func = com.funct
                parsed = self.parseArgs(result, typeof=com.type)
                args = parsed[0]
                n_args = parsed[1]
                if com.type == TYPE_NONE:
                    func(args)
                    return True

                dprint('args: ', str(args))
                dprint(type(args))
                
                dprint('n_args: ', str(n_args))
                if n_args < com.req_args:
                    print("ERROR TOO FEW ARGUMENTS")
                    return False
                if n_args == 0:
                    func()
                    return True
                elif n_args == 1:
                    func(*args)
                    return True
                else:
                    func(*args)
                    return True
        return False


def test2():

    def echoMeCaps(*text):
        _lines = text
        print('_lines: ', str(_lines), type(_lines))
        for line in _lines:
            print(line)
            if type(line) == list:
                print("is a list")
                for subline in line:
                    print(subline.upper())
            else:
                print(line.upper())

    def echoTimes(text="hello", nTimes = 2):
        try:
            if (type(nTimes)) == str:
                nTimes = int(nTimes)
            for times in range(nTimes):
                print(text)
        except Exception as E:
            print(E)

    def echoMe(text="no text added"):
        print(text)

    def adder(*args):
        x = 0
        xstr = ""
        for arg in (args):
            try:
                x += int(arg)
            except:
                xstr += arg
                pass
        print("sum", x)
        print("strsum", xstr)

    coms = commands()
    coms.use_args(True)
    coms.add_command("echo", echoMe, "Echo Me", parse= "none")
    coms.add_command("ECHO", echoMeCaps, "Echo Me CAPS", parse= "dash", req_args=1)
    coms.add_command("add", adder, "Adder", parse="paren")
    coms.add_command("times", echoTimes, "Adder", parse="paren")
    coms.add_command("exit", exit, "")

    userin = ""
    quit_vars = ["q", "quit", "x"]
    while userin not in quit_vars:
        userin = str(input("Type A Keyword:"))
        coms.check(userin)


if __name__ == '__main__':
    # print(__name__)
    test2()
