
"""
BACKGROUND

	Created January 31, 2018
		by David Klein, using previous code from Maxwell Raderstorf
		contributions found at https://github.com/Siegallab/Flexostat-interface
	An open source feature contribution to the Klavins Lab Flexostat project
		project found at https://github.com/Flexostat/Flexostat-interface

INSTRUCTIONS

	Run using Python 3 on the command line as such
	$ python3 Growth-Pipe.py -h
"""

import numpy
import matplotlib.pyplot as plt
import pandas
import os
import argparse
import warnings
import csv
import math
from math import log10
from datetime import datetime

def main():
	"""
	Defines the command line arguments intaken by the program.
	Ensures there is a config file to work with before calling the 'functions' function.
	"""
	# Allows warnings from divide by zero or log/ln negative number to be caught in try except
	warnings.filterwarnings('error')
	args = command_line_parameters()

	if os.path.exists(args.config):
		paths, process_log, exp = config_variables(args)
		process_log = functions(args, paths, process_log, exp)
		# print and save process log
		log_functions(args, process_log, exp)
	else:
		print('ERROR: Config file not found.')
	print('Program end.\n')


def command_line_parameters():
	"""
	Takes in command line argument parameters and displays help descriptions.

	:return: variable containing all command line argument parameters
	"""
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
					description="""
			Growth Rate Analysis Pipeline
			-----------------------------
			Select at least one data set: --u, --od
			Select at least one function: --parse (-p), --odlog,
					--rate (-r), --stats, --r_stats, --graph

			Optional changes: --config, --log (-l), --print
			Optional stats parameters: --block (-b) or --interval (-i)
			Optional graph parameters: --xlim (-x), --ylim (-y), --sd, --se
						""")

	parser.add_argument('--u', action='store_true', help='specify dilutions data set')
	parser.add_argument('--od', action='store_true', help='specify optical density data set')

	parser.add_argument('-p', '--parse', action='store_true', help='parse log file into clean data set')
	parser.add_argument('--odlog', action='store_true', help='parse odlog file into clean data set')
	parser.add_argument('-r', '--rate', action='store_true', help='calculate growth rate from data set')
	parser.add_argument('--stats', action='store_true', help='calculate mean, SD, and SE from data set')
	parser.add_argument('--r_stats', action='store_true', help='calculate mean, SD, and SE from growth rates of data set')
	parser.add_argument('--graph', default='0', help="graph specified data: 1 for main u/od, 2 for main stats, 3 for growth rates," + 
				" 4 for growth stats (e.g. '--graph 1234' for all)")

	parser.add_argument('-i', '--interval', default='1',
						help="modify default hour time interval for stats by multiplication (e.g. '-i 0.5' = 30 min, '-i 2' = 2 hrs)")
	parser.add_argument('-b', '--block', action='store_true', help='specify separation of statistics based on block dilutions')
	parser.add_argument('--sd', action='store_true', help='display standard deviation bars on graphs')
	parser.add_argument('--se', action='store_true', help='display standard error bars on graphs')
	# parser.add_argument('--ci', action='store_true', help='display confidence interval bars on graphs')
	parser.add_argument('-x', '--xlim', default='0-0', help="limit data to upper and lower bound x (e.g. '-x 5-10')")
	parser.add_argument('-y', '--ylim', default='0-0', help="limit data to upper and lower bound y (e.g. '-y 5-10')")
	parser.add_argument('--config', default='config-growth.csv',
						help="change config file from default 'config-growth.csv'")
	parser.add_argument('-l', '--log', action='store_true', help='optional save program processes to log text file')
	parser.add_argument('--print', action='store_true', help='optional program processes printing')

	args = parser.parse_args()
	return args


