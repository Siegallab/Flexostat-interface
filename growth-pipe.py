
"""
BACKGROUND

	Created January 31, 2018
		by David Klein, building on previous code from Maxwell Raderstorf
		contributions found at https://github.com/Siegallab/Flexostat-interface
	An open source feature contribution to the Klavins Lab Flexostat project
		project found at https://github.com/Flexostat/Flexostat-interface

INSTRUCTIONS

	Run using Python 3.6 on the command line as such
	$ python3.6 growth-pipe.py -h
"""

import numpy
import matplotlib.pyplot as plt
import pandas
import os
import argparse
import warnings
import csv
from datetime import datetime

def main():
	# Allows warnings from divide by zero or log/ln negative number to be caught in try except
	warnings.filterwarnings('error')

	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
					description="""
			Growth Rate Analysis.
			---------------------
			Select at least one data set: -u, -o
			Select at least one function: -p, -r, -s
			
			Optional path changes: -c, -l, --print
						""")

	parser.add_argument('-u', '--u', action='store_true', help='specify dilutions data set')
	parser.add_argument('-o', '--od', action='store_true', help='specify optical density data set')

	parser.add_argument('-p', '--parse', action='store_true', help='parse log file into clean data set')
	parser.add_argument('-r', '--rate', action='store_true', help='calculate growth rate from data set')
	parser.add_argument('-s', '--stats', action='store_true', help='calculate mean, SD, and SE from data set')

	# parser.add_argument('-t', '--time', default='1',
	# 					help='convert machine time into specified hour interval (default: 1)')
	# parser.add_argument('-x', '--xlim', default='0-0', help='limit data to upper and lower bound x')
	parser.add_argument('-c', '--config', default='config-growth.csv',
						help='change config file (default: config-growth.csv)')
	parser.add_argument('-l', '--log', action='store_true', help='optional save program processes log')
	parser.add_argument('--print', action='store_true', help='optional program processes printing')

	args = parser.parse_args()

	if os.path.exists(args.config):
		functions(args)
	else:
		print('ERROR: Config file not found.')
	print('Program end.\n')


def functions(args):
	"""
	Read in config file to establish paths to files.
	Determine what functions in program to run based on command line arguments.
	"""

	# read in config file and begin process log
	process_log = '\n[growth-pipe] ' + datetime.now().strftime("%Y-%m-%d %H:%M")
	paths = []
	with open(args.config) as file:
		reader = csv.reader(file)
		for row in reader:
			if row[1][-1] == '/':
				row[1] = row[1][:-1]
			paths.append(row[1])

	# ensure data and experiment directories exist
	# format paths to variable appropriately
	if paths[2][-1] == "'":
		paths[2] = paths[2][:-1]
	if os.path.exists(paths[1]):
		process_log += '\nData directory found.'
	else:
		os.system("mkdir '{}'".format(paths[1]))
		process_log += '\nData directory not found. Made new one.'
	exp = '{}/{}/'.format(paths[1], paths[2])
	if os.path.exists(exp):
		process_log += '\nExperiment directory found.'
	else:
		os.system("mkdir '{}'".format(exp))
		process_log += '\nExperiment directory not found. Made new one.'

	# make sure at least one data set is specified
	if not args.u and not args.od:
		process_log += '\nERROR: Data set not specified.'
	if args.u:
		# parse function takes log file and exports u/od csv
		if args.parse:
			with open(exp + paths[3] + '.dat') as f:  # open input file
				log = f.read()

			process_log += '\nParsing u from log file...'
			udata = parse_u(log)

			# tell user if file exists and will be overwritten or if new file will be made
			if os.path.exists(exp + paths[4] + '.csv'):
				process_log += '\nOutput file exists, will overwrite.'
			else:
				process_log += '\nOutput file not found, will make new file.'

			ufile = open(exp + paths[4] + '.csv', 'w')
			wru = csv.writer(ufile, quoting=csv.QUOTE_ALL)
			for u in udata:
				wru.writerow(u)

			f.close()
			ufile.close()
			process_log += '\nParsed csv created and exported.'
		# rate function takes u/od csv and exports u/od growth rate csv
		if args.rate:
			process_log += '\nGrowth rates for u calculating...'
			process_log = machine_to_human(exp + paths[4], exp + paths[5], process_log)

			# tell user if file exists and will be overwritten or if new file will be made
			if os.path.exists(exp + paths[6] + '.csv'):
				process_log += '\nOutput file exists, will overwrite.'
			else:
				process_log += '\nOutput file not found, will make new file.'

			r_u_csv(exp + paths[4], exp + paths[6])
			process_log += '\nGrowth rates calculated and exported.'
		# stats function takes u/od growth rate csv and exports a csv for each chamber
		if args.stats:
			process_log += '\nStats for u calculating...'
			dead, dead, process_log = validate_output_path(args, exp + paths[7], False, process_log)
			growth_rate_statistics(exp + paths[6], exp + paths[7])
			process_log += '\nStats csv calculated and exported.'
	if args.od:
		# parse function takes log file and exports u/od csv
		if args.parse:
			process_log += '\nParsing od from log file...'
			with open(exp + paths[3] + '.dat') as f:  # open input file
				log = f.read()

			oddata = parse_od(log)

			# tell user if file exists and will be overwritten or if new file will be made
			if os.path.exists(exp + paths[8] + '.csv'):
				process_log += '\nOutput file exists, will overwrite.'
			else:
				process_log += '\nOutput file not found, will make new file.'

			odfile = open(exp + paths[8] + '.csv', 'w')
			wrod = csv.writer(odfile, quoting=csv.QUOTE_ALL)
			for od in oddata:
				wrod.writerow(od)

			f.close()
			odfile.close()
			process_log += '\nParsed csv created and exported.'
		# rate function takes u/od csv and exports u/od growth rate csv
		if args.rate:
			process_log += '\nGrowth rates for od calculating...'
			process_log = machine_to_human(exp + paths[8], exp + paths[9], process_log)

			# tell user if file exists and will be overwritten or if new file will be made
			if os.path.exists(exp + paths[10] + '.csv'):
				process_log += '\nOutput file exists, will overwrite.'
			else:
				process_log += '\nOutput file not found, will make new file.'

			r_od_csv(exp + paths[8], exp + paths[10])
			process_log += '\nGrowth rates calculated and exported.'
		# stats function takes u/od growth rate csv and exports a csv for each chamber
		if args.stats:
			process_log += '\nStats for od calculating...'
			dead, dead, process_log = validate_output_path(args, exp + paths[11], False, process_log)
			growth_rate_statistics(exp + paths[10], exp + paths[11])
			process_log += '\ntats csv calculated and exported.'

	# print and save process log
	if args.print:
		print(process_log)
	if args.log:
		# if previous process log file found, save contents before overwriting
		if os.path.exists(exp + paths[12] + '.txt'):
			process_log += '\nPrevious process log found, will add to content.'
			with open(exp + paths[12] + '.txt', 'r') as log_file:
				old_log = log_file.read()
				process_log = process_log + '\n\n' + old_log
			log_file.close()
		else:
			process_log += '\nNo process log found, will create new.'
		with open(exp + paths[12] + '.txt', 'w') as log_file:
			log_file.write(process_log)
		log_file.close()


