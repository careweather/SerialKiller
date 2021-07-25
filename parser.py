

DEBUG_PRINT = False

def dprint(input, *args): 
    if DEBUG_PRINT: 
        print(input, *args)


class Command:
    def __init__(self, keyword:str, func, default_kw = None, default_type = str, default_required = False) -> None:
        self.keyword = keyword
        self.func = func
        self.args = {}
        self.req_args = []
        self.default = False
        self.default_required = default_required
        if default_kw: 
            self.default = default_kw
            self.default_type = default_type
    
    def add_argument(self, argument:str, kwname = None, type = str, default = None, required = False):
        if kwname == None: 
             kwname = argument
        if required: 
            self.req_args.append(kwname)
        self.args[argument] = {"kw": kwname, "type": type, "default": default} 
        
    def separate(str):
        strs = 0 
        return strs 

    def execute(self, input:str):
        print('input: ' , str(input), type(input))
        args = input.split("-")
        dprint('args: ' , str(args), type(args))

        func_args = {} # dict to eventually be passed to a function

        if self.default: # first part is the default option
            default = args[0]
            if not default and self.default_required: 
                print("ERROR: No default parameter found")
                return "ERROR: No default parameter found"
            func_args[self.default] = self.default_type(args[0].strip())
            args = args[1:]
            

        for arg in args:
            dprint("argument:", arg)
            tok = arg.strip().split(" " , 2)
            dprint('tok: ' , str(tok), type(tok))
            if tok[0] in self.args: 
                #dprint("token valid")
                this_arg = self.args[tok[0]]
                if len(tok) > 1: 
                    value = this_arg['type'](tok[1])
                elif this_arg['default']: 
                    value = this_arg['default']
                else: 
                    return f"ERROR: Arguement '{tok[0]}' requires a value"
                func_args[this_arg['kw']] = value
            else: 
                dprint(f"ERROR: Argument '{tok[0]}' not recognized")
                return f"ERROR: Argument '{tok[0]}' not recognized"
        
        for req_arg in self.req_args: 
            if req_arg not in func_args:
                dprint(f"ERROR: Missing Required Argument {req_arg}")
                return f"ERROR: Missing Required Argument {req_arg}"

        print(func_args)
        self.func(**func_args)
        return ""
        
    def __str__(self) -> str:
        r = 'Key: "' +  self.keyword + '"\nArgs:'
        for arg in self.args: 
            r += "\t-" + str(arg)
            params = self.args[arg]
            r += "\ttype: " + str(params['type'])
            r += "\tdefault:" + str(params['default'])
            r += "\tfunc kw:" + str(params['kw'])
            r += '\n'
        return r + '\n'

class Parser: 
    def __init__(self) -> None:
        self.commands = []
        
    def add_command(self, command:Command): 
        self.commands.append(command)
        
    def parse(self, input:str): 
        dprint("PARSING:", input)
        subs = input.split(" ", 1)
        dprint("Subs", subs)
        for command in self.commands: 
            if subs[0] == command.keyword:
                if len(subs) > 1: 
                    command.execute(subs[1])
                else: 
                    command.execute("")
                return
        dprint("KEYWORD INVALID ")

    def __str__(self) -> str:
        r = "COMMANDS:\n"
        for command in self.commands: 
            r += str(command)
        return r 



def testFunc(): 
    global DEBUG_PRINT
    DEBUG_PRINT = True

    def echo(line:str = "Hello World", caps = False):
        if caps: 
            line = line.upper()
        print('echoing:' , str(line), type(line)) 


    def echos(line = "hello", n_times = 1, caps = False):
        print("n_times", n_times)
        if caps: 
            line = line.upper()
        for x in range(n_times): 
            print(line)
        
    def add(numbs:list, mult:int = 1): 
        print("Adding", numbs, "mult", mult)
        sum = 0
        for numb in numbs:
            if numb:  
                sum += int(numb)
        sum = sum*mult
        print("Result:", sum)
    
    parser = Parser()
    cmd1 = Command("echo", echo, default_kw="line", default_required=True)
    cmd1.add_argument("u", 'caps', bool, True)
    cmd2 = Command("echos", echos, default_kw="line")
    cmd2.add_argument("u", 'caps', type=bool, default=True)
    cmd2.add_argument("x", "n_times", type = int, required=True)
    parser.add_command(cmd1)
    parser.add_command(cmd2)
    print(parser)

    userIn = input("Enter A String:")
    while userIn != "quit": 
        if userIn == "": 
            print(parser)
        else: 
            parser.parse(userIn)
        print("------------")
        userIn = input("Enter A String:")
        


if __name__ == "__main__":
    testFunc() 
    #print("hello")