def config_variables(args):
	"""
	Reads in variables from config file for growth pipe, ensures directories exist, and starts log for program processes.

	:param args: list of command line arguments
	:return: list with config file paths and log with program processes
	"""
	# begin log to keep track of program processes
	# read in config file and save all config variables to local variables in a dictionary
	process_log = '\n[Growth-Pipe] ' + datetime.now().strftime("%Y-%m-%d %H:%M")
	paths = {
		# general local variables
		'' : '', 'log file' : '', 'odlog' : '', 'blank' : '', 'block' : '',
		'log processes' : '', 'data directory' : '', 'experiment' : '', 
		# dilution local variables
		'u' : '', 'u statistics' : '', 'u machine time' : '',
		'u growth rates' : '', 'u growth statistics' : '',
		# optical density local variables
		'od' : '', 'u statistics' : '', 'od machine time' : '', 
		'od growth rates' : '', 'od growth statistics' : '',
		# dilution graph local variables
		'u graphs' : '', 'u statistics graphs' : '', 'u growth rates graphs' : '', 'u growth statistics graphs' : '',
		# optical density graph local variables
		'od graphs' : '', 'od statistics graphs' : '', 'od growth rates graphs' : '', 'od growth statistics graphs' : ''
	}
	with open(args.config) as config_file:
		reader = csv.reader(config_file)
		for row in reader:
			# removes any ending slashes that may exist in csv
			if row[1][-1] == '/':
				row[1] = row[1][:-1]
			paths[row[0]] = row[1]
			if len(row[4]) >= 1:
				if row[4][-1] == '/':
					row[4] = row[1][:-1]
			paths[row[3]] = row[4]
	config_file.close()

	# ensure data and experiment directories exist
	# format paths to variable appropriately
	if paths['experiment'][-1] == "'":
		paths['experiment'] = paths['experiment'][:-1]
	if os.path.exists(paths['data directory']):
		process_log += '\nData directory found.'
	else:
		os.system("mkdir '{}'".format(paths['data directory']))
		process_log += '\nData directory not found. Made new one.'
	exp = '{}/{}/'.format(paths['data directory'], paths['experiment'])
	if os.path.exists(exp):
		process_log += '\nExperiment directory found.'
	else:
		os.system("mkdir '{}'".format(exp))
		process_log += '\nExperiment directory not found. Made new one.'
	return paths, process_log, exp


