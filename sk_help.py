'''
CONTAINS THE HELP STRINGS FOR COMMAND LINE USES
'''

SCRIPT_HELP = '''\
USEAGE: 'script' [OPTIONS]
Modify or run a script. 
If NO args are provided, the script in the script tab will be run. 

Use ESCAPE to exit a script mid-execution

Options:
    NONE        run the script in the script tab 
    -h          print this help text
    -s [name]   save the script.        OPTIONAL: as [name].txt
    -n [name]   start a new script.     OPTIONAL: as [name].txt
    -o [name]   open a script.          OPTIONAL: open [name].txt
    -rm <name>  remove a script.        REQURIRED: remove [name].txt
    -ls         list the scripts in the script directory
    -d <DELAY>  start the script with delay [DELAY] 
    -r [name]   run the script [name].txt.
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
    -o          open a log 
    -a [name]   archive the current log     OPTIONAL: as [name].txt
    -rm [name]  remove a log                REQUIRED: remove [name].txt
    -ls         list logs in the directory
'''
PLOT_HELP = '''\
USEAGE: plot <-kv|-a> [OPTIONS]
Start, or clear a plot

Command Line Options:
    -h              Print this help message 
    -kv             Start a plot in Key-Value mode
    -a              Start a plot in Single-Array mode
    -c              Clear the current plot
    -t [targets]    Set the plot keyword targets. 
                    Separate each with a comma
    -m              Set the windowing option to 'Max'
    -l [len]        Set the max length of [len] points
'''
CONNECT_HELP = '''\
USEAGE: con [OPTIONS]
Connect to a port. 
With NO arguments, the settings are selected from the 'Port' settings below.

OPTIONS:
[PORT]      The target port name.
            If all ports begin with "COM", only the COM# is required. 
            i.e, 3 = COM3
-b [BAUD]   connect at baud rate [BAUD]
-d          enable dsrdtr
-x          enable flow control (xonxoff)
-r          enable rtscts 
-p [PARITY] set parity to [PARITY] 

Examples (assuming ports are COM5 and COM10):
con 10                (connect to COM10)
con com5 -b 9600 -x   (connect to COM5. Set baud to 9600, enable flow control)
con 5 -p ODD          (connect to COM5. Set ODD parity)
'''

KEY_HELP = '''
USEAGE plot -k <KEY> -s <SEND> 
Add a key command

Options:
    -k <KEY>        set the key to be added
    -s <SEND>       set the value to be sent on <KEY>
    -c              clear the current key table

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
con [PORT] [OPTS]   Connect to a serial port. '-h' for help
dcon                Disconnect from the serial port
ports [-a]          List availiable ports. '-a' lists more info
script [OPTS]       Run, open or save a script. '-h' for options
log [OPTS]          Open, View, Edit logs. '-h' for options
clear               Clear the terminal
new                 Open a new window
quit                Quit immediately
key [OPTS]          Set key commands. '-h' for options
help                Show help popup
'''
