## SERIAL KILLER QUICK HELP
More full documentation is avaliable in the github repo linked below. 

Certain functions are accessable via "terminal style" commands.  
Enter the keyword directly into the "To Device" text box. 
### TERMINAL COMMANDS:  
| key | Args | Function | Example |
|---|---|---|---|
| help | (none) | open help | help |
| con | (none) | connect to the selected port | con |
| dcon | (none) | disconnect from the selected port | dcon |
| clear | (none) | clear the terminal | clear |
| script | (none)<br>-[name]<br>-o<br>-s<br>-s<br>-t<br>-h | run the script in the script tab<br>run "name".txt (if it exists in the script dir)<br>open and run a file from the script dir<br>save the current script as ... <br>save the current script as "name".txt<br>jump to the script editor<br>print script help | script<br>script -example   <br>script -o<br>script -s <br>script -s -example<br>script -t<br>script -h |
| log | (none)<br>-o<br>-n<br>-h | open the latest log file<br>open |  |
| auto | (none) | toggle auto reconnect | auto |
| scan | (none) | scan/display open ports | scan |
| com | [port#] | connect to com"port#" | com20 |
| baud | [baud] | change baud rate to "baud" | baud9600 |
| new | (none) | open another instance of Serial Killer | new |
| quit | (none) | close the program | quit |

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



