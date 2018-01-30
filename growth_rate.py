import numpy
import matplotlib.pyplot as plt
import pandas
import sys
import matplotlib
import os
import argparse
import warnings
import ConfigParser

# Allows warnings from divide by zero or log/ln negative number to be caught in try except
warnings.filterwarnings('error')

# TODO Add command line argument parser if easier than current method
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
				description="""\ 
		Growth Rate Analysis.
		---------------------
			- Functions use --data_directory, experiment, and config variable for input and output
				unless inactivated by -i or -o respectively
			- X and Y limits only available for --graph
					""")
# parser.add_argument('-p', '--parse',
# 					help='parser u, od, and z values')

parser.add_argument('--r_u', help='growth rate calculations based on U dilution values')
parser.add_argument('--r_od', help='growth rate calculations based on OD optical density measurements')
parser.add_argument('--stats_u', help='calculate mean, SD, and SE for growth rates based on U')
parser.add_argument('--stats_od', help='calculate mean, SD, and SE for growth rates based on OD')

parser.add_argument('--graph', help='generate graphs')
parser.add_argument('-x', '--xlim', default='0-0', help='optional upper and lower bound x limits for graphs')
parser.add_argument('-y', '--ylim', default='0-0', help='optional upper and lower bound y limits for graphs')

parser.add_argument('-i', '--input',
					help='optional input path and filename (defaults to config file)')
parser.add_argument('-o', '--output',
					help='optional output path and filename or directory for graphs (end dir with /, default to config file)')

parser.add_argument('--data_directory', help='optional set data directory (defaults to config file)')
parser.add_argument('--experiment', help='optional set experiment (defaults to config file)')
parser.add_argument('--recent', help='optional automatically set experiment to most recent in data_directory')
parser.add_argument('--config', default='growth_rate.ini',
					help='optional configuration path and filename (defaults to growth_rate.ini)')

# parser.add_argument('-c', '--compare',
#				help='compare expected vs experimental')
# parser.add_argument('-z', '--delete',
# 				help='delete most recently created files')

args = parser.parse_args()

def main():
	"""
	Read in config file and replace based on command line inputs if necessary.
	Then determines what functions in program to run based on command line inputs and config file variables.
	"""
	config = ConfigParser.SafeConfigParser()
	config.read(args.config)
	config.items('paths')

	if args.data_directory:
		config['paths']['data_dir'] = args.data_directory
	if args.experiment:
		config['paths']['experiment'] = args.experiment
	if args.recent:
		data_temp = config.get('paths', 'data_directory')
		if os.path.exists(data_temp):
			config['paths']['experiment'] = get_recent_exp(data_temp)

	data_directory = config.get('paths', 'data_directory')
	experiment = config.get('paths', 'experiment')
	log = config.get('paths', 'log')
	u = config.get('paths', 'u')
	od = config.get('paths', 'od')
	r_u = config.get('paths', 'r_u')
	r_od = config.get('paths', 'r_od')

	if not os.path.exists(data_directory):
		print('Data folder not found, made new folder.')

	if args.r_u:
		if args.input:
			config['paths']['u'] = args.input
			input_ = '{}/{}/{}'
		r_u_csv(experiment, output)
	elif args.r_od:
		r_od_csv(experiment, output)
	elif args.stats_u:
		growth_rate_statistics(experiment, output)
	elif args.stats_od:
		growth_rate_statistics()
	elif args.graph:

		limits = [0.0, 0.0, 0.0, 0.0]
		lim_str = ''
		if args.xlim:
			limits[0] = float(args.xlim.split("-")[0])
			limits[1] = float(args.xlim.split("-")[1])
			lim_str = ' x ' + args.xlim
		if args.ylim:
			limits[2] = float(args.xlim.split("-")[0])
			limits[3] = float(args.xlim.split("-")[1])
			lim_str = lim_str + ' y ' + args.ylim

		if not os.path.exists(args.data_directory):
			os.system('mkdir {}'.format(output))
			print('Graph folder not found, made new folder.')
		generate_graphs(experiment, output, limits, lim_str)
	print('Program end.')


