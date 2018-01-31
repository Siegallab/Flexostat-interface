import numpy
import matplotlib.pyplot as plt
import pandas
import os
import argparse
import warnings
import csv
from datetime import datetime

# Allows warnings from divide by zero or log/ln negative number to be caught in try except
warnings.filterwarnings('error')

# TODO Add command line argument parser if easier than current method
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
				description="""\ 
		Growth Rate Analysis.
		---------------------
		Select function: -p, -r, -s
		Select data set: -u, -o
		
		Optional parameters: -t, -x, -y
		Optional path changes: -r, -c
					""")

parser.add_argument('-u', '--u', action='store_true', help='specify dilutions data set')
parser.add_argument('-o', '--od', action='store_true', help='specify optical density data set')

parser.add_argument('-p', '--parse', action='store_true', help='parse log file into clean data set')
parser.add_argument('-r', '--rate', action='store_true', help='calculate growth rate from data set')
parser.add_argument('-s', '--stats', action='store_true', help='calculate mean, SD, and SE from data set')

# parser.add_argument('-t', '--time', default='1',
# 					help='convert machine time into specified hour interval (default: 1)')
# parser.add_argument('-x', '--xlim', default='0-0', help='limit data to upper and lower bound x')
# parser.add_argument('-r', '--recent', help='use most recent experiment')
parser.add_argument('-c', '--config', default='config-growth.csv',
					help='change config file (default: config-growth.csv)')

args = parser.parse_args()

def main():
	"""
	Read in config file and determine what functions in program to run.
	Replace variables with command line inputs as need while progressing through.
	"""
	# print current date and time of run
	print('\n[growth-pipe] start main at' + datetime.now().strftime("%Y-%m-%d %H:%M"))
	# read in config file and save paths to array
	paths = []
	with open(args.config) as file:
		reader = csv.reader(file)
		for row in reader:
			paths.append(row[1])
	# combine data directory and experiment directory into string
	exp = '{}/{}/'.format(paths[1], paths[2])

	# if no data set specified, then skip functions of program
	if not args.u and not args.od:
		print('ERROR: Data set not specified.')
	# parse function takes log file and exports u/od csv
	elif args.parse:
		with open(args.input) as f:  # open input file
			log = f.read()
		if args.u:
			print('Parsing u from log file...')
			udata = parse_u(log)

			ufile = open(exp + paths[4], 'wb')
			wru = csv.writer(ufile, quoting=csv.QUOTE_ALL)
			for u in udata:
				wru.writerow(u)
			ufile.close()
		else:
			print('Parsing od from log file...')
			oddata = parse_od(log)

			odfile = open(exp + paths[8], 'wb')
			wrod = csv.writer(odfile, quoting=csv.QUOTE_ALL)
			for od in oddata:
				wrod.writerow(od)
			odfile.close()
		f.close()
		print('Parsed csv created and exported.')
	# rate function takes u/od csv and exports u/od growth rate csv
	elif args.rate:
		if args.u:
			print('Growth rates for u calculating...')
			machine_to_human(exp + paths[4], exp + paths[5])
			r_u_csv(exp + paths[4], exp + paths[6])
		else:
			print('Growth rates for od calculating...')
			machine_to_human(exp + paths[8], exp + paths[9])
			r_od_csv(exp + paths[8], exp + paths[10])
		print('Growth rates calculated and exported.')
	# stats function takes u/od growth rate csv and exports a csv for each chamber
	elif args.stats:
		if args.u:
			print('Stats for u calculating...')
			growth_rate_statistics(exp + paths[6], exp + paths[7])
		else:
			print('Stats for od calculating...')
			growth_rate_statistics(exp + paths[10], exp + paths[11])
		print('Stats csv calculated and exported.')

	print('Program end.\n')


def machine_to_human(intake, output):
	"""
	Converts machine time (seconds with starting time long ago) to hours from experiment start.
	Generates new csv and renames the old csv.

	:param intake: path to data
	:param output: path for export
	"""
	df = pandas.read_csv('{}.csv'.format(intake), header=None,
							names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	time_start = df.iloc[0, 0]
	# Checks if the first time point is in machine time
	if time_start > 1:
		print('Data set is using machine time. Converting to human time...')
		# Renames the csv using machine time
		command = 'mv {0}.csv {1}.csv'.format(intake, output)
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
		numpy.savetxt('{}.csv'.format(input), new_data, delimiter=",")
		print('Data set is using machine time. Data set with human time created.')
	else:
		print('Data set is using human time.')


def update_io_and_path(args, input, output, function):
	"""
	Replaces input and output variables from the config if there are command line arguments to replace them.
	Creates the folder for output stats or graphs if it there is none.

	:param args: all command line arguments
	:param input: config file input variable
	:param output: config file output variable
	:param function: the type of function
	:return: newly updated input and output variables
	"""
	# Replace input and output command line arguments as needed
	if args.input:
		input = args.input
	if args.output:
		output = args.output
	# if not output directory is stated for stats and graphs then format path based on input
	elif not args.output and (function == 'stats' or function == 'graphs'):
		directories = args.input.split('/')
		output = ''
		for dir in range(0, len(directories)-1):
			output += directories[dir] + '/'
		output += directories[-1].split('.csv')[0]

	lim_str = ''
	limits = [0.0, 0.0, 0.0, 0.0]
	# graphs will have x and y limits parsed and used for the output directory
	if function == 'graphs':
		if args.xlim:
			limits[0] = float(args.xlim.split("-")[0])
			limits[1] = float(args.xlim.split("-")[1])
			lim_str = ' x ' + args.xlim
		if args.ylim:
			limits[2] = float(args.xlim.split("-")[0])
			limits[3] = float(args.xlim.split("-")[1])
			lim_str = lim_str + ' y ' + args.ylim

	# stats and graphs will create an output directory if none exists
	if function == 'stats' or function == 'graphs':
		if not os.path.exists('{}{}'.format(output, lim_str)):
			os.system('mkdir {}{}'.format(output, lim_str))
			print('Output folder not found, made new folder.')
		else:
			print('Output folder found, will overwrite previous graphs.')
		output = '{}{}'.format(output, lim_str)

	return input, output, limits


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
		if args.begin and args.end:
			d2 = d2[args.begin:args.end]
		elif args.begin:
			d2 = d2[args.begin:]
		elif args.end:
			d2 = d2[:args.end]
		data.append(tuple(d2))
	print('')
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
		if args.begin and args.end:
			d2 = d2[args.begin:args.end]
		elif args.begin:
			d2 = d2[args.begin:]
		elif args.end:
			d2 = d2[:args.end]
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
			else:
				new_block_r.append(row[chamber])
		stats = pandas.DataFrame(block_r)
		stats.to_csv(path_or_buf='{}/ch{}.csv'.format(output, chamber), index=False)
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
