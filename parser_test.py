from parser_f import Parser, Command

def cmd_print(input, n_times = 1, capitalize = False): 
    if capitalize: 
        input = input.upper()

    for x in range(n_times): 
        print(input)

def cmd_add(numb_str, multiplier = 1):
    sum = 0 
    numb_arr = numb_str.split(",")
    for numb in numb_arr: 
        try: 
            sum += int(numb)
        except Exception as E: 
            print("Adding Error:", E)
    print(sum * multiplier)


parser = Parser()
print_cmd = Command("echo", cmd_print, 'input', default_required=True, help="echo a command")
print_cmd.add_argument("c", 'capitalize', bool, True)
print_cmd.add_argument('x', 'n_times', int)
add_cmd = Command("add", cmd_add, default_kw='numb_str')
add_cmd.add_argument("x", 'multiplier', float)
parser.add_command(Command("exit", quit))
parser.add_command(add_cmd)
parser.add_command(print_cmd)

userIn = input("Enter A String:")
while userIn != "quit": 
    if userIn == "": 
        print(parser)
    else: 
        ret = parser.parse(userIn)
        if ret:
            print(ret)
    print("------------")
    userIn = input("Enter A String:")
    