def functions(args, paths, process_log, exp):
	"""
	Runs all functions specified by the command line arguments using the config file variables, while taking not in the log variable.

	:param args: list of command line arguments
	:param paths: list with config file paths
	:param process_log: log for keeping track of processes
	:param exp: path to experiment
	:return: log of all processes that were run
	"""
	# make sure at least one data set is specified
	if not args.u and not args.od:
		print('ERROR: Data set not specified.')
	if args.u:
		# parse function takes log file and exports u csv
		if args.parse:
			with open(exp + paths['log file'] + '.dat') as f:  # open input file
				log = f.read()

			process_log += '\nParsing u from log file...'
			udata = parse_u(log)

			# tell user if file exists and will be overwritten or if new file will be made
			if os.path.exists(exp + paths['u'] + '.csv'):
				process_log += '\n\tOutput file exists, will overwrite.'
			else:
				process_log += '\n\tOutput file not found, will make new file.'

			ufile = open(exp + paths['u'] + '.csv', 'w')
			wru = csv.writer(ufile, quoting=csv.QUOTE_ALL)
			for u in udata:
				wru.writerow(u)

			f.close()
			ufile.close()
			process_log += '\n\tParsed csv created and exported.'
		# rate function takes u csv and exports u growth rate csv
		if args.rate:
			process_log += '\nGrowth rates for u calculating...'
			process_log = machine_to_human(exp + paths['u'], exp + paths['u machine time'], process_log)

			# tell user if file exists and will be overwritten or if new file will be made
			if os.path.exists(exp + paths['u growth rates'] + '.csv'):
				process_log += '\n\tOutput file exists, will overwrite.'
			else:
				process_log += '\n\tOutput file not found, will make new file.'

			u_rate(exp + paths['u'], exp + paths['u growth rates'])
			process_log += '\n\tGrowth rates calculated and exported.'
		# stats function takes u csv and exports a csv for each chamber
		if args.stats:
			process_log += '\nStats for u calculating...'
			dead, dead, process_log = validate_output_path(args, exp + paths['u statistics'], False, process_log)
			if args.block:
				statistics(exp + paths['u'], exp + paths['u statistics'], args.interval, exp + paths['block'])
			else:
				statistics(exp + paths['u'], exp + paths['u statistics'], args.interval, '')
			process_log += '\n\tStats csv calculated and exported.'
		# stats function takes u growth rate csv and exports a csv for each chamber
		if args.r_stats:
			process_log += '\nStats for u growth rates calculating...'
			dead, dead, process_log = validate_output_path(args, exp + paths['u growth statistics'], False, process_log)
			if args.block:
				statistics(exp + paths['u growth rates'], exp + paths['u growth statistics'], args.interval, exp + paths['block'])
			else:
				statistics(exp + paths['u growth rates'], exp + paths['u growth statistics'], args.interval, '')
			process_log += '\n\tStats csv calculated and exported.'
		# graph functions take specific od csv and exports graphs based on command line arguments
		if args.graph:
			if '1' in args.graph:
				process_log += '\nGraphing for u...'
				output, limits, process_log = validate_output_path(args, exp + paths['u graphs'], True, process_log)
				graphs(args, exp + paths['u'], output, limits)
				process_log += '\n\tGraphs exported.'
			if '2' in args.graph:
				process_log += '\nGraphing for u stats...'
				output, limits, process_log = validate_output_path(args, exp + paths['u statistics graphs'], True, process_log)
				graphs(args, exp + paths['u statistics'], output, limits)
				process_log += '\n\tGraphs exported.'
			if '3' in args.graph:
				process_log += '\nGraphing for u growth rates...'
				output, limits, process_log = validate_output_path(args, exp + paths['u growth rates graphs'], True, process_log)
				graphs(args, exp + paths['u growth rates'], output, limits)
				process_log += '\n\tGraphs exported.'
			if '4' in args.graph:
				process_log += '\nGraphing for u growth stats...'
				output, limits, process_log = validate_output_path(args, exp + paths['u growth statistics graphs'], True, process_log)
				graphs(args, exp + paths['u growth statistics'], output, limits)
				process_log += '\n\tGraphs exported.'
	if args.od:
		# parse function takes log file and exports od csv
		if args.parse:
			process_log += '\nParsing od from log file...'
			with open(exp + paths['log file'] + '.dat') as f:  # open input file
				log = f.read()

			oddata = parse_od(log)

			# tell user if file exists and will be overwritten or if new file will be made
			if os.path.exists(exp + paths['od'] + '.csv'):
				process_log += '\n\tOutput file exists, will overwrite.'
			else:
				process_log += '\n\tOutput file not found, will make new file.'

			odfile = open(exp + paths['od'] + '.csv', 'w')
			wrod = csv.writer(odfile, quoting=csv.QUOTE_ALL)
			for od in oddata:
				wrod.writerow(od)

			f.close()
			odfile.close()
			process_log += '\n\tParsed csv created and exported.'
		# parse function takes odlog file and exports od csv
		if args.odlog:
			process_log += '\nParsing od from odlog file...'
			# tell user if file exists and will be overwritten or if new file will be made
			if os.path.exists(exp + paths['od'] + '.csv'):
				process_log += '\n\tOutput file exists, will overwrite.'
			else:
				process_log += '\n\tOutput file not found, will make new file.'
			parse_odlog(exp + paths['odlog'], exp + paths['blank'], exp + paths['od'])
			process_log += '\n\tParsed csv created and exported.'
		# rate function takes od csv and exports od growth rate csv
		if args.rate:
			process_log += '\nGrowth rates for od calculating...'
			process_log = machine_to_human(exp + paths['od'], exp + paths['od machine time'], process_log)

			# tell user if file exists and will be overwritten or if new file will be made
			if os.path.exists(exp + paths['od growth rates'] + '.csv'):
				process_log += '\n\tOutput file exists, will overwrite.'
			else:
				process_log += '\n\tOutput file not found, will make new file.'

			od_rate(exp + paths['od'], exp + paths['od growth rates'])
			process_log += '\n\tGrowth rates calculated and exported.'
		# stats function takes od csv and exports a csv for each chamber
		if args.stats:
			process_log += '\nStats for od calculating...'
			dead, dead, process_log = validate_output_path(args, exp + paths['od statistics'], False, process_log)
			if args.block:
				statistics(exp + paths['od'], exp + paths['od statistics'], args.interval, exp + paths['block'])
			else:
				statistics(exp + paths['od'], exp + paths['od statistics'], args.interval, '')
			process_log += '\n\tStats csv calculated and exported.'
		# stats function takes od growth rate csv and exports a csv for each chamber
		if args.r_stats:
			process_log += '\nStats for od growth rates calculating...'
			dead, dead, process_log = validate_output_path(args, exp + paths['od growth statistics'], False, process_log)
			if args.block:
				statistics(exp + paths['od growth rates'], exp + paths['od growth statistics'], args.interval, exp + paths['block'])
			else:
				statistics(exp + paths['od growth rates'], exp + paths['od growth statistics'], args.interval, '')
			process_log += '\n\tStats csv calculated and exported.'
		# graph functions take specific od csv and exports graphs based on command line arguments
		if args.graph:
			if '1' in args.graph:
				process_log += '\nGraphing for od...'
				output, limits, process_log = validate_output_path(args, exp + paths['od graphs'], True, process_log)
				graphs(args, exp + paths['od'], output, limits)
				process_log += '\n\tGraphs exported.'
			if '2' in args.graph:
				process_log += '\nGraphing for od stats...'
				output, limits, process_log = validate_output_path(args, exp + paths['od statistics graphs'], True, process_log)
				graphs(args, exp + paths['od statistics'], output, limits)
				process_log += '\n\tGraphs exported.'
			if '3' in args.graph:
				process_log += '\nGraphing for od growth rates...'
				output, limits, process_log = validate_output_path(args, exp + paths['od growth rates graphs'], True, process_log)
				graphs(args, exp + paths['od growth rates'], output, limits)
				process_log += '\n\tGraphs exported.'
			if '4' in args.graph:
				process_log += '\nGraphing for od growth stats...'
				output, limits, process_log = validate_output_path(args, exp + paths['od growth statistics graphs'], True, process_log)
				graphs(args, exp + paths['od growth statistics'], output, limits)
				process_log += '\n\tGraphs exported.'
	return process_log


