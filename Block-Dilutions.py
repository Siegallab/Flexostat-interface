
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
			Optional functions: --full_log, --delay, --config, 
					--out (-o), --schedule (-s), --interval (-i)
						""")

	parser.add_argument('--full_log', action='store_true', help='use full log for OD input (instead of default od log)')
	parser.add_argument('--delay', default='0', help="delay startup of first run by minutes")
	parser.add_argument('--config', default='config.ini', help="change config file from default 'config.ini'")
	parser.add_argument('-o', '--out', action='store_true', help='program processes printing')
	parser.add_argument('-i', '--interval', default='0', help='specify hour interval (default config, otherwise 1)')
	parser.add_argument('-s', '--schedule', action='store_true', help='use interval dilution schedule')

	args = parser.parse_args()

	# Ensure config file exists, then read it in
	if os.path.exists(args.config):
		config = SafeConfigParser()
		config.read(args.config)
		controller = dict(config.items('controller'))
		log = dict(config.items('log'))
		programlog = ''

		# Update config file with new arguments if needed, then read in current ods
		controller, programlog = check_config(args, controller, log, programlog)
		current_ods = read_ods(args, log)
		# If schedule, update controller and programlog if block interval elapsed
		if args.schedule:
			controller, programlog = check_blockinterval(current_ods, log, controller, programlog)
		# Record when chambers have reacted their setpoints, and change chamber setpoints if not schedule
		controller, programlog = compare_ods(args, current_ods, controller, programlog)
		if len(programlog) > 0:
			# These three lines below update the local controller variable, then save it to the config file
			config['controller'] = controller
			config_update = open(args.config, 'w')
			config.write(config_update)
			# Print and/or save the log of program processes
			programlog = '\n' + datetime.now().strftime("%Y-%m-%d %H:%M") + programlog
			if args.out:
				print(programlog)
			blocklog_file = open(log['blocklog'], 'a')
			blocklog_file.write(programlog)
			blocklog_file.close()
	else:
		print('ERROR: Config file.')
	print('Program end.\n')


def check_config(args, controller, log, programlog):
	"""
	Compares current od measurements (either from odlog or fulllog) with the current set point.
	If set point has been reached, then replaces set point with appropriate set point from config file.

	:param args: command line arguments for program
	:param controller: config file controller variables
	:param log: config file log variables
	:param programlog: string describing updates being made
	:return: updated controller and updated programlog
	"""
	# Save set points if they have not been saved before and delay program for specified time
	if len(controller['savesetpoint'].split()) < 1:
		controller['savesetpoint'] = controller['setpoint']
		if not float(args.delay) <= 0:
			time.sleep(float(args.delay)*60)
		programlog += ' updated setpoint'
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
		programlog += ' updated blockinterval'
	if not os.path.exists(log['blocklog']):
		programlog += ' created blocklog'
	return controller, programlog


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


def compare_ods(args, current_ods, controller, programlog):
	"""
	Compares the current ods with the set points.
	Updates controller, update, and programlog appropriately.

	:param args: command line arguments for program
	:param current_ods: real ods from od log or full log file
	:param controller: controller parameters from config file
	:param programlog: string describing updates being made
	:return: updated controller and programlog variables
	"""
	reference_ods = list(map(float, controller['setpoint'].split()))
	block_ods = list(map(float, controller['blockstart'].split()))
	save_ods = list(map(float, controller['savesetpoint'].split()))
	for num in range(8):
		# If setpoint has original values, check if ODs have reached up to within 5% of setpoint
		if reference_ods[num] == save_ods[num] and not current_ods[num+1] == (reference_ods[num]-(reference_ods[num]*0.05)):
			programlog += ' chamber {} end ods {}'.format(num, ','.join(current_ods))
			# Update setpoint OD with new setpoint
			if not args.schedule:
				reference_ods[num] = block_ods[num]
		# Otherwise setpoint has blockstart values, check if ODs have reached down to within 5% of setpoint
		elif not current_ods[num+1] == (reference_ods[num]+(reference_ods[num]*0.05)):
			programlog += ' chamber {} start ods {}'.format(num, ','.join(current_ods))
			# Update setpoint OD with new setpoint
			if not args.schedule:
				reference_ods[num] = save_ods[num]
	# Update controller setpoints OD with new setpoints
	if not args.schedule:
		controller['setpoint'] = ' '.join(str(e) for e in reference_ods)
	return controller, programlog


def check_blockinterval(current_ods, log, controller, programlog):
	"""
	Determines if the block interval time has passed.
	Updates controller and programlog.

	:param current_ods: real ods from od log or full log file
	:param log: config file log variables
	:param controller: config file controller variables
	:param programlog: string describing updates being made
	:return: updated controller and programlog
	"""
	# Blocklog may not exist on first run, so it will be created on the first update
	if os.path.exists(log['blocklog']):
		blocklog_file = open(log['blocklog'], 'r')
		blocklog_contents = blocklog_file.readlines()
		blocklog_file.close()

		past = datetime.strptime(blocklog_contents[-1][0:16], "%Y-%m-%d %H:%M")
		diff = datetime.now() - past
		# If block interval reached (elapsed time = diff between current time and last blocklog entry)
		#	then update the controller setpoints appropriately
		if (diff.seconds/3600) >= float(controller['blockinterval']):
			if controller['setpoint'] == controller['savesetpoint']:
				controller['setpoint'] = controller['blockstart']
				programlog += ' block end ods {}'.format(','.join(current_ods))
			else: 
				controller['setpoint'] = controller['savesetpoint']
				programlog += ' block start ods {}'.format(','.join(current_ods))
	return controller, programlog


main()