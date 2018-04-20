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

import matplotlib.pyplot as plt
from datetime import datetime
import argparse
import warnings
import pandas
import numpy
import math
import json
import csv
import os


def main():
	"""
	Defines the command line arguments intaken by the program.
	Ensures there is a config file to work with before calling the 'functions' function.
	"""
	# Allows warnings from divide by zero or log/ln negative number to be caught in try except
	warnings.filterwarnings('error')
	args = command_line_parameters()

	if os.path.exists(args.config):
		paths, process_log = config_variables(args)
		process_log = functions(args, paths, process_log)
		# print and save process log
		log_functions(args, paths, process_log)
	else:
		print('ERROR: Config file not found.')
	print('Growth-Pipe.py end.\n')


def command_line_parameters():
	"""
	Takes in command line argument parameters and displays help descriptions.

	:return: variable containing all command line argument parameters
	"""
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
					description="""
	Growth Rate Analysis Pipeline
	-----------------------------
	Select at least one function: --parse [u, od, odlog], --growth [u, od], 
		--stats [u, od, u_growth, od_growth], --block [u_growth, od_growth]
		--graph [u, od, u_stats, od_stats, u_growth, od_growth, u_growth_stats, od_growth_stats, u_block, od_block]

	Single inputs: --parse u --growth u
	Multiple inputs: --parse u od --growth u od

	Optional changes: --config, --log, --print
	Optional stats parameters: --interval (-i)
	Optional graph parameters: --xlim (-x), --ylim (-y), --sd, --se
				""")

	parser.add_argument('--parse', nargs='+', help='parse data set from log file')
	parser.add_argument('--growth', nargs='+', help='calculate growth rate from data set')
	parser.add_argument('--stats', nargs='+', help='calculate mean, SD, and SE from data set in interval')
	parser.add_argument('--block', nargs='+', help='calculate mean, SD, and SE from growth data set in block')
	parser.add_argument('--graph', nargs='+', help='graph specified data')

	parser.add_argument('--config', default='config-growth.csv',
						help="change config file from default 'config-growth.csv'")
	parser.add_argument('--log', action='store_true', help='optional save program processes to log text file')
	parser.add_argument('--print', action='store_true', help='optional program processes printing')

	parser.add_argument('-i', '--interval', default='1',
						help="modify default hour time interval for stats by multiplication (e.g. '-i 0.5' = 30 min, '-i 2' = 2 hrs)")
	parser.add_argument('--sd', action='store_true', help='display standard deviation bars on graphs')
	parser.add_argument('--se', action='store_true', help='display standard error bars on graphs')
	parser.add_argument('-x', '--xlim', default='0-0', help="limit data to upper and lower bound x (e.g. '-x 5-10')")
	parser.add_argument('-y', '--ylim', default='0-0', help="limit data to upper and lower bound y (e.g. '-y 5-10')")

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
		'' : '', 'fulllog' : '', 'odlog' : '', 'blank' : '', 'block' : '',
		'log_processes' : '', 'data_directory' : '', 'experiment' : '', 
		# dilution local variables
		'u' : '', 'u_stats' : '', 'u_machine_time' : '',
		'u_growth' : '', 'u_growth_stats' : '', 'u_block' : '',
		# optical density local variables
		'od' : '', 'od_stats' : '', 'od_machine_time' : '', 
		'od_growth' : '', 'od_growth_stats' : '', 'od_block' : '',
		# dilution graph local variables
		'u_graphs' : '', 'u_stats_graphs' : '', 'u_growth_graphs' : '',
		 'u_growth_stats_graphs' : '', 'u_block_graphs' : '',
		# optical density graph local variables
		'od_graphs' : '', 'od_stats_graphs' : '', 'od_growth_graphs' : '',
		 'od_growth_stats_graphs' : '', 'od_block_graphs' : ''
	}
	# loop through growth config file to collect Data and Experiment folder path
	with open(args.config) as config_file:
		reader = csv.reader(config_file)
		for row in reader:
			# removes any ending slashes that may exist in csv
			if row[1][-1] == '/':
				row[1] = row[1][:-1]
			paths[row[0]] = row[4]

	# ensure data and experiment directories exist
	# format paths to variable appropriately
	if paths['experiment'][-1] == "'":
		paths['experiment'] = paths['experiment'][:-1]
	if os.path.exists(paths['data_directory']):
		process_log += '\nData directory found.'
	else:
		os.system("mkdir '{}'".format(paths['data_directory']))
		process_log += '\nData directory not found. Made new one.'
	exp = '{}/{}/'.format(paths['data_directory'], paths['experiment'])
	if os.path.exists(exp):
		process_log += '\nExperiment directory found.'
	else:
		os.system("mkdir '{}'".format(exp))
		process_log += '\nExperiment directory not found. Made new one.'

	# loop through growth config file to collect all other paths and add experiment path to their beginning
	with open(args.config) as config_file:
		reader = csv.reader(config_file)
		for row in reader:
			# removes any ending slashes that may exist in csv
			if row[1][-1] == '/':
				row[1] = row[1][:-1]
			if not row[1] in ['data_directory', 'experiment']:
				paths[row[0]] = exp + row[1]
			if len(row[4]) >= 1:
				if row[4][-1] == '/':
					row[4] = row[1][:-1]
			paths[row[3]] = row[4]
	config_file.close()

	return paths, process_log


