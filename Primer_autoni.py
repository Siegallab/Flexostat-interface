from numpy import array, ones #Array creates arrays, a data type that is like a more restricted list (https://docs.python.org/2/library/array.html)
                                                                                                    #(https://docs.scipy.org/doc/numpy/reference/generated/numpy.array.html)
                                #Ones creats an array of the specified dimensions full of 1s (https://docs.scipy.org/doc/numpy/reference/generated/numpy.ones.html)

from controller import Controller # Import the Controller object from the controller.py script
from ConfigParser import SafeConfigParser #Configuration file parser (https://docs.python.org/2/library/configparser.html)
from network import CTBasicServer #Import object defined in network.py

import threading #constructs higher-level threading interfaces on top of the lower level thread module. (https://docs.python.org/2/library/threading.html)
import sys #system specific parameters and functions (https://docs.python.org/2/library/sys.html)
import serial #Can't find info online but defintely a thing. Seems to involve the serial input ports. Can't find it being explicitly used though
import traceback # Print or recieve stack traceback (https://docs.python.org/2/library/traceback.html)
import argparse # Parser for command line options (https://docs.python.org/3/library/argparse.html)
import stacktracer # imports all fucntions from stacktracer.py 
import time


debug = False #what does this do

# Add necessary command line arguments
parser = argparse.ArgumentParser(description='Turbidostat controller.') # This section defines the command line inputs
parser.add_argument("-c", "--config_filename", default="config.ini", 
                    help="Where to load configuration from.")# This creates a command line argument c
parser.add_argument("-s", "--cylinder", 
		    help = "Print Which pinch valve you want dispense through (value = 1-8), ex. printing 2 will dispense into cylinder 2")
parser.add_argument("-v", "--volume", 
		    help = "Print the volume you want pumped between 0 - 2000 in the format ####. ex. to pump 500ul print 0500")
args = parser.parse_args()

    # Startup stacktracer for debugging deadlock
stacktracer.trace_start("trace.html", interval=60, auto=True)
    
    # Read configuration from the config file
config = SafeConfigParser()
print 'Reading config file from', args.config_filename
config.read(args.config_filename)
controller_params = dict(config.items('controller'))
port_names = dict(config.items('ports'))
pump_params = dict(config.items('pump'))
logs = dict(config.items('log'))
    
cport = serial.Serial(port_names['controllerport'],
                          int(controller_params['baudrate']),
                          timeout=4,
                          writeTimeout=1)
                             
cport.lock = threading.RLock()
if (port_names['pumpport'].upper()!='NONE'):
	pump_port = serial.Serial(port_names['pumpport'],
                                  int(pump_params['baudrate']),timeout = 1,
                                  writeTimeout = 1)
        pump_port.lock = threading.RLock()
else:
        pump_port = None
pumpdriver_package = 'plugins.%s' % pump_params['pumpdriver'] # should link to cheapopumdriver/ne500pumpdriver plugin in "plugins" folder
        # May have to specify which plugin to be used fro both pumpdriver and controlfun
control_function_package = 'plugins.%s' % controller_params['controlfun'] # should link to turbidostatController/SQ/_SIN plugin in "plugins" folder
        
        # Import pumpdriver
pumpdriver = __import__(pumpdriver_package, globals(), locals(), # import "Pump" function
                        ['Pump'], -1)

# check if a valve was selected, if no valve is selected the code simply closes all valves
vol = 0000
if args.volume:
	with cport.lock:
		cport.write("clo;")
	print "Closing all valves;"  #close valves
	time.sleep(.5)		     #Open solenoid
	with cport.lock:
		cport.write("sel0;")
	print "select 0"
	time.sleep(.5)
	vol = args.volume 		     #if a volume is specified use that volume
	pump = 'pmv' + str(vol) + ';'
	with cport.lock:	
		cport.write(pump)	     #fill pump
	time.sleep(1)
if args.cylinder:
	with cport.lock:
		cport.write("clo;")     #close solenoid
	time.sleep(1)
	cyl = "sel" + args.cylinder + ';'
	print "select valve " + cyl	     #open selected valve
	with cport.lock:
		cport.write(cyl)
	time.sleep(1)
	if args.volume:
		print "Dispensing"	     #incrementally dispense into chosen cylinder
		pump2 = 'pmv0000;'
		with cport.lock:
			cport.write(pump2)
			time.sleep(.5)
		with cport.lock:
			cport.write("clo;")

elif args.cylinder == "0":
	print "Pump filled, choose where to dispense with -v of same volume"
		
#Else command that closes all valves in the case of no cylinder specification
else:
	with cport.lock:
		cport.write("clo;")
	print "Closing all valves;"  #close valves
