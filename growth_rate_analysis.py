import numpy
import matplotlib.pyplot as plt
import pandas
import sys
import matplotlib
import os
import argparse
import warnings

# Allows warnings from divide by zero or log/ln negative number to be caught in try except
warnings.filterwarnings('error')

# TODO Add command line argument parser if easier than current method
# parser = argparse.ArgumentParser(description='Growth Rate Analysis.')
# parser.add_argument("-d", "--experiment", default="",
# 				help="Experiment date to analyze or empty ")

def main():
	"""
	Determines if program will be run automatically with command line inputs or manually with user prompts.
	Determines what functions in program to run based on inputs.
	"""

	argv = False
	argv_count = 1
	file_prefix = 'test_data_'
	if len(sys.argv) > 1:
		argv = True
		file_prefix = sys.argv[1]
		argv_count += 1

	decision = auto_man_input(argv, argv_count, '<1> to generate growth rate csv with u\n\t' +
	                            '<2> to generate growth rate csv with od\n\t' +
	                            '<3> to designate growth rate analysis\n\t' +
	                            'or <Enter> to designate graph creation: ')
	experiment = auto_man_input(argv, argv_count,
								'Enter experiment date to analyze \n\tor <Enter> to analyze latest one: ')

	if experiment == '' or experiment == 'recent':
		experiment = get_recent_exp()
	location = 'Data/{}'.format(experiment)

	if decision == '1':
		machine_to_human(location, 'u', file_prefix)
		r_u_csv(location, 'u', file_prefix)
	elif decision == '2':
		machine_to_human(location, 'od', file_prefix)
		r_od_csv(location, 'od', file_prefix)
	elif decision == '3':
		data_set = get_data_set(location, argv, argv_count, file_prefix)
		# limits, limit_dir = get_axis_parameters(argv, argv_count)
		growth_rate_statistics(location, data_set, file_prefix)
	else:
		data_set = get_data_set(location, argv, argv_count, file_prefix)
		limits, limit_dir = get_axis_parameters(argv, argv_count)
		output = get_output_directory(location, data_set, limit_dir)
		generate_graphs(data_set, location, output, limits, file_prefix)
	print('Program end.')


def auto_man_input(argv, argv_count, prompt):
	"""
	Sets variable using either command line argument or user input following printed prompt

	:param argv: run automatically with command line argument or manually with user prompt
	:param argv_count: keeps track of the current command line argument to use
	:param prompt: user prompt to print
	:return: set variable
	"""
	if argv:
		parameter = str(sys.argv[argv_count])
		argv_count += 1
	else:
		parameter = raw_input(prompt)
	return parameter


def get_recent_exp():
	"""
	Finds the most recent experiment directory.

	:return: Most recent experiment directory
	"""
	exp_list = os.listdir('Data/')
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


def get_output_directory(location, data_set, limit_dir):
	"""
	Finds or creates directory for outputting graphs.

	:param location: path to experiment
	:param data_set: output data set
	:param limit_dir: x and y limits in string
	:return: directory for outputting graphs
	"""
	if not os.path.exists('{}/{}{}'.format(location, data_set, limit_dir)):
		os.system('mkdir {}/{}{}'.format(location, data_set, limit_dir))
		print('Analysis folder not found, made new folder.')
	else:
		print('Analysis folder found, will overwrite previous graphs.')
	output = '{}/{}{}'.format(location, data_set, limit_dir)
	return output


