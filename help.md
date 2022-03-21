
# Commands

## con [portname] [options]

Connect to a port with settings

**Options:** 
```
*none*              Open the port selected in the port dropdown
[portname]          Open port name [portname] 
                    Use the full port name or (if on Windows) the com port number.
                    i.e. 'con 3' opens COM3 

-b [baud]           Set the baud rate
-d                  Enable dsrdtr
-x                  Enable xonxoff
-r                  Enable rts/cts
-p [parity]         Set parity: 
-h                  Show Help Text
```

## dcon

Disconnect from a port

## script [options]

Run, Save or modify a script

**Options**

```
*none*      Run the script in the script tab
-h          Show help text
-o [name]   Open a script (optional open [name].txt)
-t          Jump to the script tab
-ls         List availiable scripts
-n [name]   Start a new script (optional [name].txt)
-rm [name]  Remove a script (required: [name].txt)
-d [delay]  Start the script with delay [delay] (milliseconds)
-a [arg]    Run the script with argument [a] 
```

## log [options]

Open, list or Archive a log

**options**
```
*none*      open the most recent log file
-h          show help text
-o          open a log from the directory
-a [name]   archive the current log (optional as [name].txt)
-ls         list log files in the log directory
```

## plot [options]

**options**
```
*none*          open the most recent log file
-h              show help text
-kv             start the plot in key-value mode
-c              clear the plot
-t [targets]    set the plot's target values (comma seperated)
-a [name]       archive the current log (optional as [name].txt)
-ls             list log files in the log directory
```



