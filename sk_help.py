'''
CONTAINS THE HELP STRINGS FOR COMMAND LINE USES
'''

from sk_tools import GITHUB_URL

GREETINGS_TEXT = f'''\
                    _         _   _     _  _  _             
                   (_)       | | | |   (_)| || |            
   ___   ___  _ __  _   __ _ | | | | __ _ | || |  ___  _ __ 
  / __| / _ \| '__|| | / _` || | | |/ /| || || | / _ \| '__|
  \__ \|  __/| |   | || (_| || | |   < | || || ||  __/| |   
  |___/ \___||_|   |_| \__,_||_| |_|\_\|_||_||_| \___||_|   
                                                           
-----------------Written by Alex Laraway--------------------
{GITHUB_URL}

run with --h for CLI options
'''
SCRIPT_HELP = '''\
USEAGE: 
    script [options]
If NO options are provided, the script in the script tab will be run. 
Options:
    NONE                run the script in the script tab 
    -h, --help          print this help text
    -s, --save [name]   save the script.   (optional: 'name'.txt)
    -n, --new [name]    start a new script. (optional: 'name'.txt)
    -o, --open [name]   open a script. (optional: 'name'.txt)
    -rm [name]          remove a script. (optional: 'name'.txt)
    -ls                 list the scripts in the script directory
    -r [name]           run the script [name].txt.

Use ESCAPE to exit a script mid-execution
'''
SCRIPT_SYNTAX_HELP = '''\
Each line in this text will be evaluated as if it was typed into the 'output' line.
Lines are evaluated with a delay between sends.
Lines starting with '#' are evaluated as commands. 
'//' Is a comment. It is not included. 

Script Commands:
#name=[name]                Save the script as [name].txt
#delay=[milliseconds]       Delay between sends [milliseconds] (int)
#ARG=[default]              Set the default argument if none is provided from a command
#info=[string]              Print [string] to the terminal as info
#error=[string]             Print [string] to the terminal as an error
#loop=[numb_loops]          Run the code between this line and #endloop [numb_loops] times.
                            If no '=[numb_loops]' is provided, it will run infinitely
#endloop                    Signals the end of the loop 
#exit                       Exit the script at this line. 

Script Special Words:
$LOOP                       Replaced with the current loop index.
$ARG                        Replaced with the arguments passed with script call -a
'''
LOG_HELP = '''\
USEAGE: log [OPTIONS]
If NO options are provided, the most recent log is opened.

Options:
    -h, --help              Show this help message
    -o, --open              open a log 
    -a, --archive [name]    archive the current log (optional [name].txt)
    -ls, --list             list all logs
    --name <name>           Set the log "name"
    --tfmt <format>         Set the log "time format"
    --fmt <format>          Set the log "format"
'''
PLOT_HELP = '''\
USEAGE:
    plot [command] [options]

Commands:
    kv, key-value       Start a plot in Key-Value mode 
    sv, single-value    Start a plot in Single-Value mode 
    sa, single-array    Start a plot in Single-Array mode 
    ka, key-array       Start a plot in Key-Array mode 
    p, pause            Pause / Resume the plot 
    c, clear            Clear the Plot 

Options:
    -h, --help              Print this help message
    -s, --seps <seps>       Set the separators to [seps]
    -r, --ref <refs>        Set the reference lines to [refs]
    -l, --limits <limits>   Set the plot limit mode ("Max" or "Window")
    -k, --keys <keys>       Set the target keywords (comma seperate)
    -p, --points <points>   Set the number of plot points
'''
CONNECT_HELP = '''\
USEAGE: 
    con [portname] [options]

If no [portname] is given, it is selected from the "port" dropdown below.
[portname] can be the full port name or the COM number. i.e, 3 = COM3

OPTIONS:
    -h, --help          Show this help message
    -b, --baud <rate>   Set baud rate [rate] 
    -d, --dsrdtr        enable dsrdtr
    -x, --xonxoff       enable flow control (xonxoff)
    -r, --rtscts        enable rtscts 
    -p, --parity <p>    set parity to [p] 

Examples (assuming ports are COM5 and COM10):
con 10                (connect to COM10)
con com5 -b 9600 -x   (connect to COM5. Set baud to 9600, enable flow control)
con 5 -p ODD          (connect to COM5. Set ODD parity)
'''

KEY_HELP = '''
USEAGE:
    key                     Jump to "keyboard" text edit
    key set <key> <value>   set <key> to <value> in table
    key clear               Clear the current table

Options:
    -h, --help      Show this help message

'''

HELP_TEXT = '''\
Serial from the device will appear here. 
Type "help" for to view help pop-up.
Navigation: 
    ESC             Jump to Input, stop script
    CTRL+P          Show ports
    CTRL+E          Clear Terminal
    CTRL+S          Start Script
    CTRL+< or >     Tab Right or left
    CTRL+SHIFT+c    Connect or Disconnect

Common Commands: 
    con [port] [options]    Connect to a serial port. '-h' for help
    dcon                    Disconnect from the serial port
    ports [-a]              List availiable ports. '-a' lists more info
    script [options]        Run, open or save a script. '-h' for help
    log [options]           Open, View, Edit logs. '-h' for options
    clear                   Clear the terminal
    new                     Open a new window
    quit                    Quit immediately
    key [options]           Set key commands. '-h' for options
    help                    Show help popup
'''

COW_BORED = """
      Z Z   ^__^
        z z (--)\_______
            (__)\       )\\
                ||----w |
                ||     ||
"""

COW_DEAD = """
        \   ^__^         
         \  (XX)\_______        George, not the livestock...   
            (__)_ x   x )---            \  ,-----, 
              U ||----w |               ,--'---:---`--,
                ||     ||               ==(o)-----(o)==J
"""

COW_BUBBLES = """
  O   o     ^__^
      o  o  (--)\_______
          o (o )\       )\\
                ||----w |
                ||     ||
"""

COW_IN_LOVE = '''
        ^__^ ^__^
 ______/(-oo)(--)\_______
(       /( <)(> )\       )\\
|_______||        ||----w |
||      ||        ||     ||
'''

COW_NERD = """
        \  ^___^
         \ (oo-)\___________
           (u_ )            |->
               \            |
                ||-------WW |
                ||         ||
"""