def functions(args, paths, process_log):
	"""
	Runs all functions specified by the command line arguments using the config file variables, while taking note in the log variable.

	:param args: list of command line arguments
	:param paths: list with config file paths
	:param process_log: log for keeping track of processes
	:return: log of all processes that were run
	"""
	if args.parse:
		for i in args.parse:
			if i in ['u', 'od']:
				parse(paths['fulllog'], paths[i], i)
				machine_to_human(paths[i], paths[i + '_machine_time'])
				process_log += '\n\tParsed csv created and exported.'
			elif i == 'odlog':
				parse_odlog(paths['odlog'], paths['blank'], paths['od'])
				machine_to_human(paths['odlog'], paths['od_machine_time'])
				process_log += '\n\tParsed csv created and exported.'
	if args.growth:
		for i in args.growth:
			if i in ['u', 'od']:
				u_growth(paths['u'], paths[i + '_growth'])
				process_log += '\n\tGrowth rates csv calculated and exported.'
	if args.stats:
		for i in args.stats:
			if i in ['u', 'od', 'u_growth', 'od_growth']:
				validate_output_path(args, paths['u growth statistics'], False)
				stats(paths[i], paths[i + '_graphs'], args.interval)
				process_log += '\n\tStats csv calculated and exported.'
	if args.block:
		for i in args.block:
			if i in ['u_growth', 'od_growth']:
				block(paths[i], paths[i[0] + '_block'], paths['od'])
				process_log += '\n\Block stats csv calculated and exported.'
	if args.graph:
		for i in args.block:
			bars = ''
			if i in ['u_stats', 'od_stats', 'u_growth_stats', 'od_growth_stats', 'u_block', 'od_block']:
				if args.se:
					bars = 'SE'
				elif args.sd:
					bars = 'SD'
			if i in ['u', 'od', 'u_growth', 'od_growth', 'u_stats', 'od_stats', 'u_growth_stats', 'od_growth_stats', 'u_block', 'od_block']:
				output, limits = validate_output_path(args, paths[i + '_graphs'], True)
				graph(paths[i], output, limits, bars)
				process_log += '\n\Graphs exported.'
	return process_log