def get_recent_exp(data_directory):
	"""
	Finds the most recent experiment directory.

	:return: Most recent experiment directory
	"""
	exp_list = os.listdir(data_directory)
	recent = '00-00-00'
	recent_split = recent.split('-')
	for exp in exp_list:
		if exp[0].isdigit():
			split = exp.split('-')
			last = split[2][0:2]
			# Compares the split up experiment dates from the Data directory
			# First compares the day, month, then year, and replaces the most recent accordingly
			if int(split[0]) > int(recent_split[0]):
				recent = exp
				recent_split = [split[0], split[1], last]
			elif split[0] == recent_split[0] and int(split[1]) > int(recent_split[1]):
				recent = exp
				recent_split = [split[0], split[1], last]
			elif split[0] == recent_split[0] and split[1] == recent_split[1] and int(last) > int(recent_split[2]):
				recent = exp
				recent_split = [split[0], split[1], last]
			else:
				continue
	print('Using data from experiment {}.'.format(recent))
	return recent


def get_output_directory(data_directory):
	"""
	Finds or creates directory for outputting graphs.

	:param location: path to experiment
	:param data_set: output data set
	:param limit_dir: x and y limits in string
	:return: directory for outputting graphs
	"""
	if not os.path.exists('{}'.format(data_directory)):
		os.system('mkdir Data/')
		print('Data folder not found, made new folder.')
	else:
		print('Analysis folder found, will overwrite previous graphs.')
	output = '{}/{}{}'.format(location, data_set, limit_dir)
	return output


def machine_to_human(experiment):
	"""
	Converts machine time (seconds with starting time long ago) to hours from experiment start.
	Generates new csv and renames the old csv.

	:param location: path to experiment
	:param data_set: csv data to convert
	:param file_prefix: any prefix before the data set in the file name
	"""
	df = pandas.read_csv('{}.csv'.format(experiment), header=None,
							names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	time_start = df.iloc[0, 0]
	# Checks if the first time point is in machine time
	if time_start > 1:
		print('Data set is using machine time. Converting to human time...')
		# Renames the csv using machine time
		command = 'mv {0}.csv {0}_machine.csv'.format(experiment)
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
		print('Data set with human time created.')
	else:
		print('Data set is using human time.')


def r_u_csv(experiment, output):
	"""
	Calculates growth rate data based on dilutions (u) and saves to csv.

	:param location: path to experiment
	:param data_set: csv data to calculate growth rate from
	:param file_prefix: any prefix before the data set in the file name
	"""
	print('Growth rate csv generating...')

	df = pandas.read_csv('{}.csv'.format(experiment), header=None,
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
	print('Growth rate csv generated and exported.')


def r_od_csv(experiment, output):
	"""
	Calculates growth rate data based on optical density (od) and saves to csv.

	:param location: path to experiment
	:param data_set: csv data to calculate growth rate from
	:param file_prefix: any prefix before the data set in the file name
	"""
	print('Growth rate csv generating...')

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
	print('Growth rate csv generated and exported.')


def growth_rate_statistics(experiment, output):
	"""
	Analyzes growth rate csv for general statistics (averages, standard deviation, and standard error).

	:param location: path to experiment
	:param data_set: growth rate csv data to analyze from
	:param file_prefix: any prefix before the data set in the file name
	"""
	print('Starting growth rate statistics...')
	output = get_output_directory(output)
	df = pandas.read_csv('{}.csv'.format(experiment), header=None,
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
		stats.to_csv(path_or_buf='{}{}.csv'.format(output, chamber), index=False)
	# generate_graphs('{}_stats'.format(data_set), output, output, '00-00-00', file_prefix)

	# TODO Add ability to define region where statistics will be calculated
	# TODO Write statistics to a file


def generate_graphs(experiment, output, limits):
	"""
	Creates a scatter plot for each chamber based on defined x and y limits and a data set csv.

	:param data_set: csv data to graph
	:param location: path to experiment
	:param output: path to directory for graph export
	:param limits: x and y limits to use for graphs
	:param file_prefix: any prefix before the data set in the file name
	"""
	print('Beginning analysis...')
	df = pandas.read_csv('{}.csv'.format(experiment), header=None,
							names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	for chamber in range(1, 9):
		df.plot.scatter(x='Time', y='{}'.format(chamber))
		# If x or y limits are not zero, then resize graph to the inputted limits
		if limits[0] != limits[1]:
			plt.xlim(limits[0], limits[1])
		if limits[2] != limits[3]:
			plt.ylim(limits[2], limits[3])
		plt.savefig('{}{}.png'.format(output, chamber))
		plt.close()
	print('Graphs have completed.')


main()
