# Servostat-interface
---

This is the python software for the klavins lab turbidostot (see http://klavinslab.org/hardware for details) with programming contributions from the siegal lab.

## Table of Contents

---
1. [Technical](#technical)
    * [Requirements](#requirements)
    * [Known Issues](#known-issues)
2. [File Overview](#file-overview)
3. [Software Setup](#software-setup)
    * [RPi SSH Access](#raspberrypi-ssh-access)
    * [Running an Experiment](#running-an-experiment)
	* [Primer Auto Guide](#primer_auto-guide)
5. [Hardware Setup](#hardware-setup)

---
## Technical

For now see the official turbidostat page on how to configre. 

### Requirements
* Python 2.7.x
   * Pyserial 2.7: https://pypi.python.org/pypi/pyserial
   * numpy: http://www.numpy.org/
   * pygments: (available through pip)
   * flask (for the plotserver, which plots the experiment in a browser)

To install requirements, run:
```Bash
$ sudo pip install numpy pygments pySerial flask
```

### Known issues
All platforms:
* Not exiting via ctrl-C can leave orphaned threads that may interfere with
later instances of the application, especially on MacOS and nix.

MacOS (and probably linux):
* Pumping volumes that take longer than 'period' seconds to process will result in a negative timer value being set, which in turn causes a timer overflow and the program to sleep for nearly 2^32 seconds (many years).

---
## File Overview

For more information, see [WIKI.MD](https://github.com/Siegallab/Flexostat-interface/blob/master/WIKI.MD)

### Related Files
* servostat.py is the main function to be run in the command line with a config file
    * controller.py contains the code behind the Controller object used in servostat.py
        * mytimer.py is used in controller.py to run time related functions
        * Plugins
          * pumpdriver plugin is called from plugins folder dependant in info provided by config file
            * Use either Cheapopumpdrive or ne500pumdriver
          * controllfun is called from plugins folder dependant in info provided by config file
            * Use either chemostat of turbidostatController/SQ/_SIN (More details later on which does what)
    * The CTBasicServer object defined in network.py is used in servostat.py to create a basic network
    * stacktracer.py is used in servostat.py to create a stack trace as the program runs
    * Outputs data in the log files specified in the Log section of the config file
    * Testing Git Functionality
* optional Block-Dilutions.py runs by crontab, in parallel with the main experiment programs, to allow larger dilutions with longer periods of undisturbed growth ([WIKI.MD](WIKI.MD) for more info)
* optional Growth-Pipe.py calculates growth rates based on OD or U data, calculates summary statistics, produces graphs, and estimates significant changes in growth rate ([WIKI.MD](WIKI.MD) for more info)
* optional Media-Monitor.py runs by crontab, in parallel with main experiment programs, to keep track of media levels and report to experimenters ([WIKI.MD](WIKI.MD) for more info)

---
## Software Setup
### Raspberry Pi SSH Access
To Access the Pi via SSH type the following command into the command line in terminal:
```Shell
* $ ssh pi@framboise0.bio.nyu.edu
```
* when prompted type in the password printed on the Pi.

### Running an Experiment
Make sure you are in the right folder:
```Shell
* $ cd ~/Flexostat-interface
```
Check for existing Log files:
```Shell
* $ ls
```
  * There is data from a previous run if you see:
    * Log.dat (The calculated od measurments based on the blank, times and dilution values)
    * odlog.dat (The rough uninterpreted values for the OD sensors)
    * errors.log (A log of any errors that occured)
    * blank.dat (The base settings established at the begining of a new run. This file will be created if one is not present in the Flexostat-interface folder. If one is present it will be used as a zero baseline of OD measurments.)

Setup for the Run
* If there was previous data:
  * create a new directory in the Data folder to store the data:
```Shell
$ cd Data
$ mkdir *targetdir*
```
  * Change back to the Flexostat-interface directory:
```Shell
$ cd ../
```
  * If you want to add to that data back it up and run the code:
```Shell
$ cp log.dat odlog.dat error.log Data/*targetdir*
$ python servostat.py
```
  * if you want to create new data but with the same zeroed baseline:
```Shell
$ mv log.dat odlog.dat error.log Data/*targetdir*
$ python servostat.py
```
  * if tou want to create new data and a new baseline:
```Shell
$ mv log.dat odlog.dat error.log blank.dat Data/*targetdir*
$ python servostat.py
```
  * to halt the code:
```Shell
ctrl c
```

With screen:
* before you run the code type:
```Shell
$ screen
```
* it wll look almost the same but screen should be running
  * run code normally
* to return to normal terminal:
```Shell
ctrl a d
```
* to return to detached screen window:
```Shell
$ screen -ls
```
* this will show a list of the detached screens you have running
```Shell
$ screen -r *adress of detached screen from list*
ex $ screen -r 2477.pts-0.server1
```
* to halt the code and exit
```Shell
ctrl c
$ exit
```

### Primer_auto guide
Make sure your present working directory is ~/Flexostat-interface. (type pwd in command line)

If it is not type cd ~/Flexostat-interface.

The primer auto has 4 inputs to be put into the command line.

* the language: python
* The script: always Primer_auto.py
* The cylinder you want to dispense into:
  * denote using -s
  * print an integer between 1 and 8
* The volume you want to dispense:
  * denote using -v
  * an integer between 0000 and 2000 always consisting of 4 digits
  * (Printing a value >= 2000 will simply cause the pump to fill fully)
  * ex. to dispense 500ul print 0500

The entire line whould look like:
```Shell
 $ python Primer_auto.py -s # -v ####
 ```

A fifth input is present but does not need to be specified unless specifically needed. This input is the config file that specifies the parameters for the turbidostat to function on. The code is set to use "config.ini" as a default. This file must be in the same folder as the Primer_auto.py script for the code to run.

The code is also directly dependant upon the controller.py script, cheapopumpdriver.py script and a number of imported modules. To avoid issues always run the script in the same directory (Flexostat-interface) as all other flexostat code files. Ensure that all modules imported at the head of the script are installed on the computer being used before running.

The functional commands sent to the board in the code are sent using the line cport.write().

the commands are:
* "clo;" - closes all valves
* "sel#;" - opens one selected valve. (0 is the solenoid, 1-8 are the cylinder valves)
* "pmv####;" - Moves the pump to the specified position between 0 and 2000. To fill the pump a value >0 is used. To empty the pump the command "pmv0000;" is used.

For further questions and troubleshooting see comments in the code.

---
## Hardware Setup

Board Framework Installation

To install the firmware on the boards you must use a PC with the Atmel Studio software installed on it that is connected to the atmel Ice device.

For the OD boards us the 6 pin ISP cable. Plug it to the ICE in the AVR port. Plug it to the board on the group of six pins labeled ISP.

For the Main Board use the same cord plugged into the AVR on the ICE but with the adapted plugged into the midpoint. On the adapter there is a ten pin port labeled AVR JTAG. Plug this into the ten pin group on the main board labelled JTAG.

Follow the installation instructions here: https://depts.washington.edu/soslab/turbidostat/pmwiki/pmwiki.php?n=ConstructionManual.Programming
For issues with the ICE use this guide: http://www.atmel.com/Images/Atmel-42330-Atmel-ICE_UserGuide.pdf