def machine_to_human(intake, output, process_log):
	"""
	Converts machine time (seconds with starting time long ago) to hours from experiment start.
	Generates new csv and renames the old csv.

	:param intake: path to data
	:param output: path for export
	:return: returns updated log of program processes
	"""
	df = pandas.read_csv('{}.csv'.format(intake), header=None,
							names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	time_start = df.iloc[0, 0]
	# Checks if the first time point is in machine time
	if time_start > 1:
		process_log += '\nData set is using machine time. Converting to human time...'
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
		process_log += '\nData set is using machine time. Data set with human time created.'
	else:
		process_log += '\nData set is using human time.'
	
	return process_log


def validate_output_path(args, output, function, process_log):
	"""
	Creates the output folder if it there is none.

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
			limits[0] = float(args.xlim.split("-")[0])
			limits[1] = float(args.xlim.split("-")[1])
			lim_str = ' x ' + args.xlim
		if args.ylim:
			limits[2] = float(args.xlim.split("-")[0])
			limits[3] = float(args.xlim.split("-")[1])
			lim_str = lim_str + ' y ' + args.ylim

	# create an output directory if none exists
	if not os.path.exists('{}{}'.format(output, lim_str)):
		os.system("mkdir '{}{}'".format(output, lim_str))
		process_log += '\nOutput folder not found, made new folder.'
	else:
		process_log += '\nOutput folder found, will overwrite previous files.'
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


def r_u_csv(intake, output):
	"""
	Calculates growth rate data based on dilutions (u) and saves to csv.

	:param intake: path to data
	:param output: path for export
	"""
	df = pandas.read_csv('{}.csv'.format(intake), header=None,
							names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
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
				new_row.append(round((numpy.log(1 + (element / 15000)) / time_difference), 6))
		new_data_r.append(new_row)

	numpy.savetxt('{}.csv'.format(output), new_data_r, delimiter=",")


def r_od_csv(experiment, output):
	"""
	Calculates growth rate data based on optical density (od) and saves to csv.

	:param intake: path to data
	:param output: path for export
	"""
	df = pandas.read_csv('{}.csv'.format(experiment), header=None,
							names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
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
					new_row.append(round((numpy.log(element / previous_od[ch_count]) / time_difference), 6))
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


def growth_rate_statistics(intake, output):
	"""
	Analyzes growth rate csv for general statistics (averages, standard deviation, and standard error).

	:param intake: path to data
	:param output: path for export
	"""
	df = pandas.read_csv('{}.csv'.format(intake), header=None,
	                     names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])

	for chamber in range(2, 10):
		new_block_r = []
		hour = 1
		block_r = []
		for row in df.itertuples():
			if row[1] >= hour:
				sem = numpy.std(new_block_r) / numpy.sqrt(len(new_block_r))
				block_r.append([hour, numpy.mean(new_block_r), numpy.std(new_block_r), sem])
				hour += 1
				new_block_r = []
			new_block_r.append(row[chamber])
		stats = pandas.DataFrame(block_r)
		stats.to_csv(path_or_buf='{}/ch{}.csv'.format(output, chamber-1), index=False)
	# generate_graphs('{}_stats'.format(data_set), output, output, '00-00-00', file_prefix)

	# TODO generate graphs for statistics


def generate_graphs(intake, output, limits):
	"""
	Creates a scatter plot for each chamber based on defined x and y limits and a data set csv.

	:param intake: path to data
	:param output: path for export
	:param limits: x and y limits to use for graphs
	"""
	df = pandas.read_csv('{}.csv'.format(intake), header=None,
							names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	for chamber in range(1, 9):
		df.plot.scatter(x='Time', y='{}'.format(chamber))
		# If x or y limits are not zero, then resize graph to the inputted limits
		if limits[0] != limits[1]:
			plt.xlim(limits[0], limits[1])
		if limits[2] != limits[3]:
			plt.ylim(limits[2], limits[3])
		plt.savefig('{}/ch{}.png'.format(output, chamber))
		plt.close()


main()
