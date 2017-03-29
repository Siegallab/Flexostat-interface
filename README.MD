Servostat-interface
============

This is the python software for the klavins lab turbidostot (see http://klavinslab.org/hardware for details)

Requirements
------------
* Python 2.7.x
   * Pyserial 2.7: https://pypi.python.org/pypi/pyserial
   * numpy: http://www.numpy.org/
   * pygments: (available through pip)
   * flask (for the plotserver, which plots the experiment in a browser)

To install requirements, run:
$ sudo pip install numpy pygments pySerial flask


Configuration
------------------

For now see the official turbidostat page.


Known issues
-------------
All platforms:
* Not exiting via ctrl-C can leave orphaned threads that may interfere with 
later instances of the application, espeically on MacOS and *nix.

MacOS (and probably linux):
* Pumping volumes that take longer than 'period' seconds to process will result in a negative timer value being set, which in turn causes a timer overflow and the program to sleep for nearly 2^32 seconds (many years).

Related Files
-------------------
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

Primer_auto guide
-------------------

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

python Primer_auto.py -s # -v ####

A fifth input is present but does not need to be specified unless specifically needed. This input is the config file that specifies the parameters for the turbidostat to function on. The code is set to use "config.ini" as a default. This file must be in the same folder as the Primer_auto.py script for the code to run.

The code is also directly dependant upon the controller.py script, cheapopumpdriver.py script and a number of imported modules. To avoid issues always run the script in the same directory (Flexostat-interface) as all other flexostat code files. Ensure that all modules imported at the head of the script are installed on the computer being used before running.

The functional commands sent to the board in the code are sent using the line cport.write().

the commands are:
* "clo;" - closes all valves
* "sel#;" - opens one selected valve. (0 is the solenoid, 1-8 are the cylinder valves)
* "pmv####;" - Moves the pump to the specified position between 0 and 2000. To fill the pump a value >0 is used. To empty the pump the command "pmv0000;" is used.

For further questions and troubleshooting see comments in the code.
