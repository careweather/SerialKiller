## SERIAL KILLER QUICK HELP
More full documentation is avaliable in the github repo linked below. 

Certain functions are accessable via "terminal style" commands.  
Enter the keyword directly into the "To Device" text box. 
### TERMINAL COMMANDS:  
| --Key-- | --Function-- | 
|:-------------:|:-------------|
|help|open this help window|
|con|connect to the port selected|
|dcon|disconnect|
|clear|clear terminal text|
|script|run the script in script tab|
|quit|close the program immediately|
|save|save current configuration|
|new|open a new window|
|log|open the latest log|
|logs|open a log from the log directory|
|scan|rescan for Serial Ports|
|auto|toggle auto-reconnect|
|com*|open com port (*) if it's avaliable|
|baud*|change baud rate to (*)|


### Command Conflicts: 
If there are possible conflicts between commands and messages to send to a device, a command char can be used to distinguish commands.  
For example, "$" would mean that only commands that begin with $ are accepted ($help, $new, etc...).  
Set a command char with:
> Adv. Settings > Commands

### Logging
If the "Auto-Log" checkbox is checked, everything that appears on the terminal will be written to a log file in the log directory. The log directory defaults to the program's directory.  
The log directory can be changed to anywhere on the user's PC by clicking on:
> Logs > Change Log Dir


Logs can be opened, modified and saved with a simple text editor by clicking "view logs" or by typing the command "logs". 

### Scripts 
A script is an easy way to automate an interface with a device. 

Each new line of the script is run as an input in the "to device" line.

Most devices need time to reply, so a delay between each line can be used. 

Because lines are interpreted as inputs directly on the "send" line, it's also possible to run commands to serial killer (like clearing the terminal, creating new logs, etc)