def machine_to_human(location, data_set, file_prefix):
	"""
	Converts machine time (seconds with starting time long ago) to hours from experiment start.
	Generates new csv and renames the old csv.

	:param location: path to experiment
	:param data_set: csv data to convert
	:param file_prefix: any prefix before the data set in the file name
	"""
	df = pandas.read_csv('{}/{}{}.csv'.format(location, file_prefix, data_set), header=None,
							names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	time_start = df.iloc[0, 0]
	# Checks if the first time point is in machine time
	if time_start > 1:
		print('Data set is using machine time. Converting to human time...')
		# Renames the csv using machine time
		command = 'mv {0}/{1}{2}.csv {0}/{1}{2}_machine.csv'.format(location, file_prefix, data_set)
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
		numpy.savetxt('{}/{}{}.csv'.format(location, file_prefix, data_set), new_data, delimiter=",")
		print('Data set with human time created.')
	else:
		print('Data set is using human time.')


def r_u_csv(location, data_set, file_prefix):
	"""
	Calculates growth rate data based on dilutions (u) and saves to csv.

	:param location: path to experiment
	:param data_set: csv data to calculate growth rate from
	:param file_prefix: any prefix before the data set in the file name
	"""
	print('Growth rate csv generating...')

	df = pandas.read_csv('{}/{}{}.csv'.format(location, file_prefix, data_set), header=None,
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

	numpy.savetxt('{}/{}r{}.csv'.format(location, file_prefix, data_set), new_data_r, delimiter=",")
	print('Growth rate csv generated and exported.')


def r_od_csv(location, data_set, file_prefix):
	"""
	Calculates growth rate data based on optical density (od) and saves to csv.

	:param location: path to experiment
	:param data_set: csv data to calculate growth rate from
	:param file_prefix: any prefix before the data set in the file name
	"""
	print('Growth rate csv generating...')

	df = pandas.read_csv('{}/{}{}.csv'.format(location, file_prefix, data_set), header=None,
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
			else:
				# Negative OD's are ignored with growth rate being a blank space
				if element <= 0 or previous_od[ch_count] <= 0:
					new_row.append(None)
				else:
					try:
						new_row.append(round((numpy.log(element / previous_od[ch_count]) / time_difference), 6))
					# If the growth rate calculation fails (it will for values <= 0) then append a blank space
					except (Warning, Exception):
						new_row.append(None)
				# Each element is saved for comparison with the next element of that chamber
				previous_od[ch_count] = element
			ch_count += 1
		new_data_r.append(new_row)

	df = pandas.DataFrame(new_data_r)
	df.to_csv(path_or_buf='{}/{}r{}.csv'.format(location, file_prefix, data_set), index=False)
	print('Growth rate csv generated and exported.')


def get_data_set(location, argv, argv_count, file_prefix):
	"""
	Sets data set, ensures data set csv exists, and that it is in hours (as opposed to machine time).
	If data set does not exist (can happen in growth rate) or is in machine time, then calculate appropriately.

	:param location: path to experiment
	:param argv: run automatically with command line argument or manually with user prompt
	:param argv_count: keeps track of the current command line argument to use
	:param file_prefix: any prefix before the data set in the file name
	:return: data set variable
	"""
	data_set = auto_man_input(argv, argv_count, '<od> for OD, <u> for dilutions, <z> for something,' +
	                          '\n\t<ru> for growth rate based on u, <rod> for growth rate based on od' +
	                          '\n\tEnter data set to analyze: ')

	if data_set == 'ru' and not os.path.exists('{}/{}{}.csv'.format(location, file_prefix, data_set)):
		r_u_csv(location, data_set, file_prefix)
	elif data_set == 'rod' and not os.path.exists('{}/{}{}.csv'.format(location, file_prefix, data_set)):
		r_od_csv(location, data_set, file_prefix)
	machine_to_human(location, data_set, file_prefix)
	return data_set


def get_axis_parameters(argv, argv_count):
	"""
	Determines x and y limits by command line arguments or from user input following prompts.
	Creates an array for those limits and a string for directory creation.

	:param argv: run automatically with command line argument or manually with user prompt
	:param argv_count: keeps track of the current command line argument to use
	:return: array of x and y limits and those limits put into a string for making a directory
	"""
	limits = [0, 0, 0, 0]
	limit_dir = ''
	decision = auto_man_input(argv, argv_count, 'Define x limits? <x> yes or <Enter> no: ')
	if decision == 'x':
		if argv:
			limits[0] = sys.argv[argv_count]
			limits[1] = sys.argv[argv_count]
			argv_count += 2
		else:
			limits[0] = float(raw_input('\tEnter x lower limit: '))
			limits[1] = float(raw_input('\tEnter x upper limit: '))
		limit_dir += '-x-{}-{}'.format(limits[0], limits[1])

	decision = auto_man_input(argv, argv_count, 'Define y limits? <y> yes or <Enter> no: ')
	if decision == 'y':
		if argv:
			limits[2] = sys.argv[argv_count]
			limits[3] = sys.argv[argv_count]
			argv_count += 2
		else:
			limits[2] = float(raw_input('\tEnter y lower limit: '))
			limits[3] = float(raw_input('\tEnter y upper limit: '))
		limit_dir += '-y-{}-{}'.format(limits[2], limits[3])
	return limits, limit_dir


def growth_rate_statistics(location, data_set, file_prefix):
	"""
	Analyzes growth rate csv for statistics (averages, standard deviation, and standard error).

	:param location: path to experiment
	:param data_set: growth rate csv data to analyze from
	:param file_prefix: any prefix before the data set in the file name
	"""
	print('Starting growth rate statistics...')
	output = get_output_directory(location, data_set, '')
	df = pandas.read_csv('{}/{}{}.csv'.format(location, file_prefix, data_set), header=None,
	                     names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	for chamber in range(1, 9):
		stats = pandas.DataFrame(columns=['Time','Average','SD','SE'])
		hour = [0,1]
		while (hour[1] < df.iloc[-1,0]):
			ave = df['{}'.format(chamber)].loc[hour[0]:hour[1]].mean()
			sd = df['{}'.format(chamber)].loc[hour[0]:hour[1]].std()
			se = df['{}'.format(chamber)].loc[hour[0]:hour[1]].sem()
			temp = pandas.DataFrame([[hour[1],ave,sd,se]], columns=['Time','Average','SD','SE'])
			print(temp)
			stats = stats.append(temp)
			hour[0] = hour[1]
			hour[1] = hour[1]+1
		stats.to_csv(path_or_buf='{}/{}{}_stats_{}.csv'.format(output, file_prefix, data_set, chamber), index=False)
	generate_graphs('{}_stats'.format(data_set), output, output, '00-00-00', file_prefix)

	# TODO Iterate through growth rate chamber rows, calculate average, SD, and SE across each hour
	# TODO Add ability to define region where statistics will be calculated
	# TODO Write statistics to a file


def generate_graphs(data_set, location, output, limits, file_prefix):
	"""
	Creates a scatter plot for each chamber based on defined x and y limits and a data set csv.

	:param data_set: csv data to graph
	:param location: path to experiment
	:param output: path to directory for graph export
	:param limits: x and y limits to use for graphs
	:param file_prefix: any prefix before the data set in the file name
	"""
	print('Beginning analysis...')
	df = pandas.read_csv('{}/{}{}.csv'.format(location, file_prefix, data_set), header=None,
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
	print('Graphs have completed.')


def generate_dual_graphs(data_set_1, data_set_2, location, output, limits, file_prefix):
	"""
	Creates a scatter plot with two defined overlapping data sets with defined x and y limits (y can be different).

	:param data_set_1: first csv data set to graph
	:param data_set_2: second csv data set to graph
	:param location: path to experiment
	:param output: path to directory for graph export
	:param limits: x and y limits to use for graphs
	:param file_prefix: any prefix before the data set in the file name
	"""
	print('Beginning analysis...')
	df1 = pandas.read_csv('{}/{}{}.csv'.format(location, file_prefix, data_set_1), header=None,
							names=['Time', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8'])
	df2 = pandas.read_csv('{}/{}{}.csv'.format(location, file_prefix, data_set_2), header=None,
							usecols=[1, 2, 3, 4, 5, 6, 7, 8],
							names=['2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8'])
	df = pandas.concat([df1, df2], axis=1)
	for chamber in range(1, 9):
		df.plot.scatter(x='Time', y='1.{}'.format(chamber))
		df.plot(secondary_y=['2.{}'.format(chamber)])
		if limits[0] != limits[1]:
			plt.xlim(limits[0], limits[1])
		if limits[2] != limits[3]:
			plt.ylim(limits[2], limits[3])
		plt.savefig('{}/ch{}.png'.format(output, chamber))
		plt.close()
	print('Graphs have completed.')
	# TODO Finish building function for overlapping two data sets with separate y limits

main()
