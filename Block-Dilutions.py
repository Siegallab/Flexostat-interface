
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
			Select one function: --odlog, --fulllog
			Optional functions: --delay, --config, --log (-l), --out
						""")

	parser.add_argument('--odlog', action='store_true', help='use odlog for OD input')
	parser.add_argument('--fulllog', action='store_true', help='use full log for OD input')
	parser.add_argument('--delay', default='10', help="delay startup by minutes (default '10' = 10 mins)")
	parser.add_argument('--config', default='config.ini', help="change config file from default 'config.ini'")
	parser.add_argument('-l', '--log', action='store_true', help='optional save program processes to log text file')
	parser.add_argument('--out', action='store_true', help='optional program processes printing')

	args = parser.parse_args()

	if os.path.exists(args.config) and (args.odlog or args.fulllog):
		config = SafeConfigParser()
		config.read(args.config)
		controller = dict(config.items('controller'))
		log = dict(config.items('log'))
		# Continue main loop until keyboard interrupt
		try:
			# Record start time and date of function
			programlog = '\n[Block-Dilutions] ' + datetime.now().strftime("%Y-%m-%d %H:%M") + ' program start'
			time.sleep(args.delay*60)
			update = False
			while True:
				# Determine if OD set point for max or min was reached and update config file parameters appropriately
				update, programlog, controller = needs_update(args, controller, log, programlog, update)
				if update:
					# These three lines below update the local controller variable, then save it to the config file
					config['controller'] = controller
					config_update = open(args.config, 'w')
					config.write(config_update)
					# Print and/or save the log of program processes
					programlog = update_programlog(args, log, programlog)
					update = False
				time.sleep(5)
		# At keyboard interrupt, save program log
		except KeyboardInterrupt:
			update_programlog(args, log, programlog)
			time.sleep(1)
	else:
		print('ERROR: Config file or argument not found.')
	print('Program end.\n')


def needs_update(args, controller, log, programlog, update):
	"""
	Compares current od measurements (either from odlog or fulllog) with the current set point.
	If set point has been reached, then replaces set point with appropriate set point from config file.

	:param args: command line arguments for program
	:param controller: config file controller variables
	:param log: config file log variables
	:return: boolean if config file update needed or not
	"""
	# Save set points if they have not been saved before
	if len(controller['savesetpoint'].split()) < 8:
		controller['savesetpoint'] = controller['setpoint']
		programlog += '\n[Block-Dilutions] saved setpoint in config file'
		update = True
	# If odlog argument specified, then compute ODs from blank and odlog file
	if args.odlog:
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
	# If fulllog argument specified, then use flexoparse code to get ODs from fullog file
	else:
		log_file = open(log['fulllog'], 'r')
		line = log_file.readlines()[-1]  # Parse input file into list of lines
		current_ods = []
		d1 = line.split(":")
		current_ods.append([int(d1[1][:-7])])
		ods = d1[2][2:-6].split(",")
		for od in ods:
			current_ods.append(float(od))
	# If setpoint has original values, check if ODs have reached up to within 5% of setpoint
	if controller['setpoint'] == controller['savesetpoint']:
		reference_ods = list(map(float, controller['setpoint'].split()))
		change_ods = list(map(float, controller['blockstart'].split()))
		for num in range(8):
			if not current_ods[num+1] == (reference_ods[num]-(reference_ods[num]*0.05)):
				update = True
				reference_ods[num] = change_ods[num]
				# Saves the OD measurement and channel number when setpoint reached
				programlog += '\n{}\n[Block-Dilutions] channel {} change'.format(current_ods, num)
	# If setpoint has blockstart values, check if ODs have reached down to within 5% of setpoint
	else:
		reference_ods = list(map(float, controller['setpoint'].split()))
		change_ods = list(map(float, controller['savesetpoint'].split()))
		for num in range(8):
			if not current_ods[num+1] == (reference_ods[num]+(reference_ods[num]*0.05)):
				update = True
				reference_ods[num] = change_ods[num]
				# Saves the OD measurement and channel number when setpoint reached
				programlog += '\n{}\n[Block-Dilutions] channel {} change'.format(current_ods, num)
	# Convert any changed setpoints back into string
	controller['setpoint'] = ' '.join(str(e) for e in reference_ods)
	return update, programlog, controller


def update_programlog(args, log, programlog):
	"""
	Print and/or save program log with a time and date stamp.

	:param args: command line arguments for program
	:param log: config file log variables
	:param programlog: program log string
	:return: emptied string for clean program log
	"""
	programlog += '\n[Block-Dilutions] ' + datetime.now().strftime("%Y-%m-%d %H:%M") + ' program save'
	if args.out:
		print(programlog)
	if args.log:
		# if previous program log file found, save contents before overwriting
		if os.path.exists(log['blocklog']):
			with open(log['blocklog'], 'r') as log_file:
				old_log = log_file.read()
				programlog = programlog + '\n\n' + old_log
			log_file.close()
		with open(log['blocklog'], 'w') as log_file:
			log_file.write(programlog)
		log_file.close()
	return ''


main()