"""
BACKGROUND

	Created February 26, 2018
		by David Klein, using previous code from Maxwell Raderstorf
		contributions found at https://github.com/Siegallab/Flexostat-interface
	An open source feature contribution to the Klavins Lab Flexostat project
		project found at https://github.com/Flexostat/Flexostat-interface

INSTRUCTIONS

	Run using Python 2.7 on the command line as such
	$ python2.7 Block-Dilutions.py -h
"""

import os
import csv
import json
import time
import numpy
import argparse
from math import log10
from datetime import datetime
from configparser import SafeConfigParser


def main():
	"""
	Defines the command line arguments intaken by the program.
	Ensures there is a config file to work with before running main loop.
	Keyboard interrupt ends program.
	"""
	args = command_line_arguments()
	# Ensure config file exists and function specified, then read in config variables
	if os.path.exists(args.config) and (args.schedule != args.chamber):
		config = SafeConfigParser()
		config.read(args.config)
		controller = dict(config.items('controller'))
		log = dict(config.items('log'))

		# The log is organized for schedule and chamber respectively like so:
		# [date, time, schedule, new setpoints for chambers, human time (hr), experiment time, current ODs]
		# [date, time, chamber, new setpoints for chambers, human time (hr), experiment time, current ODs]
		if args.schedule:
			programlog = [datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), 'schedule']
		else:
			programlog = [datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), 'chamber']
		# Read in current ODs and make sure config variables match command line arguments
		human_time, machine_time, current_ods = read_ods(args, log)
		programlog = programlog + [','.join(controller['setpoint'].split()), human_time, machine_time, ','.join(str(e) for e in current_ods)]
		controller = update_config(args, config, controller)

		# If blocklog doesn't exist, start dilution blocks and create
		if not os.path.exists(log['blocklog']):
			update_log(args, log, programlog)
		else:
			blocklog_file = open(log['blocklog'], 'r')
			prevlog = list(csv.reader(blocklog_file))[-1]
			blocklog_file.close()

			# Update controller and programlog if block interval elapsed
			if args.schedule:
				controller, programlog = check_blockinterval(current_ods, controller, programlog, prevlog)
			# Update controller and programlog with new setpoints and chamber report when each chamber reaches their setpoint
			else:
				controller, programlog = compare_ods(current_ods, controller, programlog)
			# Update config and log if setpoints have been changed
			if not prevlog[3] == programlog[3]:
				update_config(args, config, controller)
				update_log(args, log, programlog)
	else:
		print('ERROR: Config file not found or function not specified correctly.')
	print('Block-Dilutions.py end.')


def command_line_arguments():
	"""
	Takes in command line argument parameters and displays help descriptions.

	:return: variable containing all command line argument parameters
	"""
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
					description="""
	Block Dilutions Pipeline
	------------------------
	Select one main function: --schedule (-s), --chamber (-c)
	Optional changes: --odlog, --delay, --config, 
			--out (-o), --growth (-g), --dilution (-d)
				""")

	parser.add_argument('--odlog', action='store_true', help='use OD log for OD input (instead of default full log)')
	parser.add_argument('--delay', default='0', help="delay startup of first run by minutes")
	parser.add_argument('--config', default='config.ini', help="change config file from default 'config.ini'")
	parser.add_argument('-o', '--out', action='store_true', help='program processes printing')
	parser.add_argument('-g', '--growth', default='0', help='specify hour interval for growth block (default config, otherwise 7)')
	parser.add_argument('-d', '--dilution', default='0', help='specify hour interval for dilution (default config, otherwise 4)')
	parser.add_argument('-c', '--chamber', action='store_true', help='use individual chamber OD for dilutions')
	parser.add_argument('-s', '--schedule', action='store_true', help='use interval dilution schedule for dilutions')

	args = parser.parse_args()
	return args


def read_ods(args, log):
	"""
	Read in current ods based on od log or full log file.

	:param args: command line arguments for program
	:param log: config file log variables
	:return: list of current od values, experiment time in human (hr) and machine units
	"""
	# if odlog specificed, compute compute ODs from blank and odlog file
	if args.odlog:
		blank_file = open(log['blanklog'], 'r')
		blank_content = blank_file.read()
		blank_file.close()
		blank_data = list(map(int, blank_content.split()))
		btx = blank_data[0::2]
		brx = blank_data[1::2]

		odlog_file = open(log['odlog'], 'r')
		first = odlog_file.readlines()[0]
		line = odlog_file.readlines()[-1]
		odlog_file.close()

		time_start = int(first.split()[0])
		line = list(map(int, line.split()))
		current_ods = []
		machine_time = int(line[0])
		human_time = (machine_time - time_start) / 3600
		tx = line[1::2]
		rx = line[2::2]
		for num in range(8):
			if tx[num] == 0 or rx[num] == 0 or brx[num] == 0 or btx[num] == 0:
				current_ods.append(0)
				continue
			blank_od = float(brx[num]) / float(btx[num])
			od_measure = float(rx[num]) / float(tx[num])
			current_ods.append(log10(blank_od/od_measure))
	# otherwise use json standard library to get ODs from fulllog file
	else:
		log_file = open(log['fulllog'], 'r')
		log_data = log_file.readlines()
		log_file.close()
		first = log_data[0]
		time_start = json.loads(first)['timestamp']
		last_line = log_data[-1]
		if len(last_line) < 1:
			last_line = log_data[-2]
		last_line = json.loads(last_line)
		current_ods = list(last_line['ods'])
		machine_time = last_line['timestamp']
		human_time = (machine_time - time_start) / 3600
	return human_time, machine_time, current_ods


