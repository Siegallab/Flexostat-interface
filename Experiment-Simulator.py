
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
	start_time = datetime.now()
	last_time = datetime.now()
	od_subtraction = numpy.asarray([0.0] * 8)
	try:
		while (last_time - start_time).seconds/60 < float(args.exp_len):
			now_time = datetime.now()
			diff = (now_time - last_time).seconds/60
			if diff >= float(args.data_time):
				od_subtraction = produce_data(args, od_subtraction)
			#if diff >= float(args.block_time):
			#	analyze_block(args)
			last_time = now_time
			time.sleep(3)
	except KeyboardInterrupt:
		print('Program end.\n')


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
	
	All parameters are optional. These are the defaults:
		0.4 true growth, 20 SD for OD noise, 'config.ini' for config file
		0.05 minute (3 second) data production, 0.1 minute (18 second) block analysis, 2 hour experiment length
		print is on
						""")

	parser.add_argument('--growth', default='0.4', help='true growth rate, defaults to 0.4')
	parser.add_argument('--noise', default='0.002', help='standard deviation of OD noise, defaults to 0.002')
	parser.add_argument('--data_time', default='0.05', help='minute interval for each data production, defaults to 0.05 (3 seconds)')
	parser.add_argument('--block_time', default='0.1', help='minute interval for each block analysis, defaults to 0.1 (18 seconds)')
	parser.add_argument('--exp_len', default='120', help='minute length for entire simulated experiment, defaults to 120')
	parser.add_argument('--config', default='config.ini', help='experiment config file, defaults to config.ini')
	parser.add_argument('--print', action='store_false', help='turn off print by using flag, defaults to on')

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
		dlog = {"timestamp": int(round(time.time())), "ods": [0.0001] * 8, "u": [0] * 8}
		logfile = open(log['fulllog'], 'a')
		log_str = json.dumps(dlog)
		logfile.write('%s\n' % log_str)
		logfile.close()

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
	true_GR = float(args.growth) / 60
	true_OD = latest_OD * numpy.exp(true_GR)
	OD_noise = numpy.random.normal(0, float(args.noise), (len(latest_OD),)) #pylint: disable=E1101
	for chamber in latest_OD:
		if chamber < float(args.noise):
			OD_noise = numpy.random.normal(float(args.noise)*2, float(args.noise), (len(latest_OD),))
	observed_OD = (true_OD + OD_noise) - od_subtraction

	# compute the U and Z values based on OD
	out_us, out_zs = [], []
	for chamber in range(len(observed_OD)):
		temp_u, temp_z = computeControl(observed_OD, zs, controller, setpoints, chamber)
		out_us.append(temp_u)
		out_zs.append(temp_z)

	# calculate value to subtract from next OD
	for chamber in range(8):
		if out_us[chamber] > 0:
			od_subtraction[chamber] = (6.23661e-05 * out_us[chamber]) + 0.001339
		else:
			od_subtraction[chamber] = 0

	# write line of data to full log file
	time_secs = timestamp + 60
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
	os.system("python3 Block-Dilutions.py --full_log")


main()