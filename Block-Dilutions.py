
"""
BACKGROUND

	Created February 26, 2018
		by David Klein, building on previous code from Maxwell Raderstorf
		contributions found at https://github.com/Siegallab/Flexostat-interface
	An open source feature contribution to the Klavins Lab Flexostat project
		project found at https://github.com/Flexostat/Flexostat-interface

INSTRUCTIONS

	Run using Python 2.7 on the command line as such
	$ python2.7 Block-Dilutions.py -h
"""

import os
import csv
import time
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

	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
					description="""
			Block Dilutions Pipeline
			------------------------
			Select one main function: --schedule (-s), --chamber (-c)
			Optional changes: --full_log, --delay, --config, 
					--out (-o), --interval (-i)
						""")

	parser.add_argument('--full_log', action='store_true', help='use full log for OD input (instead of default od log)')
	parser.add_argument('--delay', default='0', help="delay startup of first run by minutes")
	parser.add_argument('--config', default='config.ini', help="change config file from default 'config.ini'")
	parser.add_argument('-o', '--out', action='store_true', help='program processes printing')
	parser.add_argument('-i', '--interval', default='0', help='specify hour interval (default config, otherwise 1)')
	parser.add_argument('-c', '--chamber', action='store_true', help='use individual chamber OD for dilutions')
	parser.add_argument('-s', '--schedule', action='store_true', help='use interval dilution schedule for dilutions')

	args = parser.parse_args()

	# Ensure config file exists and function specified, then read in config variables
	if os.path.exists(args.config) and (args.schedule != args.chamber):
		config = SafeConfigParser()
		config.read(args.config)
		controller = dict(config.items('controller'))
		log = dict(config.items('log'))

		# The log is organized for schedule and chamber respectively like so:
		# [date, time, schedule, start/end, experiment time and current ODs]
		# [date, time, chamber, start (1) or end (0) for chamber 1, 2, 3, 4, 5, 6, 7, 8, experiment time and current ODs]
		if args.schedule:
			programlog = [datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), 'schedule', '', '']
		else:
			programlog = [datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), 'chamber'] + (['']*9)
		# Read in current ODs and make sure config variables match command line arguments
		current_ods = read_ods(args, log)
		controller = update_config(args, config, controller)

		# If blocklog doesn't exist, start dilution blocks and create
		if not os.path.exists(log['blocklog']) and args.schedule:
			programlog = programlog[0:2] + ['start', ','.join(current_ods)]
			update_log(args, log, programlog)
		elif not os.path.exists(log['blocklog']) and args.chamber:
			programlog = programlog[0:2] + ([1]*8) + [','.join(current_ods)]
			update_log(args, log, programlog)
		else:
			blocklog_file = open(log['blocklog'], 'r')
			prevlog = list(csv.reader(blocklog_file))[-1]
			blocklog_file.close()

			# Update controller and programlog if block interval elapsed
			if args.schedule:
				controller, programlog = check_blockinterval(current_ods, log, controller, programlog, prevlog)
			# Update controller and programlog with new setpoints and chamber report when each chamber reaches their setpoint
			else:
				controller, programlog = compare_ods(args, current_ods, controller, programlog)
			# If a change was made based on the last element being filled, then update config and log
			if len(programlog[-1]) > 0:
				update_config(args, config, controller)
				update_log(args, log, programlog)
	else:
		print('ERROR: Config file not found or function not specified correctly.')
	print('Program end.\n')


