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
        * [Growth Rate Pipeline](#growth-rate-pipeline-todo)
		* [Large Dilution Pipeline](#large-dilution-pipeline-todo)
		* [Media Monitoring](#media-monitoring-todo)
		* [Analysis](#analysis-todo)
		* [Organization](#organization-todo)
2. [File Overview](#file-overview)
3. [Up and Running](#up-and-running)
    * [RPi SSH Access](#raspberrypi-ssh-access)
    * [Running the Code](#running-the-code)
    * [Git](#git)
4. [Files In-depth](#files-in-depth)
    * [Primer_auto Guide](#primer_auto-guide)
    * [Flexoparser_csv Guide](#flexoparser_csv-guide)
	* [growth-pipe Guide](#growth-pipe-guide)
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
$ sudo pip install numpy pygments pySerial flask

### Configuration
For now see the official turbidostat page.

### Known issues
All platforms:
* Not exiting via ctrl-C can leave orphaned threads that may interfere with
later instances of the application, especially on MacOS and nix.

MacOS (and probably linux):
* Pumping volumes that take longer than 'period' seconds to process will result in a negative timer value being set, which in turn causes a timer overflow and the program to sleep for nearly 2^32 seconds (many years).

### TODO
#### Growth Rate Pipeline TODO
1. Figure out implementation
    - [x] a. allow for easy user and automated use
    - [x] b. csv config file for defining file paths
    - [x] c. integrate flexoparser csv file functions
2. Crontab automation
    - [x] a. test and debug
3. Log file
    - [x] a. save and/or print program processes
4. Growth rate analysis
    - [x] a. analyze OD growth rates from flexoparsed files
    - [x] b. analyze U growth rates
    - [x] c. deal with math error causing input
    - [x] d. test, final debug, and stable build
5. Mean, SD, SE
    - [x] a. calculate stats for growth rates
    - [x] b. test and finish stable build
    - [x] c. fix nan's dropping stats
    - [x] d. time interval control
    - [x] e. stats for OD and U
6. Data presentation
    - [x] a. graphs for OD, U, R-OD, R-U, R-OD stats, R-U stats
    - [x] b. x and y lim
    - [ ] c. multiple data sets on a single graph
#### Large Dilution Pipeline TODO
1. Main functionality
	- [ ] a. allow dynamic config variable changes
    - [ ] b. ensure flexostat files can update variables
    - [ ] c. software and hardware test, debug, and stable build
2. Statistics
	- [ ] a. way to document time intervals of dilution
    - [ ] b. automated blocking of growth intervals
    - [ ] c. stats and graphs
#### Media Monitoring TODO
1. Main functionality
	- [ ] a. calculate remaining percentage and amount of media
    - [ ] b. notify experimenters
#### Analysis TODO
1. Significance Calculation
	- [ ] a. percent change
	- [ ] b. statistical significance
	- [ ] c. output graphs
	- [ ] d. implement functionality in previous pipelines
2. Predictive Analysis
	- [ ] a. predictive stats based on parameters
    - [ ] b. compare stats with experimental
    - [ ] c. output status report
    - [ ] d. output graphs
#### Organization TODO
1. GitHub
	- [ ] a. organize github files
    - [ ] b. update and simplify README

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

---
## Up and Running
### Raspberry Pi SSH Access
To Access the Pi via SSH type the following command into the command line in terminal:

* $ ssh pi@framboise0.bio.nyu.edu

* when prompted type in the password printed on the Pi.

### Running the Code
Make sure you are in the right folder:
* $ cd ~/Flexostat-interface
Check for existing Log files:
* $ ls
  * There is data from a previous run if you see:
    * Log.dat (The calculated od measurments based on the blank, times and dilution values)
    * odlog.dat (The rough uninterpreted values for the OD sensors)
    * errors.log (A log of any errors that occured)
    * blank.dat (The base settings established at the begining of a new run. This file will be created if one is not present in the Flexostat-interface folder. If one is present it will be used as a zero baseline of OD measurments.)

Setup for the Run
* If there was previous data:
  * create a new directory in the Data folder to store the data:
    * $ cd Data
    * $ mkdir *targetdir*
  * Change back to the Flexostat-interface directory:
    * $ cd ../
  * If you want to add to that data back it up and run the code:
    * $ cp log.dat odlog.dat error.log Data/*targetdir*
    * $ python servostat.py
  * if you want to create new data but with the same zeroed baseline:
    * $ mv log.dat odlog.dat error.log Data/*targetdir*
    * $ python servostat.py
  * if tou want to create new data and a new baseline:
    * $ mv log.dat odlog.dat error.log blank.dat Data/*targetdir*
    * $ python servostat.py
  * to halt the code:
    * ctrl c


With screen:
* before you run the code type:
  * $ screen
    * it wll look almost the same but screen should be running
  * run code normally
* to return to normal terminal:
  * ctrl a d
* to return to detached screen window:
  * $ screen -ls
    * this will show a list of the detached screens you have running
  * $ screen -r *adress of detached screen from list*
    * ex $ screen -r 2477.pts-0.server1
* to halt the code and exit
  * ctrl c
  * $ exit

### Git
Whenever changes are made either on the pi, on your computer or on git directly, make sure to update all pertinent repositories.

Change to the right folder:
* $ cd Flexostat-interface

always start with:
* $ git init
* $ git pull

If you make a change on the PI or your computer that is linked to git:
* $ If you add a new file or folder or alter a file:
  * $ git add --all
  * $ git commit -m "*Comment*"
  * $ git push
    * $ Type in username an password when prompted

* $ If you have new data you want to push to git:
  * $ cd Data/*data directory*
  * $ git add -f --all
  * $ git commit -m "*Comment*"
  * $ git push
    * $ Type in username an password when prompted

* If changes have been made on github:
  * $ git pull

* To view you git configuration settings:
  * $ git config --list
* To view commands that can be used to alter config settings:
  * $ git config
* To view and change origin url:
  * $ git remote -v
  * $ git remote set-url *siteurl*

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

 $ python Primer_auto.py -s # -v ####

A fifth input is present but does not need to be specified unless specifically needed. This input is the config file that specifies the parameters for the turbidostat to function on. The code is set to use "config.ini" as a default. This file must be in the same folder as the Primer_auto.py script for the code to run.

The code is also directly dependant upon the controller.py script, cheapopumpdriver.py script and a number of imported modules. To avoid issues always run the script in the same directory (Flexostat-interface) as all other flexostat code files. Ensure that all modules imported at the head of the script are installed on the computer being used before running.

The functional commands sent to the board in the code are sent using the line cport.write().

the commands are:
* "clo;" - closes all valves
* "sel#;" - opens one selected valve. (0 is the solenoid, 1-8 are the cylinder valves)
* "pmv####;" - Moves the pump to the specified position between 0 and 2000. To fill the pump a value >0 is used. To empty the pump the command "pmv0000;" is used.

For further questions and troubleshooting see comments in the code.

### Flexoparser_csv guide
Flexoparser_csv has 2 mandatory arguments and 3 optional arguments:

* -i The input file. Must be log.dat output file. The file must be in the same directory as the code or the line must explicity direct to the location of the file.
* -f The output filename you want. This filename provided will be followed by _OD, _U and _Z for each of the respective outputs. If you want it to output it in a specific directory you must explicity describe it.
* -o Which types of value you want ouputed, Either od, u, z or all. The default is all
* -b A machine time at which you want to start parsing the data. Default is the start of the file
* -e A machine time at which you want to stop parsing the file. Default is the end of the file.

A standard command line prompt without the optional inputs should look like:

$ python Flexoparser_csv.py -i ~/Flexostat-interface/Data/log.dat -f ~/Flexostat-interface/Data/test_data

A standard command line prompt with the optional inputs that will output just od values from time: 1493413783-14934549836 should look like:

$ python Flexoparser_csv.py -i ~/Flexostat-interface/Data/log.dat -f ~/Flexostat-interface/Data/test_data -o od -b 1493413783 -e 14934549836

### Growth-Pipe Guide
The pipeline is made to deal with dilution (u) or optical density (od) data. The functions include **parsing** the data from the *log.dat* file made by the flexostat experiment, calculating the **growth rates**, calculating general **statistics** on either the parsed data or the growth rate data, and **graphing** any of the below data sets. All paths and filenames need to be specified in the *config-growth.csv* file then all functions can be run from a single command line input. This allows for easy scheduling of this pipeline through crontab as the main flexostat experiment continuously updates the *log.dat* file from which this pipeline feeds from.

Run this pipeline using **Python 3**. The order of arguments on the command line does not matter.

Running this code through the command line will general an explanation of all functions of the pipeline.
```Shell
$ python3 growth-pipe.py -h
```
Running this code will generate all the data and statistics for dilutions (u) and optical density (od). The flags *--u* and *--od* tell the program to analyze both sets of data. *--parse* will parse the u and od data from the *log.dat* file, *--stats* will calculate mean, standard deviation, and standard error for this data, *--rate* will analyze the growth rates for both u and od, and *--r_stats* will calculate the mean, standard deviation, and standard error for the growth rate data.
```Shell
$ python3 growth-pipe.py --u --od --parse --stats --rate --r_stats
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
  * $ sudo apt-get install git
* initialize git:
  * $ git init
* Clone the Flexostat Repository:
  * $ git clone https://github.com/Siegallab/Flexostat-interface

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
