# Serial Killer - A killer serial terminal

An open source Serial Terminal, with a host of features for automation and simplicity.

![terminal-example](img/example.png)

Current Features:

- "Command line" style control
  - Quickly connect to a port, clear the terminal or access a number of other features with a handful of commands, entered directly in the output text box.
- Auto-Rescan - Any change in available serial ports is immediately displayed.
- Auto-Reconnect - Reconnect to a port as soon as it appears.
- Auto-Save - User settings are remembered between program loads.
- Text Color Highlighting - Inputs, outputs, etc. are colored differently to make communication clear.
- Logging - All input/output is saved by default to a timestamped log file.
  - Recover data when the terminal is cleared or the program closed.
  - Interleave data from multiple ports at one time.
  - Create custom log formats to export formatted data.
- Custom Single-key press controls
  - Tie single key presses to messages sent to the device.
- Scripting - Automate an interface, run tests or configure the UI with basic scripting files.
  - The K.I.S.S. scripting syntax has a minimal number of features but supports looping, custom arguments, delays, and other commands.
- Plotting - Graph data as it is received.
  - Use custom filters to remove irrelevant data.
  - Set custom plot limits and sizes.
  - Use features built into pyqtgraph to export plot images, transform data, etc.

# Install:

<details open>

Ensure the following packages are installed:

- Pip
- Python > 3.8

Run serial_killer.py from a terminal.  
If imports are unsuccessful, you will be prompted to auto-install packages.

## For Linux

For Linux use, the user needs access to the serial ports. This is done with:

> $ sudo adduser <your_username> dialout

check you are added to the group:

> & groups

Your computer will need to be restarted in order for this change to take effect.

</details>

# Run:

With Python >= 3.8, run `serial_killer.py`

# Usage:

## General

<details open>

### Text

The types of messages that might be shown in the terminal are shown below:

![text_settings](img/text.PNG)

RX (text from a device) text is colored white.  
TX (text to a device) text is colored blue.

The text sent to the device, INFO text, and ERROR text all have optional strings prepended to them. These are not required, but may make logging easier to understand. Customize these strings in the `Settings > Terminal Settings` box. Use the checkboxes to set if each type of text should be included in the terminal or log.

![term_settings](img/terminal-settings.PNG)

### Text TO a device

Use the 'TX' text box at the top of the window both as a way to send text to the device, and as a way to enter commands.

This text is only sent after pressing 'Send' or hitting `ENTER`.

To append a newline or return character (as is common with serial messages) to this text, edit the string defined in `Settings > Append to Send:`. The text here will be appended to everything sent.

![send_settings](img/send-settings.PNG)

Because some characters like `tab` and `newline` cannot be typed with the `TAB` and `ENTER` keys, an option is provided to interpret "\t", "\n", and "\r" in the input with their corresponding control characters. As with other text interpretation, "\\\n", "\\\t", and "\\\r" are replaced with literal \n, \t ,\r.

If enabled, this would mean that:

```
hello\tworld \n i am on a newline \\n i am not
```

is sent as:

```
hello   world
 i am on a newline \n i am not
```

Similarly to shell terminals, the up and down arrows will scroll through the history of commands sent.

### $UTS

I have also included one keyword that will be replaced in input: `$UTS`, which is replaced with the current UNIX timestamp.

```
the unix timestamp is $UTS
```

sends:

```
the unix timestamp is 1647726351
```

</details>

# Commands

<details open>

Commands are typed directly in the "TX" text box, as if they were being sent to the device. They have a command-line style syntax. Arguments and values are separated with spaces.

> TODO: Implement command escape char to prevent conflicts between commands and text to send

The list of commands and their uses are detailed below:


<!-- con -->
## con [port] [options]

Connect to a port (optional: with settings defined in [options]).

If no arguments are provided, the settings in the "Port" box at the bottom of the window are used.

**Options:**

```
*none*              Open the port selected in the port dropdown
[name]              Open port name [portname]
                    Use the full port name or (if on Windows) the com port number.
                    i.e. 'con 3' opens COM3

-b [baud]           Set the baud rate to [baud]
-d                  Enable dsrdtr
-x                  Enable xonxoff
-r                  Enable rts/cts
-p [parity]         Set parity to [parity] (accepts "EVEN", "ODD", "MARK" or "SPACE")
-h                  Show Help Text
```

**Examples**
(assuming ports available are COM1, COM33, and COM50)

Connect to COM33 at 9600 baud:

```
con COM33 -b 9600
```

Connect to COM50 with EVEN parity and rtscts ON.

```
con 50 -p EVEN -r
```
<!-- con -->
---

## dcon

Disconnect from the current port (if connected).

---

## ports [-a]

Show all available ports.

Optional: if argument '-a' is included, additional port information is printed.

---

## clear

Immediately clear the terminal

---

## script [options]

Run, Save or modify a script based on the [options] provided.

If NO options are provided, the script in the script tab is run.

**Options**

```
*none*      Run the script in the script tab
-h          Show help text
-o [name]   Open a script (optional open [name].txt)
            If no [name] is given, a file dialoge will open.
            The script will not run unless '-r' argument is also provided.
-t          Jump to the script tab
-ls         List all scripts
-n [name]   Start a new script (optional [name].txt)
-rm [name]  Remove a script (optional [name].txt)
            If no [name] is given, a file dialoge will open.
-d [delay]  Start the script with delay [delay] (milliseconds)
-a [arg]    Pass argument [arg] into script
```