def read_ods(args, log):
	"""
	Read in current ods based on od log or full log file.

	:param args: command line arguments for program
	:param log: config file log variables
	:return: list of current od values
	"""
	# If full log argument specified, then use flexoparse code to get ODs from fullog file
	if args.full_log:
		log_file = open(log['fulllog'], 'r')
		line = log_file.readlines()[-1]  # Parse input file into list of lines
		current_ods = []
		d1 = line.split(":")
		current_ods.append([int(d1[1][:-7])])
		ods = d1[2][2:-6].split(",")
		for od in ods:
			current_ods.append(float(od))
	# Otherwise od log will be read, then compute ODs from blank and odlog file
	else:
		blank_file = open(log['blanklog'], 'r')
		blank_content = blank_file.read()
		blank_file.close()
		blank_data = list(map(int, blank_content.split()))
		btx = blank_data[0::2]
		brx = blank_data[1::2]

		odlog_file = open(log['odlog'], 'r')
		line = odlog_file.readlines()[-1]
		odlog_file.close()
		line = list(map(int, line.split()))
		current_ods = [int(line[0])]
		tx = line[1::2]
		rx = line[2::2]
		for num in range(8):
			if tx[num] == 0 or rx[num] == 0 or brx[num] == 0 or btx[num] == 0:
				current_ods.append(0)
				continue
			blank_od = float(brx[num]) / float(btx[num])
			od_measure = float(rx[num]) / float(tx[num])
			current_ods.append(log10(blank_od/od_measure))
	return current_ods


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
		print('updated setpoint')
	# If block interval, set to config otherwise 1 if not specified, save as float, and update config to match
	if args.schedule:
		if float(args.interval) <= 0:
			args.block_interval = 1
			if len(controller['blockinterval']) > 0:
				args.interval = float(controller['blockinterval'])
		else:
			args.interval = float(args.interval)
		if not args.interval == float(controller['blockinterval']):
			controller['blockinterval'] = str(args.interval)
		print('updated blockinterval')

	config['controller'] = controller
	config_update = open(args.config, 'w')
	config.write(config_update)

	return controller


def update_log(args, log, programlog):
	"""
	Updates the blocklog file with new updates and prints out if specified.

	:param args: command line arguments for program
	:param log: config file log variables
	:param programlog: list of updated status
	"""
	if args.out:
		print(' '.join(programlog))
	blocklog_file = open(log['blocklog'], 'a')
	wr = csv.writer(blocklog_file)
	wr.writerow(programlog)
	blocklog_file.close()


def check_blockinterval(current_ods, log, controller, programlog, prevlog):
	"""
	Determines if the block interval time has passed.
	Updates controller and programlog appropriately.

	:param current_ods: real ods from od log or full log file
	:param log: config file log variables
	:param controller: config file controller variables
	:param programlog: list of updated status
	:param prevlog: list of previous status
	:return: updated controller and programlog
	"""
	past = datetime.strptime(prevlog[0] + ' ' + prevlog[1], "%Y-%m-%d %H:%M")
	diff = datetime.now() - past
	# If block interval reached (elapsed time = diff between current time and last blocklog entry)
	#	then update the controller setpoints appropriately
	if (diff.seconds/3600) >= float(controller['blockinterval']):
		if controller['setpoint'] == controller['savesetpoint']:
			controller['setpoint'] = controller['blockstart']
			programlog[3] = 'end'
			programlog[-1] = ','.join(current_ods)
			programlog = ' block end ods {}'.format(','.join(current_ods)) + programlog
		else: 
			controller['setpoint'] = controller['savesetpoint']
			programlog[3] = 'start'
			programlog[-1] = ','.join(current_ods)
			programlog = ' block start ods {}'.format(','.join(current_ods)) + programlog
	return controller, programlog


def compare_ods(args, current_ods, controller, programlog):
	"""
	Compares the current ods with the set points.
	Updates controller and programlog appropriately.

	:param args: command line arguments for program
	:param current_ods: real ods from od log or full log file
	:param controller: controller parameters from config file
	:param programlog: list of updated status
	:return: updated controller and programlog variables
	"""
	reference_ods = list(map(float, controller['setpoint'].split()))
	block_ods = list(map(float, controller['blockstart'].split()))
	save_ods = list(map(float, controller['savesetpoint'].split()))
	change = ''
	for num in range(8):
		# If setpoint has original values, check if ODs have reached up to within 5% of setpoint
		if reference_ods[num] == save_ods[num] and not current_ods[num+1] >= (reference_ods[num]-(reference_ods[num]*0.05)):
			# Update setpoint OD with new setpoint and mark change in programlog
			reference_ods[num] = block_ods[num]
			programlog[num+3] = 0
			programlog[-1] = ','.join(current_ods)
		# Otherwise setpoint has blockstart values, check if ODs have reached down to within 5% of setpoint
		elif not current_ods[num+1] <= (reference_ods[num]+(reference_ods[num]*0.05)):
			# Update setpoint OD with new setpoint and mark change in programlog
			reference_ods[num] = save_ods[num]
			programlog[num+3] = 1
			programlog[-1] = ','.join(current_ods)

	controller['setpoint'] = ' '.join(str(e) for e in reference_ods)
	return controller, programlog


main()