def update_config(args, config, controller):
	"""
	Updates the config file to match command line arguments and program updates.

	:param args: command line arguments for program
	:param config: variable holding all config variables from file
	:param controller: config file controller variables
	:return: updated controller variables
	"""
	# Save set points if they have not been saved before and delay program for specified time
	if len(controller['savesetpoint'].split()) < 1:
		controller['savesetpoint'] = controller['setpoint']
		if not float(args.delay) <= 0:
			time.sleep(float(args.delay)*60)
	# If block interval, set to config otherwise 1 if not specified, save as float, and update config to match
	if args.schedule:
		if float(args.growth) <= 0 and len(controller['growthinterval']) == 0:
			args.growth = 7
		elif float(args.growth) <= 0:
			args.growth = float(controller['growthinterval'])
		if float(args.dilution) <= 0 and len(controller['dilutioninterval']) == 0:
			args.dilution = 4
		elif float(args.dilution) <= 0:
			args.dilution = float(controller['dilutioninterval'])
		controller['growthinterval'] = args.growth
		controller['dilutioninterval'] = args.dilution
	config['controller'] = controller
	config_update = open(args.config, 'w')
	config.write(config_update)
	return controller


def check_blockinterval(current_ods, controller, programlog, prevlog):
	"""
	Determines if the block interval time has passed.
	Updates controller and programlog appropriately.

	:param current_ods: real ods from od log or full log file
	:param controller: config file controller variables
	:param programlog: list of updated status
	:param prevlog: list of previous status
	:return: updated controller and programlog
	"""
	past = datetime.strptime(prevlog[0] + ' ' + prevlog[1], "%Y-%m-%d %H:%M")
	diff = datetime.now() - past
	# If block interval reached (elapsed time = diff between current time and last blocklog entry)
	#	then update the controller setpoints appropriately
	if controller['setpoint'] == controller['savesetpoint'] and (diff.seconds/3600) >= float(controller['growthinterval']):
		controller['setpoint'] = controller['blockstart']
	elif controller['setpoint'] == controller['blockstart'] and (diff.seconds/3600) >= float(controller['dilutioninterval']):
		controller['setpoint'] = controller['savesetpoint']
	programlog[3] = ','.join(controller['setpoint'].split())
	programlog[-1] = ','.join(str(e) for e in current_ods)
	return controller, programlog


def compare_ods(current_ods, controller, programlog):
	"""
	Compares the current ods with the set points.
	Updates controller and programlog appropriately.

	:param current_ods: real ods from od log or full log file
	:param controller: controller parameters from config file
	:param programlog: list of updated status
	:return: updated controller and programlog variables
	"""
	reference_ods = list(map(float, controller['setpoint'].split()))
	block_ods = list(map(float, controller['blockstart'].split()))
	save_ods = list(map(float, controller['savesetpoint'].split()))
	for num in range(8):
		# If setpoint has original values, check if ODs have reached up to within 5% of setpoint
		if reference_ods[num] == save_ods[num] and current_ods[num] >= (reference_ods[num]-(reference_ods[num]*0.05)):
			# Update setpoint OD with new setpoint
			reference_ods[num] = block_ods[num]
		# Otherwise setpoint has blockstart values, check if ODs have reached down to within 5% of setpoint
		elif current_ods[num] <= (reference_ods[num]+(reference_ods[num]*0.05)):
			# Update setpoint OD with new setpoint
			reference_ods[num] = save_ods[num]
	controller['setpoint'] = ' '.join(str(e) for e in reference_ods)
	programlog[3] = ','.join(str(e) for e in reference_ods)
	programlog[-1] = ','.join(str(e) for e in current_ods)
	return controller, programlog


def update_log(args, log, programlog):
	"""
	Updates the blocklog file with new updates and prints out if specified.

	:param args: command line arguments for program
	:param log: config file log variables
	:param programlog: list of updated status
	"""
	if args.out:
		print("Block report: {}".format(programlog))
	blocklog_file = open(log['blocklog'], 'a')
	wr = csv.writer(blocklog_file)
	wr.writerow(programlog)
	blocklog_file.close()


main()