

# Install: 
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

The machine will need to be restarted in order for this change to take effect.

# Run: 

With Python >= 3.8, run `serial_killer.py`  

# Useage:

> TODO: Write This. 

# Modification / Under the hood

## GUI

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

