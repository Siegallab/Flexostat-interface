# Servostat-interface
---

This is the python software for the klavins lab turbidostot (see http://klavinslab.org/hardware for details) with programming contributions from the siegal lab.

## Table of Contents

---
1. [Technical](#technical)
    * [Requirements](#requirements)
    * [Configuration](#configuration)
    * [Known Issues](#known-issues)
    * [TODO](#todo)
		* [Controller](#controller-todo)
        * [Growth Rate Pipeline](#growth-rate-pipeline-todo)
		* [Media Monitoring](#media-monitoring-todo)
		* [Future](#future-todo)
2. [File Overview](#file-overview)
3. [Up and Running](#up-and-running)
    * [RPi SSH Access](#raspberrypi-ssh-access)
    * [Running an Experiment](#running-an-experiment)
    * [Git](#git)
4. [Files In-depth](#files-in-depth)
    * [Primer_auto Guide](#primer_auto-guide)
    * [Flexoparser_csv Guide](#flexoparser_csv-guide)
	* [Growth-Pipe Guide](#growth-pipe-guide)
	* [Block-Dilutions Guide](#block-dilutions-guide)
	* [Media-Monitor Guide](#media-monitor-guide)
5. [Hardware Setup](#hardware-setup)
    * [RPi Setup Guide](#raspberry-pi-settup-guide)
    * [Board Framework Installation](#board-framework-installation)
6. [Contributors](#contributors)

---
## Technical
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

### Configuration
For now see the official turbidostat page.

### Known issues
All platforms:
* Not exiting via ctrl-C can leave orphaned threads that may interfere with
later instances of the application, especially on MacOS and nix.

MacOS (and probably linux):
* Pumping volumes that take longer than 'period' seconds to process will result in a negative timer value being set, which in turn causes a timer overflow and the program to sleep for nearly 2^32 seconds (many years).

### TODO
#### Controller TODO
	- [ ] Test run with new changes
#### Growth Rate Pipeline TODO
1. Implement blocking
	- [x] a. allow stats to be analyzed into blocks
	- [x] b. implement for both schedule and chamber-by-chamber
2. Significance calculations
	- [ ] a. stats calculate significant growth rate change
3. Debugging
	- [x] a. stable build
	- [ ] b. data (simulated or real) run
#### Media Monitoring TODO
1. Main functionality
	- [x] a. calculate remaining percentage and amount of media
    - [x] b. ability to notify experimenters
2. Debugging
	- [x] a. stable build
	- [ ] b. data (simulated or real) run
#### Future TODO
This is a list of ideas thought about as ways to improve the turbidostat programs. These are non-essential and non-priority but may be convenient or useful for certain experiments.
1. Predictive Analysis
	- [ ] a. predictive stats based on researcher parameters
    - [ ] b. compare theoretical stats with experimental
2. Data Presentation
	- [ ] a. multiple data sets on a single graph

---
## File Overview
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
* optional Block-Dilutions.py runs by crontab, in parallel with the main experiment programs, to allow larger dilutions with longer periods of undisturbed growth
* optional Growth-Pipe.py calculates growth rates based on OD or U data, calculates summary statistics, produces graphs, and estimates significant changes in growth rate
* optional Media-Monitor.py runs by crontab, in parallel with main experiment programs, to keep track of media levels and report to experimenters

---
## Up and Running
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

### Git
Whenever changes are made either on the pi, on your computer or on git directly, make sure to update all pertinent repositories.

Change to the right folder:
```Shell
$ cd Flexostat-interface
```

always start with:
```Shell
$ git init
$ git pull
```

If you make a change on the PI or your computer that is linked to git:
* If you add a new file or folder or alter a file:
```Shell
$ git add --all
$ git commit -m "*Comment*"
$ git push
```
* Type in username an password when prompted

* If you have new data you want to push to git:
```Shell
$ cd Data/*data directory*
$ git add -f --all
$ git commit -m "*Comment*"
$ git push
```
* Type in username an password when prompted

* If changes have been made on github:
```Shell
$ git pull
```

* To view you git configuration settings:
```Shell
$ git config --list
```
* To view commands that can be used to alter config settings:
```Shell
$ git config
```
* To view and change origin url:
```Shell
$ git remote -v
$ git remote set-url *siteurl*
```

---
## Files In-depth
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

### Flexoparser_csv guide
[Flexoparser_csv](legacy_and_extra/Flexoparser_csv.py) has 2 mandatory arguments and 3 optional arguments:

* -i The input file. Must be log.dat output file. The file must be in the same directory as the code or the line must explicity direct to the location of the file.
* -f The output filename you want. This filename provided will be followed by _OD, _U and _Z for each of the respective outputs. If you want it to output it in a specific directory you must explicity describe it.
* -o Which types of value you want ouputed, Either od, u, z or all. The default is all
* -b A machine time at which you want to start parsing the data. Default is the start of the file
* -e A machine time at which you want to stop parsing the file. Default is the end of the file.

A standard command line prompt without the optional inputs should look like:
```Shell
$ python Flexoparser_csv.py -i ~/Flexostat-interface/Data/log.dat -f ~/Flexostat-interface/Data/test_data
```

A standard command line prompt with the optional inputs that will output just od values from time: 1493413783-14934549836 should look like:
```Shell
$ python Flexoparser_csv.py -i ~/Flexostat-interface/Data/log.dat -f ~/Flexostat-interface/Data/test_data -o od -b 1493413783 -e 14934549836
```

### Growth-Pipe Guide
For a video explaining Growth-Pipe and Block-Dilutions please refer to [David's website.](http://www.kleinjdavid.com/research#growth-rate-analysis)

The pipeline is made to deal with a wide variety of data based on dilution (u) or optical density (od). The functions include **parsing** the data from the full log or od log file made by the main flexostat experiment, calculating the **growth rates**, calculating general **statistics** on either the parsed data or the growth rate data, calculating general statistics on **blocks** from the Block-Dilutions.py output, and **graphing** any data set. All paths and filenames need to be specified in the *config-growth.csv* file then all functions can be run from a single command line input. This allows for easy scheduling of this pipeline through crontab as the main flexostat experiment continuously updates the full log or od log file from which this pipeline feeds from.
![Directories](/explanations/directories.png)
The Growth-Pipe.py program will import from and export to two lower directories (Data and Experiment). The names of these two directories and all import and export files are specified within the *config-growth.csv* file. This config file exists in the same directory as the Growth-Pipe program. **Do not** change the *variable* columns in the config file. **Do** include all file extensions.

Run this pipeline using **Python 3**. The order of arguments on the command line does not matter.

Running this code through the command line will generate an explanation of all functions of the pipeline and the arguments they allow as input.
```Shell
$ python3 Growth-Pipe.py -h
```
Running this code will generate all the data and statistics for dilutions (u) and optical density (od). *--parse* will parse the u and od data from the full log file, *--growth* will analyze the growth rates for both u and od, *--stats* will calculate mean, standard deviation, and standard error for the growth data.
```Shell
$ python3 Growth-Pipe.py --parse u od --growth u od --stats u_growth od_growth
```
If you already had the optical density growth rates but wanted to calculate statistics for them every 30 minutes as opposed to the default hour intervals, you would use the *--interval* flag and specify an hour multiplier as such.
```Shell
$ python3 Growth-Pipe.py --stats od --interval 0.5
```
The *--graph* function for graphing data allows you to specify any data set. You can specify x and y limits as well as error bars based on either standard deviation (*--sd*) or standard error (*--se*). This code below will generate graphs for hours 0 to 5 based on dilution growth rate data and optical density growth rate data, using standard error for the error bars.
```Shell
$ python3 Growth-Pipe.py --graph u_growth od_growth --xlim 0-5 --se
```

### Block-Dilutions Guide
For a video explaining Growth-Pipe and Block-Dilutions please refer to [David's website.](http://www.kleinjdavid.com/research#growth-rate-analysis)

The program is meant to change the *config.ini* file that is continually read by the experiment Controller program in order for large dilutions to occur in the experiment and give wide ranges between which the cell cultures can grow without dilutions. The program can either be run where each chamber's variables in the *config.ini* file are changed depending on their current ODs or where all chambers' variables in the *config.ini* file are changed together after specific intervals of time. The program allows for easy scheduling of how often to check the OD and/or interval status through crontab.
![Blocks](/explanations/blocks.png)
The program reads in OD data from either the *odlog.dat* and *blank.dat* or *log.dat* files, as well as the set point variables for each chamber from the *config.ini* file, and reports in the *block.log* file when individual chambers have reached their set points. Depending on if the program is set to run based on individual chambers or all together on a scheduled interval, the program will update variables in the *config.ini* file appropriately and report these changes in the *block.log* file.

Run this pipeline using **Python 2.7**. The order of arguments on the command line does not matter.

Running this code through the command line will generate an explanation of all functions of the program.
```Shell
$ python2.7 Block-Dilutions.py -h
```
Run large dilutions on a schedule together with the *--schedule* command, as shown. By default the program will take the time interval from the *config.ini* and if there is none it will take 1 hour. To set the time interval and update the config variable use *--interval* followed by an hour unit. Below we are setting the interval to 5 hours. It is recommended to delay the first run of the program by a few minutes using the *--delay* as such. Below we set the delay to 10 minutes.
```Shell
$ python2.7 Block-Dilutions.py --schedule --interval 5 --delay 10
```
Run large dilutions on a chamber by chamber basis based on their individual ODs with the *--chamber* command, as shown. By default, the program reads from *config.ini* for information on where other files are located and for set point information. To change this use the *--config* command. Below we use the *exp-10.ini* file instead. Any updates reported to the *block.log* file by the program can also be printed out using the *--out* command like such.
```Shell
$ python2.7 Block-Dilutions.py --chamber --config exp-10.ini --out
```
### Media-Monitor Guide
This program is meant to monitor the media levels of the experiment. You initialize the program with a starting amount of media using *--start*, then the *media.log* file will be read in or created if it doesn't exist (change the name with *--log*) along with the *config.ini* file for the main experiment (edit this input name with *--config*). The program is best run using crontab. There are four ways to specify when to report the media level and percent, and three ways to communicate the report (text and email require setting up in the code).

![Monitor](/explanations/monitor.png)

Run this pipeline using **Python 3**. The order of arguments on the command line does not matter.

Running this code through the command line will generate an explanation of all functions of the program.
```Shell
$ python3 Media-Monitor.py -h
```

Below is an example of how to start running the program in crontab. The starting amount of 450ml is specified using *--start 450*. Every 2 hours it will check the media and report when the media has reached 25% of the starting amount using *--percent 25*, when the media only has 50ml left using *--limit 50*, and every time 100ml of media is used using *--amount 100*. You can also set the program to report every time it runs using *--report*. This run will email the reports to yourEmail@gmail.com using *--email yourEmail@gmail.com*.
```Shell
$ 0 2 * * * python3 Media-Monitor.py --start 450 --percent 25 --limit 50 --email yourEmail@gmail.com
```

---
## Hardware Setup
### Raspberry pi settup guide
Initial Configuration
* First, follow the practical steps in the guide provided with the Pi.
* Make sure the sd card is inserted and connect ethernet.
* Connect the Pi using the HDMI cable to the monitor and connect a mouse and Keyboard via usb.
* In the initial configuration screen, under advance options make sure SSH, SPI and Serial are enabled.
* Setup your username and password.
* Select Finish and reboot Pi


For any other setup needs see: https://www.raspberrypi.org/documentation/setup/


The Code
* install git:
```Shell
$ sudo apt-get install git
```
* initialize git:
```Shell
$ git init
```
* Clone the Flexostat Repository:
```Shell
$ git clone https://github.com/Siegallab/Flexostat-interface
```
Modules
* boot up terminal
* Install require modules using the line:
  * $ sudo pip install numpy pygments pySerial flask
* if when code is run the error message shows **modulename** not found run:
  * $ sudo pip install **modulename**
  * run this for any an all modules not found when running the code until the code runs or a module unrelated error shows

Board Framework Installation

To install the firmware on the boards you must use a PC with the Atmel Studio software installed on it that is connected to the atmel Ice device.

For the OD boards us the 6 pin ISP cable. Plug it to the ICE in the AVR port. Plug it to the board on the group of six pins labeled ISP.

For the Main Board use the same cord plugged into the AVR on the ICE but with the adapted plugged into the midpoint. On the adapter there is a ten pin port labeled AVR JTAG. Plug this into the ten pin group on the main board labelled JTAG.

Follow the installation instructions here: https://depts.washington.edu/soslab/turbidostat/pmwiki/pmwiki.php?n=ConstructionManual.Programming
For issues with the ICE use this guide: http://www.atmel.com/Images/Atmel-42330-Atmel-ICE_UserGuide.pdf

---
## Contributors
* Siegal Lab
    * [Maxwell Raderstorf](https://github.com/maxstorf)
    * [David Klein](https://github.com/KEYS248)
