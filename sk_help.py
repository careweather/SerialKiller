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


LOG_HELP = '''\
USEAGE: 'log' [OPTIONS]

Options:
    NONE        open the most recent log 
    -o          open a log 
    -a [name]   archive the current log     OPTIONAL: as [name].txt
    -rm [name]  remove a log                REQUIRED: remove [name].txt
    -ls         list logs in the directory
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
#warning=[string]           Print [string] to the terminal as a warning
#error=[string]             Print [string] to the terminal as an error
#loop=[numb_loops]          Run the code between this line and #endloop [numb_loops] times.
                            If no '=[numb_loops]' is provided, it will run infinitely
#endloop                    Signals the end of the loop 
#exit                       Exit the script at this line. 

Script Special Words:
$LOOP                       Replaced with the current loop index.
$ARG                        Replaced with the arguments passed with script call -a
'''

PLOT_HELP = '''\
USEAGE:
plot <-kv|-a> [OPTIONS]
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
COMMAND 'con'
Connect to a port.

Command Line Options:
    [PORT]      connect to port name [PORT]
                '?' expands port dropdown
    -b [BAUD]   connect at baud rate [BAUD](int)
    -d          enable dsrdtr
    -x          enable flow control (xonxoff)
    -r          enable rtscts 
    -p [PARITY] set parity to [PARITY] 
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
Serial from the device will appear here
Type "help" for more information

Commands: 
con [PORT] [OPTIONS] 
    Connect to a serial port. 
    If no [PORT] argument is given, the port dropdown will be selected
    use 'con -h' for options
dcon
    Disconnect from the serial port
ports
    List availiable ports
script [OPTIONS]
    Run, open or save a script
    use 'script -h' for options
log [OPTIONS]      
    Open, View, Edit logs 
    use 'con -h' for options
clear
    Clear the terminal
quit     
    Quit immediately
help      
    Show help popup
'''
