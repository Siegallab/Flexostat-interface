from controller import Controller # Import the Controller object from the controller.py script
from ConfigParser import SafeConfigParser #Configuration file parser (https://docs.python.org/2/library/configparser.html)
from network import CTBasicServer #Import object defined in network.py

import argparse # Parser for command line options (https://docs.python.org/3/library/argparse.html)
import serial   # #Can't find info online but defintely a thing. Seems to involve handleing the serial input ports.
import stacktracer # imports all fucntions from stacktracer.py (
import sys #system specific parameters and functions (https://docs.python.org/2/library/sys.html)
import threading #constructs higher-level threading interfaces on top of the lower level thread module. (https://docs.python.org/2/library/threading.html)
import time #Time access and conversions (https://docs.python.org/2/library/time.html)
import traceback # Print or recieve stack traceback (https://docs.python.org/2/library/traceback.html)


def Main():
    parser = argparse.ArgumentParser(description='Turbidostat controller.') # This section defines the command line inputs
    parser.add_argument("-c", "--config_filename", default="config.ini", # This creates a command line argument c
                        help="Where to load configuration from.")
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

    # Open ports
    cont_port = serial.Serial(port_names['controllerport'],
                              int(controller_params['baudrate']),
                              timeout=4,
                              writeTimeout=1)
    cont_port.lock = threading.RLock()
    if (port_names['pumpport'].upper()!='NONE'):
        pump_port = serial.Serial(port_names['pumpport'],
                                  int(pump_params['baudrate']),timeout = 1,
                                  writeTimeout = 1)
        pump_port.lock = threading.RLock()
    else:
        pump_port = None
    
    # Make and start the controler
    cont = Controller(controller_params, logs, pump_params,
                      cont_port, pump_port, args.config_filename)
    cont.start()
    
    # Setup network configue port
    def cb(cmd):
        if 'list' in cmd:
            return str(controller_params)
    netserv = CTBasicServer(('', int(port_names['network'])), cb)
    netserv.start()
    
    print 'num threads: ' + str(len(sys._current_frames().keys()))
    # Run until a keyboard interrupt.
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print 'shutting down'
        cont.quit()
        time.sleep(1.1)


if __name__ == '__main__':
    Main()