def machine_to_human(intake, output, process_log):
	"""
	Converts machine time (seconds with starting time long ago) to hours from experiment start.
	Generates new csv and renames the old csv.

	:param intake: path to data
	:param output: path for export
	:param process_log: log for keeping track of processes
	:return: returns updated log of program processes
	"""
	df = pandas.read_csv('{}.csv'.format(intake), header=None,
							names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	time_start = df.iloc[0, 0]
	# Checks if the first time point is in machine time
	if time_start > 1:
		process_log += '\n\tData set is using machine time. Converting to human time...'
		# Renames the csv using machine time
		command = "mv '{}.csv' '{}.csv'".format(intake, output)
		os.system(command)
		new_data = []
		# Iterates through rows of csv and changes time point to hours in new row array
		# Joins each array into new data array and saves to a new csv
		for row in df.itertuples():
			new_row = []
			row_id = True
			for element in row:
				if row_id:
					row_id = False
				elif len(new_row) == 0:
					new_row.append((element - time_start) / 3600)
				else:
					new_row.append(element)
			new_data.append(new_row)
		numpy.savetxt('{}.csv'.format(intake), new_data, delimiter=",")
		process_log += '\n\tData set is using machine time. Data set with human time created.'
	else:
		process_log += '\n\tData set is using human time.'
	
	return process_log


def validate_output_path(args, output, function, process_log):
	"""
	Creates the output folder if there is none.
	Parses limits for graphs based on command line parameters.

	:param args: command line argument array for limit parsing
	:param output: path for export
	:param function: specify true if function is graphs for limit parsing
	:param process_log: log for keeping track of processes
	:return: new output based on limits, limits for graphs, and updated log for program processes
	"""
	lim_str = ''
	limits = [0.0, 0.0, 0.0, 0.0]
	# graphs will have x and y limits parsed and used for the output directory
	if function:
		if args.xlim:
			temp = args.xlim
			limits[0] = float(temp.split("-")[0])
			limits[1] = float(temp.split("-")[1])
			lim_str = lim_str + ' x' + args.xlim
		if args.ylim:
			temp = args.ylim
			limits[2] = float(temp.split("-")[0])
			limits[3] = float(temp.split("-")[1])
			lim_str = lim_str + ' y' + args.ylim
		if args.sd:
			lim_str = lim_str + ' sd'
		elif args.se:
			lim_str = lim_str + ' se'

	# create an output directory if none exists
	if not os.path.exists('{}{}'.format(output, lim_str)):
		os.system("mkdir '{}{}'".format(output, lim_str))
		process_log += '\n\tOutput folder not found, made new folder.'
	else:
		process_log += '\n\tOutput folder found, will overwrite previous files.'
	output = '{}{}'.format(output, lim_str)

	return output, limits, process_log


def parse_u(rdata):
	"""
	Parses dilution values from the log file.

	:param rdata: string of log file contents
	:return: array of all dilution values
	"""
	lines = rdata.split('\n')  # Parse input file into list of lines
	data = []
	for line in lines[:-1]:
		d1 = line.split(":")
		d2 = [int(d1[1][:-7])]
		us = d1[3][2:-6].split(",")
		for u in us:
			d2.append(float(u))
		data.append(tuple(d2))

	return data


def parse_od(rdata):
	"""
	Parses optical density values from the log file.

	:param rdata: string of log file contents
	:return: array of all optical density values
	"""
	lines = rdata.split('\n')  # Parse input file into list of lines
	data = []
	for line in lines[:-1]:
		d1 = line.split(":")
		d2 = [int(d1[1][:-7])]
		ods = d1[2][2:-6].split(",")
		for od in ods:
			d2.append(float(od))
		data.append(tuple(d2))

	return data


def parse_odlog(odlog, blank, output):
	"""
	Parses optical density values from the odlog file.

	:param odlog: path to od data
	:param blank: path to blank od data
	:param output: path for export
	"""
	blank_file = open(blank + '.dat', 'r')
	blank_content = blank_file.read()
	blank_file.close()
	blank_data = list(map(int, blank_content.split()))
	btx = blank_data[0::2]
	brx = blank_data[1::2]

	odlog_file = open(odlog + '.dat', 'r')
	odlog_content = odlog_file.readlines()
	odlog_file.close()
	od_list = []
	for line in odlog_content:
		line = list(map(int, line.split()))
		temp_ods = [int(line[0])]
		tx = line[1::2]
		rx = line[2::2]
		for num in range(8):
			if tx[num] == 0 or rx[num] == 0 or brx[num] == 0 or btx[num] == 0:
				temp_ods.append(0)
				continue
			blank_od = float(brx[num]) / float(btx[num])
			od_measure = float(rx[num]) / float(tx[num])
			temp_ods.append(log10(blank_od/od_measure))
		od_list.append(temp_ods)
	odfile = open(output + '.csv', 'w')
	wrod = csv.writer(odfile, quoting=csv.QUOTE_ALL)
	wrod.writerows(od_list)
	odfile.close()


def u_rate(intake, output):
	"""
	Calculates growth rate data based on dilutions (u) and saves to csv.

	:param intake: path to data
	:param output: path for export
	"""
	df = pandas.read_csv('{}.csv'.format(intake), header=None, names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	new_data_r = []
	time_start = df.iloc[0, 0]
	previous_time = df.iloc[0, 0]
	time_difference = 0
	for row in df.itertuples():
		new_row = []
		row_id = True
		# Iterates through each row and row element in data frame
		#       adds calculated growth rates to new row array, which is added to new data array
		for element in row:
			# Disregard first element (row number added by pandas when data frame is made)
			if row_id:
				row_id = False
				continue
			# Second element is the time point and time difference is calculated (should always be 60 sec)
			elif len(new_row) == 0:
				new_row.append(element - time_start)
				time_difference = element - previous_time
				previous_time = element
			# If first row of data frame (determined by time point) or zero value, it is arbitrarily set to zero
			elif element == 0 or new_row[0] == 0:
				new_row.append(float(0))
			# Rest of elements will be values that do not cause errors when calculating growth rate
			else:
				new_row.append(round((numpy.log(1 + (element / 15000)) / time_difference), 6)) # pylint: disable=E1101
		new_data_r.append(new_row)

	numpy.savetxt('{}.csv'.format(output), new_data_r, delimiter=",")


def od_rate(experiment, output):
	"""
	Calculates growth rate data based on optical density (od) and saves to csv.

	:param intake: path to data
	:param output: path for export
	"""
	df = pandas.read_csv('{}.csv'.format(experiment), header=None, names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	new_data_r = []
	time_start = df.iloc[0, 0]
	previous_time = df.iloc[0, 0]
	time_difference = 0
	previous_od = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
	for row in df.itertuples():
		new_row = []
		row_id = True
		ch_count = 0
		# Iterates through each row and row element in data frame
		#       adds calculated growth rates to new row array, which is added to new data array
		for element in row:
			# Disregard first element (row number added by pandas when data frame is made)
			if row_id:
				row_id = False
				continue
			# Second element is the time point and time difference is calculated (should always be 60 sec)
			elif len(new_row) == 0:
				new_row.append(element - time_start)
				time_difference = element - previous_time
				previous_time = element
				continue
			# If first row of data frame (determined by time point) it is arbitrarily set to zero
			elif new_row[0] == 0:
				new_row.append(float(0))
			# Negative OD's are ignored with growth rate being a blank space
			elif element < 0 or previous_od[ch_count] < 0:
				new_row.append(None)
				previous_od[ch_count] = element
			else:
				try:
					new_row.append(round((numpy.log(element / previous_od[ch_count]) / time_difference), 6)) # pylint: disable=E1101
				# If the growth rate calculation fails (it will for values <= 0) then append a blank space
				except (Warning, Exception) as err:
					# For showing the warning or exception, uncomment the below line
					# print('{}'.format(err))
					new_row.append(None)
				# Each element is saved for comparison with the next element of that chamber
				previous_od[ch_count] = element
			ch_count += 1
		new_data_r.append(new_row)

	df = pandas.DataFrame(new_data_r)
	df.to_csv(path_or_buf='{}.csv'.format(output), index=False)


def statistics(intake, output, interval, block):
	"""
	Analyzes growth rate csv for general statistics (averages, standard deviation, and standard error).

	:param intake: path to data
	:param output: path for export
	:param interval: modify default hour time interval by multiplication
	:param block: path to blocklog file
	"""
	df = pandas.read_csv('{}.csv'.format(intake), header=None, names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])

	# if blocklog file is specified, then separate stats into blocks
	if len(block) > 0:
		# for each chamber, will iterate through dataframe and iterate through blocklog data as each block time is reached
		blocklog_file = open(block, 'r')
		blocklog = csv.reader(blocklog_file)
		blocklog_file.close()
		for chamber in range(2, 10):
			# for first blocklog row, define setpoint, next setpoint, start of block, end of block, block, and blocklog row 
			setpoint = float(blocklog[0][2].split(',')[chamber-2])
			next_setpoint = float(blocklog[1][2].split(',')[chamber-2])
			row_start = 0
			row_end = float(blocklog[0][4])
			block = 1
			block_row = 1
			start_time = 0
			end_time = 0
			new_block_r = []
			block_r = [['Block', 'Mean', 'SD', 'SE', 'Block Start', 'Block End', 'Start Time', 'End Time', 'n']]
			for row in df.itertuples():
				# if element is a number (not a NaN) then add to block
				if not math.isnan(row[chamber]):
					new_block_r.append(row[chamber])
					end_time = row[1]
				# if the end of the block has been reached, save stats on that block
				if row[1] >= row_end and len(new_block_r) >= 1:
					num = len(new_block_r)
					mean = numpy.mean(new_block_r)
					sd = numpy.std(new_block_r)
					sem = sd / numpy.sqrt(num)
					# compare current and next setpoint, if greater then it is a block period, if less then it is a dilution period (marked as 0)
					if sum(setpoint) > sum(next_setpoint):
						block_r.append([block, mean, sd, sem, row_start, row_end, start_time, end_time, num])
						block += 1
					else:
						block_r.append([0, mean, sd, sem, row_start, row_end, start_time, end_time, num])
					# iterate to next blocklog row, start of block, end of block, setpoint, and next setpoint
					block_row += 1
					row_start = row_end
					setpoint = next_setpoint
					try:
						row_end = float(blocklog[block_row][4])
						next_setpoint = float(blocklog[block_row][2].split(',')[chamber-2])
					except:
						row_end = numpy.mean(df.tail(2)['Time'])
						next_setpoint = float(blocklog[block_row-2][2].split(',')[chamber-2])
					new_block_r = []
					start_time = row[1]
			stats = pandas.DataFrame(block_r)
			stats.to_csv(path_or_buf='{}/ch{}.csv'.format(output, chamber-1), index=False, header=False)
	# otherwise separate stats by hour
	else:
		# for each chamber, iterate through dataframe to calculate stats
		for chamber in range(2, 10):
			start_time = 0
			end_time = 0
			new_block_r = []
			# multiple default 1 hour by command line argument
			hour = 1 * float(interval)
			block_r = [['Hour', 'Mean', 'SD', 'SE', 'Start Time', 'End Time', 'n']]
			for row in df.itertuples():
				# if element is a number (not a NaN) then add to block
				if not math.isnan(row[chamber]):
					new_block_r.append(row[chamber])
					end_time = row[1]
				# if the end of the hour unit has been reached, then save stats on that hour
				if row[1] >= hour and len(new_block_r) >= 1:
					num = len(new_block_r)
					mean = numpy.mean(new_block_r)
					sd = numpy.std(new_block_r)
					sem = sd / numpy.sqrt(num)
					block_r.append([hour, mean, sd, sem, start_time, end_time, num])
					# multiple default 1 hour by command line argument
					hour += 1 * float(interval)
					new_block_r = []
					start_time = row[1]
			stats = pandas.DataFrame(block_r)
		stats.to_csv(path_or_buf='{}/ch{}.csv'.format(output, chamber-1), index=False, header=False)


def graphs(args, intake, output, limits):
	"""
	Creates a scatter plot for each chamber based on defined x and y limits and a data set csv.

	:param args: command line argument array for error bar and data set parsing
	:param intake: path to data
	:param output: path for export
	:param limits: x and y limits to use for graphs
	"""
	if '2' in args.graph or '4' in args.graph:
		for chamber in range(1, 9):
			df = pandas.read_csv('{}/ch{}.csv'.format(intake, chamber), header=1, names=['Hour', 'Mean', 'SD', 'SE', 'Start Time', 'End Time', 'n'])
			if args.sd:
				df.plot.scatter(x='Hour', y='Mean', yerr='SD')
			elif args.se:
				df.plot.scatter(x='Hour', y='Mean', yerr='SE')
			else:
				df.plot.scatter(x='Hour', y='Mean')
			# If x or y limits are not zero, then resize graph to the inputted limits
			if limits[0] != limits[1]:
				plt.xlim(limits[0], limits[1])
			if limits[2] != limits[3]:
				plt.ylim(limits[2], limits[3])
			plt.savefig('{}/ch{}.png'.format(output, chamber))
			plt.close()
	else:
		df = pandas.read_csv('{}.csv'.format(intake), header=None, names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
		for chamber in range(1, 9):
			df.plot.scatter(x='Time', y='{}'.format(chamber))
			# If x or y limits are not zero, then resize graph to the inputted limits
			if limits[0] != limits[1]:
				plt.xlim(limits[0], limits[1])
			if limits[2] != limits[3]:
				plt.ylim(limits[2], limits[3])
			plt.savefig('{}/ch{}.png'.format(output, chamber))
			plt.close()
			

def log_functions(args, process_log, exp):
	"""
	Prints and/or updates the log of processes from this growth rate program based on command line arguments.

	:param args: command line argument array for deciding print and/or file write-out
	:param process_log: log for keeping track of processes
	:param exp: path to experiment
	"""
	if args.print:
		print(process_log)
	if args.log:
		# if previous process log file found, save contents before overwriting
		if os.path.exists(exp + paths['log processes'] + '.log'):
			process_log += '\nPrevious process log found, will add to content.'
			with open(exp + paths['log processes'] + '.log', 'r') as log_file:
				old_log = log_file.read()
				process_log = process_log + '\n\n' + old_log
			log_file.close()
		else:
			process_log += '\nNo process log found, will create new.'
		with open(exp + paths['log processes'] + '.log', 'w') as log_file:
			log_file.write(process_log)
		log_file.close()


main()
