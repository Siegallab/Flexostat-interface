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
* servostat.py is the main function to be run
    * controller.py contains the code behind the Controller object used in servostat.py
        * mytimer.py is used in controller.py to run time related functions
        * Plugins
          * pumpdriver plugin is called from plugins folder dependant in info provided by config file
            * Use either Cheapopumpdrive or ne500pumdriver
          * controllfun is called from plugins folder dependant in info provided by config file
            * Use either chemostat of turbidostatController/SQ/_SIN (More details later on which does what)
    * The CTBasicServer object defined in network.py is used in servostat.py to create a basic network
    * stacktracer.py is used in servostat.py to create a stack trace as the program runs
    
    
