"""
BACKGROUND

	Created April 12, 2018
		by David Klein
		contributions found at https://github.com/Siegallab/Flexostat-interface

INSTRUCTIONS

	Run using Python 3 on the command line as such
	$ python3 Experiment-Simulator.py -h
"""
from datetime import datetime
import argparse
import numpy
import os
from configparser import ConfigParser
import time
import json


def main():
	"""
	Defines the command line arguments intaken by the program.
	Ensures there is a config file to work with before calling the 'functions' function.
	"""
	args = command_line_parameters()
	start_time, last_data, last_block = datetime.now(), datetime.now(), datetime.now()
	od_subtraction = numpy.asarray([0.0] * 8)
	try:
		while (datetime.now() - start_time).seconds/60 < float(args.exp_len):
			if (datetime.now() - last_data).seconds >= float(args.data_time):
				od_subtraction = produce_data(args, od_subtraction)
				last_data = datetime.now()
			if (datetime.now() - last_block).seconds >= float(args.block_time):
				analyze_block(args)
				last_block = datetime.now()
			time.sleep(1)
	except KeyboardInterrupt:
		print('Experiment-Simulator.py interrupt.\n')
	print('Experiment-Simulator.py end.\n')


def command_line_parameters():
	"""
	Takes in command line argument parameters and displays help descriptions.

	:return: variable containing all command line argument parameters
	"""
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
					description="""
	Experiment Simulator Program
	----------------------------
	Simply run with the command: python Experiment-Simulator.py
	
	All parameters are optional. 
	Defaults:
		0.4 true growth rate, 0.0005 SD for OD noise, 
		'config.ini' for config file,
		2 second data production, 
		5 second block analysis, 
		2 hour experiment length,
		10 ml chamber volume,
		print is on
	Block Dilution defaults:
		'config.ini' for config file,
		chamber mode,
		print is on
						""")

	parser.add_argument('--rate', default='0.4', help='true growth rate, defaults to 0.4')
	parser.add_argument('--noise', default='0.0005', help='standard deviation of OD noise, defaults to 0.0005')
	parser.add_argument('--data_time', default='2', help='second interval for each data production, defaults to 2 seconds')
	parser.add_argument('--block_time', default='5', help='second interval for each block analysis, defaults to 5 seconds')
	parser.add_argument('--exp_len', default='120', help='real minute length for entire simulated experiment, defaults to 120')
	parser.add_argument('--config', default='config.ini', help='experiment config file, defaults to config.ini')
	parser.add_argument('--print', action='store_false', help='turn off print by using flag, defaults to on')
	parser.add_argument('--chamber', action='store_true', help='use individual chamber OD for dilutions, default mode')
	parser.add_argument('--schedule', action='store_true', help='use interval dilution schedule for dilutions')
	parser.add_argument('--growth', default='0', help="specify 'hour' interval for growth block in schedule mode (default to config file, otherwise 7)")
	parser.add_argument('--dilution', default='0', help="specify 'hour' interval for dilution block in schedule mode (default to config file, otherwise 4)")
	parser.add_argument('--volume', default='10', help='specify ml chamber volume for negative growth from dilution, defaults to 10ml')
	
	args = parser.parse_args()
	return args


