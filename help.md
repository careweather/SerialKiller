## SERIAL KILLER QUICK HELP
More full documentation is avaliable in the github repo linked below. 

Certain functions are accessable via "terminal style" commands.  
Enter the keyword directly into the "To Device" text box. 
### TERMINAL COMMANDS:  
|Key|Function|Args|Example|
|:-------------:|:-------------:|:----------:|:---:|
|help|open this help window| none | >> help
|con|connect to the port selected|none | >>con
|dcon|disconnect|none | >>dcon
|clear|clear terminal text|none | >>clear
|script|run the script in script tab|-o open -s save -[name] run "name"|>>script -example
|quit|close the program immediately|none |
|save|save current configuration|none |
|new|open a new window|none |
|log|open the latest log|-l open latest. -n start new.|
|scan|rescan for Serial Ports|none |
|auto|toggle auto-reconnect|none |
|com*|open com port (*) if it's avaliable|none |
|baud*|change baud rate to (*)|none |


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