def machine_to_human(intake, output):
	"""
	Converts machine time (seconds with starting time long ago) to hours from experiment start.
	Generates new csv and renames the old csv.

	:param intake: path to data
	:param output: path for export
	"""
	df = pandas.read_csv('{}'.format(intake), header=None,
							names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	time_start = df.iloc[0, 0]
	# Checks if the first time point is in machine time
	if time_start > 1:
		# Renames the csv using machine time
		command = "mv '{}' '{}'".format(intake, output)
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
		numpy.savetxt('{}'.format(intake), new_data, delimiter=",")


def validate_output_path(args, output, function):
	"""
	Creates the output folder if there is none.
	Parses limits for graphs based on command line parameters.

	:param args: command line argument array for limit parsing
	:param output: path for export
	:param function: specify true if function is graphs for limit parsing
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
	output = '{}{}'.format(output, lim_str)

	return output, limits


def parse(intake, output, dataset):
	"""
	Parses OD or U values from the fulllog file.

	:param intake: path to data
	:param output: path for export
	:param dataset: either OD or U values to parse
	"""
	if dataset == 'od':
		dataset = 'ods'
	logfile = open(intake, 'r')  # open input file
	logdata = logfile.readlines()
	logfile.close()

	data = []
	for line in logdata:
		if len(line) > 0:
			temp_data = json.loads(line)
			data.append([temp_data['timestamp']] + temp_data[dataset])
	ufile = open(output, 'w')
	writer = csv.writer(ufile)
	writer.writerows(data)
	ufile.close()


def parse_odlog(odlog, blank, output):
	"""
	Parses optical density values from the odlog file.

	:param odlog: path to od data
	:param blank: path to blank od data
	:param output: path for export
	"""
	blank_file = open(blank, 'r')
	blank_content = blank_file.read()
	blank_file.close()
	blank_data = list(map(int, blank_content.split()))
	btx = blank_data[0::2]
	brx = blank_data[1::2]

	odlog_file = open(odlog, 'r')
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
			temp_ods.append(math.log10(blank_od/od_measure))
		od_list.append(temp_ods)
	odfile = open(output, 'w')
	wrod = csv.writer(odfile, quoting=csv.QUOTE_ALL)
	wrod.writerows(od_list)
	odfile.close()


def u_growth(intake, output):
	"""
	Calculates growth rate data based on dilutions (u) and saves to csv.

	:param intake: path to data
	:param output: path for export
	"""
	df = pandas.read_csv('{}'.format(intake), header=None, names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
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

	numpy.savetxt('{}'.format(output), new_data_r, delimiter=",")


def od_growth(intake, output):
	"""
	Calculates growth rate data based on optical density (od) and saves to csv.

	:param intake: path to data
	:param output: path for export
	"""
	df = pandas.read_csv('{}'.format(intake), header=None, names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
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
	df.to_csv(path_or_buf='{}'.format(output), index=False)


def stats(intake, output, interval):
	"""
	Analyzes growth rate csv for general statistics (averages, standard deviation, and standard error).

	:param intake: path to data
	:param output: path for export
	:param interval: modify default hour time interval by multiplication
	"""
	df = pandas.read_csv('{}'.format(intake), header=None, names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	# for each chamber, iterate through dataframe to calculate stats
	for chamber in range(2, 10):
		start_time = 0
		end_time = 0
		new_block = []
		# multiple default 1 hour by command line argument
		hour = 1 * float(interval)
		block = [['Hour', 'Mean', 'SD', 'SE', 'Start Time', 'End Time', 'n']]
		for row in df.itertuples():
			# if element is a number (not a NaN) then add to block
			if not math.isnan(row[chamber]):
				if len(new_block) == 0:
					start_time = row[1]
				new_block.append(row[chamber])
				end_time = row[1]
			# if the end of the hour unit has been reached, then save stats on that hour
			if row[1] >= hour and len(new_block) >= 1:
				num = len(new_block)
				mean = numpy.mean(new_block)
				sd = numpy.std(new_block)
				sem = sd / numpy.sqrt(num)
				block.append([hour, mean, sd, sem, start_time, end_time, num])
				# multiple default 1 hour by command line argument
				hour += 1 * float(interval)
				new_block = []
		stats = pandas.DataFrame(block)
		stats.to_csv(path_or_buf='{}/ch{}.csv'.format(output, chamber-1), index=False, header=False)


def block(intake, output, od_raw):
	"""
	Analyzes growth rate csv for general statistics (averages, standard deviation, and standard error).

	:param intake: path to data
	:param output: path for export
	:param od_raw: optical density data for use in block analysis
	"""
	df = pandas.read_csv('{}'.format(intake), header=None, names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	# block information format: [date, time, schedule or chamber, new setpoints for chambers, human time (hr), experiment time, current ODs]
	# for each chamber, will iterate through dataframe and iterate through blocklog data as each block time is reached
	blocklog_file = open(block, 'r')
	blocklog = csv.reader(blocklog_file)
	blocklog_file.close()
	if blocklog[0][2] == 'schedule':
		for chamber in range(2, 10):
			# for first blocklog row, define setpoint, next setpoint, start of block, end of block, block, and blocklog row 
			setpoint = float(blocklog[0][2].split(',')[chamber-2])
			next_setpoint = float(blocklog[1][2].split(',')[chamber-2])
			block_append = [0, float(blocklog[0][4]), 0, 0]
			new_block = []
			block_row = 1
			od_block = 1
			u_block = 1
			growth = True
			max_reached = False
			min_reached = False
			ods = pandas.read_csv('{}'.format(od_raw), header=None, names=['Time', 1, 2, 3, 4, 5, 6, 7, 8])
			block_od = [['Block', 'Mean', 'SD', 'SE', 'Block Start', 'Block End', 'Start Time', 'End Time', 'n']]
			block_u = [['Block', 'Upper or Lower' 'Mean', 'SD', 'SE', 'Block Start', 'Block End', 'Start Time', 'End Time', 'n']]
			for row in df.itertuples():
				# if element is a number (not a NaN) then add to block
				if not math.isnan(row[chamber]):
					if len(new_block) == 0:
						block_append[2] = row[1]
					new_block.append(row[chamber])
					block_append[3] = row[1]
				# if in the growth phase and the max is reached for the first time, save the block as an OD block
				if growth and not max_reached and ods.loc[ods['Time'] == row[1]][chamber-2] >= (setpoint-setpoint*0.05) and len(new_block) >= 1:
					num = len(new_block)
					mean = numpy.mean(new_block)
					sd = numpy.std(new_block)
					sem = sd / numpy.sqrt(num)
					block_od.append([od_block, mean, sd, sem] + block_append + [num])
					od_block += 1
					max_reached = True
					new_block = []
				# if the lower minimum setpoint is reached, reset the list of elements for the next U block
				if not growth and not min_reached and ods.loc[ods['Time'] == row[1]][chamber-2] <= (setpoint+setpoint*0.05):
					min_reached = True
					new_block = []
				# if the end of the block has been reached, save stats on that block as a U block
				if row[1] >= block_append[1] and len(new_block) >= 1:
					num = len(new_block)
					mean = numpy.mean(new_block)
					sd = numpy.std(new_block)
					sem = sd / numpy.sqrt(num)
					# compare current and next setpoint, if greater then it is a block period, if less then it is a dilution period
					if sum(setpoint) > sum(next_setpoint):
						growth = False
						min_reached = False
						block_u.append([u_block, 'Upper', mean, sd, sem] + block_append + [num])
					else:
						growth = True
						max_reached = False
						block_u.append([u_block, 'Lower', mean, sd, sem] + block_append + [num])
					u_block += 1
					# iterate to next blocklog row, start of block, end of block, setpoint, and next setpoint
					new_block = []
					block_row += 1
					block_append[0] = block_append[1]
					setpoint = next_setpoint
					try:
						block_append[1] = float(blocklog[block_row][4])
						next_setpoint = float(blocklog[block_row][2].split(',')[chamber-2])
					except:
						block_append[1] = numpy.mean(df.tail(2)['Time'])
						next_setpoint = float(blocklog[block_row-2][2].split(',')[chamber-2])
			stats = pandas.DataFrame(block_od)
			stats.to_csv(path_or_buf='{}/od_ch{}.csv'.format(output, chamber-1), index=False, header=False)
			stats = pandas.DataFrame(block_u)
			stats.to_csv(path_or_buf='{}/u_ch{}.csv'.format(output, chamber-1), index=False, header=False)
	else:
		for chamber in range(2, 10):
			# for first blocklog row, define setpoint, next setpoint, start of block, end of block, block, and blocklog row 
			setpoint = float(blocklog[0][2].split(',')[chamber-2])
			next_setpoint = float(blocklog[1][2].split(',')[chamber-2])
			# block append holds [start of the block from blocklog, end of the block from blocklog, starting element time, and ending element time]
			block_append = [0, float(blocklog[0][4]), 0, 0]
			new_block = []
			growth_block = 1
			dilution_block = 1
			block_row = 1
			block = [['Growth or Dilution', 'Block', 'Mean', 'SD', 'SE', 'Block Start', 'Block End', 'Start Time', 'End Time', 'n']]
			block_od = [['Block', 'Mean', 'SD', 'SE', 'Block Start', 'Block End', 'Start Time', 'End Time', 'n']]
			for row in df.itertuples():
				# if element is a number (not a NaN) then add to block
				if not math.isnan(row[chamber]):
					if len(new_block) == 0:
						block_append[2] = row[1]
					new_block.append(row[chamber])
					block_append[3] = row[1]
				# if the end of the block has been reached, save stats on that block
				if row[1] >= block_append[1] and len(new_block) >= 1:
					num = len(new_block)
					mean = numpy.mean(new_block)
					sd = numpy.std(new_block)
					sem = sd / numpy.sqrt(num)
					# compare current and next setpoint, if greater then it is a block period, if less then it is a dilution period
					if sum(setpoint) > sum(next_setpoint):
						block.append(['Growth', growth_block, mean, sd, sem] + block_append + [num])
						block_od.append([growth_block, mean, sd, sem] + block_append + [num])
						growth_block += 1
					else:
						block.append(['Dilution', growth_block, mean, sd, sem] + block_append + [num])
						dilution_block += 1
					# iterate to next blocklog row, start of block, end of block, setpoint, and next setpoint
					new_block = []
					block_row += 1
					block_append[0] = block_append[1]
					setpoint = next_setpoint
					try:
						block_append[1] = float(blocklog[block_row][4])
						next_setpoint = float(blocklog[block_row][2].split(',')[chamber-2])
					except:
						block_append[1] = numpy.mean(df.tail(2)['Time'])
						next_setpoint = float(blocklog[block_row-2][2].split(',')[chamber-2])
			stats = pandas.DataFrame(block)
			stats.to_csv(path_or_buf='{}/ch{}.csv'.format(output, chamber-1), index=False, header=False)
			stats = pandas.DataFrame(block_od)
			stats.to_csv(path_or_buf='{}/od_ch{}.csv'.format(output, chamber-1), index=False, header=False)


def graph(intake, output, limits, bars):
	"""
	Creates a scatter plot for each chamber based on defined x and y limits and a data set csv.

	:param intake: path to data
	:param output: path for export
	:param limits: x and y limits to use for graphs
	:param bars: string of error bar type to put on graph
	"""
	for chamber in range(1, 9):
		df = pandas.read_csv('{}/ch{}.csv'.format(intake, chamber), header=1, names=['Hour', 'Mean', 'SD', 'SE', 'Start Time', 'End Time', 'n'])
		if len(bars) > 0:
			df.plot.scatter(x='Hour', y='Mean', yerr=bars)
		else:
			df.plot.scatter(x='Hour', y='Mean')
		# If x or y limits are not zero, then resize graph to the inputted limits
		if limits[0] != limits[1]:
			plt.xlim(limits[0], limits[1])
		if limits[2] != limits[3]:
			plt.ylim(limits[2], limits[3])
		plt.savefig('{}/ch{}.png'.format(output, chamber))
		plt.close()
			

def log_functions(args, paths, process_log):
	"""
	Prints and/or updates the log of processes from this growth rate program based on command line arguments.

	:param args: command line argument array for deciding print and/or file write-out
	:param paths: list with config file paths
	:param process_log: log for keeping track of processes
	"""
	if args.print:
		print(process_log)
	if args.log:
		# if previous process log file found, save contents before overwriting
		if os.path.exists(paths['log_processes']):
			process_log += '\nPrevious process log found, will add to content.'
			with open(paths['log_processes'], 'r') as log_file:
				old_log = log_file.read()
				process_log = process_log + '\n\n' + old_log
			log_file.close()
		else:
			process_log += '\nNo process log found, will create new.'
		with open(paths['log_processes'], 'w') as log_file:
			log_file.write(process_log)
		log_file.close()


main()