def produce_data(args, od_subtraction):
	"""
	Generate OD and U data as if from a normal experiment run.

	:param args: command line arguments for program
	:param od_subtraction:
	:return: value to subtract from next OD
	"""
	# read in the config file variables
	config = ConfigParser()
	config.read(args.config)
	controller = dict(config.items('controller'))
	setpoints = list(map(float, controller['setpoint'].split()))
	log = dict(config.items('log'))

	# if no log of data exists, then create the first line with a little density
	if not os.path.exists(log['fulllog']):
		dlog = {"timestamp": int(round(time.time())), "ods": [0.01] * 8, "u": [0] * 8}
		logfile = open(log['fulllog'], 'a')
		log_str = json.dumps(dlog)
		logfile.write('%s\n' % log_str)
		logfile.close()
		od_subtraction = numpy.asarray([0.0] * 8)

	# read in the log data and save the variables from the last line
	logfile = open(log['fulllog'], 'r')  # open input file
	logdata = logfile.readlines()
	logfile.close()
	last_line = logdata[-1]
	if len(last_line) < 1:
		last_line = logdata[-2]
	last_line = json.loads(last_line)
	timestamp = last_line['timestamp']
	latest_OD = numpy.asarray(last_line['ods'])
	try:
		zs = numpy.asarray(last_line['z'])
	except:
		zs = [None] * len(latest_OD)

	# simulate OD with some noise based on the last reading
	true_GR = float(args.rate) * (int(controller['period']) / 3600)
	true_OD = latest_OD * numpy.exp(true_GR - od_subtraction) 
	OD_noise = numpy.random.normal(0, float(args.noise), (len(latest_OD),)) #pylint: disable=E1101
	# no noise will be implemented if the noise will prevent growth
	for chamber in range(len(latest_OD)):
		if (true_OD[chamber] - latest_OD[chamber]) <= float(args.noise):
			OD_noise[chamber] = 0
	observed_OD = true_OD + OD_noise

	# compute the U and Z values based on OD
	out_us, out_zs = [], []
	for chamber in range(len(observed_OD)):
		temp_u, temp_z = computeControl(observed_OD, zs, controller, setpoints, chamber)
		out_us.append(temp_u)
		out_zs.append(temp_z)

	# calculate value to subtract from next OD
	for chamber in range(8):
		if out_us[chamber] > 0:
			od_subtraction[chamber] = numpy.log(int(args.volume)/ (int(args.volume) + (out_us[chamber]/100))) #pylint: disable=E1101
			#od_subtraction[chamber] = (6.23661e-05 * out_us[chamber]) + 0.001339 # calculate linear od change
		else:
			od_subtraction[chamber] = 0.0

	# write line of data to full log file
	time_secs = timestamp + int(controller['period'])
	dlog = {'timestamp': time_secs, 'ods': [round(od, 4) for od in observed_OD],
	        'u': out_us, 'z': [str(z) for z in out_zs]}
	log_str = json.dumps(dlog)
	if args.print:
		print(log_str)
	logfile = open(log['fulllog'], 'a')
	logfile.write('%s\n' % log_str)
	logfile.close()

	return od_subtraction


def computeControl(ods, zs, controller, setpoints, chamber):
	"""
	Computes U and Z values for OD values based on setpoints.
	This method is based off the turbidostatController.py method.

	:param ods: currently observed OD
	:param zs: previously reported Z values
	:param controller: config file variables
	:param setpoints: current setpoints from config file
	:param chamber: current chamber
	:return: computed U and Z value for chamber
	"""
	z = zs[chamber]
	if z == None:
		z = 90
	z = float(z)

	err_sig = 1000 * (ods[chamber] - setpoints[chamber])
	z = z + err_sig * float(controller['ki'])
	if z < 0:
		z = 0
	if z > float(controller['maxdilution']):
		z = float(controller['maxdilution'])

	u = z + err_sig * float(controller['kp'])
	if u < float(controller['mindilution']):
		u = float(controller['mindilution'])
	if u > float(controller['maxdilution']):
		u = float(controller['maxdilution'])
	u = int(u) # make sure u is an int

	return u, z


def analyze_block(args):
	"""
	Run the Block-Dilutions.py program with specific inputs.

	:param args: command line arguments for program
	"""
	if args.schedule:
		command = "python2.7 Block-Dilutions.py --config {} --out --schedule".format(args.config)
	else:
		command = "python2.7 Block-Dilutions.py --config {} --out --chamber".format(args.config)
	if float(args.growth) > 0:
		command += " --growth {}".format(args.growth)
	if float(args.dilution) > 0:
		command += " --dilution {}".format(args.growth)
	os.system(command)


main()