**Examples**  
Open and run a script named "test".txt:

```
script -o test -r
```

Run the script in the script tab with send delay 500ms and optional argument "hello"

```
script -d 500 -a hello
```

**See scripting syntax section for more information**

---

## log [options]

Open, list or Archive a log

If NO options are provided, the most recent log file is opened.

**options**

```
*none*      open the most recent log file
-h          show help text
-o          open a log from the directory
-a [name]   archive the current log (optional as [name].txt)
-ls         list log files in the log directory
```

**Examples**  
Archive the current log as 'my-log'.txt

```
log -a my-log
```

---

## plot [options]

Start, Modify or Stop a plot.

**options**

```
-h              show help text
-kv             start the plot in key-value mode
-c              clear the plot
-t [targets]    set the plot's target values (comma seperated)
-m              Operate the plot limits in "max" mode. Otherwize "window"
-l [length]     Set the max length of the plot
```

**Examples**  
Start a plot in key-value mode with target keys of "X,Y,Z" and a max length of 100 data points.

```
plot -kv -t X,Y,Z -l 100
```

**See plotting section for more information**

---

## key [options]

Set, or Clear keyboard commands.

To set a key and value, use arguments "-k [key]" and "-v [value]".

**options**

```
*none*          jump to the 'keyboard control' text line
-h              show help text
-k [key]        set the key to [key]
-v [value]      set the value to send to [value]
-c              clear all key-value pairs
```

**Examples**  
Set key '1' to send value 'one'

```
key -k 1 -v one
```

---

## new

Open a new Serial Killer window.

---

## quit (or exit)

Exit Serial Killer immediately.

---

</details>

# Scripts

<details open>

### Syntax

Each line of text in the script tab is evaluated as if it was being typed directly into the terminal and sent.

To allow for a device to reply, a delay (in milliseconds) is set between one send and the next.

**Comments** are designated by text that follows a `//`, much like in javascript or c++.

**Script Commands** are lines that begin with `#`. Multiple commands can appear on the same line, provided that each has a '#' before it. Script commands do not have a delay associated with them, line with regular lines.

These lines can be either serial killer commands (i.e. `#dcon`, `#plot -kv`, etc...) or can be a number of script-specific commands that are detailed below.

### #delay=[delay_time]

This will set the delay between sends to [delayTime] (in milliseconds). This will override any delay time set before it.

### #pause=[pause_time]

This will pause the script for [pause_time] (in milliseconds). It will not change the delay time between sends.

### #info=[info] and #error=[error]

Both these commands print text to the terminal in style INFO and style ERROR.

### #loop

### #loop=[loop_numb]

### #endloop

The `#loop=[numb_loops]` and `#endloop` keywords are meant to signal start and stop of a loop.

If `#loop` is used rather than `#loop=[numb_loops]`, the loop will run indefinitely, so:

The lines in between these keywords will be run [numb_loop] times.

The variable `$LOOP` keeps track of the number of loops executed. This counter starts at 0 and increments by one each loop execution. To use this counter, include `$LOOP` anywhere in the script.

### #end

End the script at this line.

### Examples

A super basic example of sending lines of text to a device after a delay of 50 milliseconds

```
#delay=50
send1
send2
send3
```

After making sure no device is connected, loop through 10 cycles, sending an incrementing number.

```
#dcon #delay=100    // disconnect, set delay to 100 ms
#info=starting loop //
#loop=10            // loop 10 times
slow loop $LOOP
#endloop
//#end              // Uncomment to end here
#pause=1000         // One-Time pause for 1 second
#loop=15 #delay=30  // Loop again, much faster
fast loop $LOOP
#endloop
```

</details>

## Logs

<details open>
</details>

## Plotting

<details open>
</details>

## Keyboard Control

<details open>
</details>

# Possible Future Features / Fixes

### Plots

- Add plot types for parsing and plotting arrays and single variables
- Add flexible input parsing, separators, etc. for plot data.
- Add multiple scale plotting.

### Scripting

- Integrate python scripts directly in the script tab. I have done some experiments using python's eval() and exec() functionality, but I ran into bugs that looked too time consuming to address.

### Serial

- Add encodings other than 'utf-8' for input and output.

### Commands

- Additional Commands for changing settings
- Adding escape character to command parser

## Modification / Under the hood

### GUI

[PyQt5](https://pypi.org/project/PyQt5/) is the framework for GUI development.

Use [QtDesigner](https://doc.qt.io/qt-5/qtdesigner-manual.html) to modify the GUI.

The `.ui` needed for QtDesigner are found in the [/ui_files](/ui_files) folder. These files are translated into python files using the `pyuic5` tool. The outputs of these translations are found in the [/gui](/gui/) folder.

To modify the GUI, do the following steps:

1. Open the .ui file in QtDesigner.
2. Make modifications.
3. Save the file.
4. Update the python files in the /gui folder. This can be done one of two ways:
   - Run Serial Killer with the argument '-u'
     > py serial_killer.py -u
   - OR Update things manually:
     > pyuic5 -o gui/GUI_MAIN_WINDOW.py ui_files/serial_killer_main_window.ui  
     > pyuic5 -o gui/GUI_LOG_POPUP.py ui_files/serial_killer_log_popup.ui  
     > pyuic5 -o gui/GUI_HELP_POPUP.py ui_files/serial_killer_help_popup.ui
5. Run Serial Killer
