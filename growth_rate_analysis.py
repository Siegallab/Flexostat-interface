import numpy
import matplotlib.pyplot as plt
import pandas
import sys
import matplotlib
import os
import argparse

parser = argparse.ArgumentParser(description='Growth Rate Analysis.')
#parser.add_argument("-d", "--experiment_date", default="",
#					help="Experiment date to analyze or empty ")

argv = False
argv_count = 1
if len(sys.argv) > 1:
	argv = True
if argv:
	file_prefix = sys.argv[1]
	argv_count += 1
else:
	file_prefix = 'test_data_'

def auto_man_input(argv, argv_count, prompt):
	if argv:
		parameter = str(sys.argv[argv_count])
		argv_count += 1
	else:
		parameter = raw_input(prompt)
	return parameter

def machine_to_human(location, data_set):
	df = pandas.read_csv('{}/{}{}.csv'.format(location, file_prefix, data_set), header=None,
						 names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	time_start = df.ix[0, 0]
	if time_start > 1:
		print('Data set is using machine time. Converting to human time...')
		command = 'mv {0}/{1}{2}.csv {0}/{1}{2}_machine.csv'.format(location, file_prefix, data_set)
		os.system(command)
		new_data = []

		for row in df.itertuples():
			new_row = []
			row_id = True
			for element in row:
				if row_id:
					row_id = False
				elif len(new_row) == 0:
					new_row.append((element - time_start)/3600)
				else:
					new_row.append(element)
			new_data.append(new_row)
		numpy.savetxt('{}/{}{}.csv'.format(location, file_prefix, data_set), new_data, delimiter = ",")
		print('Data set with human time created.')
	else:
		print('Data set is using human time.')

def growth_rate_csv(location, data_set):
	print('Growth rate csv generating...')

	df = pandas.read_csv('{}/{}{}.csv'.format(location, file_prefix, data_set), header = None,
						   names = ['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	new_data_r = []
	time_start = df.ix[0, 0]
	previous_time = df.ix[0, 0]
	time_difference = 0
	previous_od = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
	for row in df.itertuples():
		new_row = []
		row_id = True
		ch_count = 0
		for element in row:
			if row_id:
				row_id = False
				continue
			elif len(new_row) == 0:
				new_row.append(element-time_start)
				time_difference = element - previous_time
				previous_time = element
			elif element == 0 or new_row[0] == 0:
				new_row.append(float(0))
			else:
				if data_set == 'od':
					prev_od = previous_od[ch_count]
					current_od = element
					#print('\tcurr: {}, prev: {}'.format(element, previous_od[ch_count]))
					if prev_od <= 0:
						prev_od = 0.0001
					if current_od <= 0:
						current_od = 0.0001
					#print('\t\tcurr: {}, prev: {}, time diff: {}'.format(current_od, prev_od, time_difference))
					new_row.append(round((numpy.log(current_od / prev_od) / time_difference), 6))
				else:
					new_row.append(round((numpy.log(1 + (element / 15000)) / time_difference), 6))
			previous_od[ch_count] = element
			ch_count += 1
		#print(new_row)
		new_data_r.append(new_row)
	numpy.savetxt('{}/{}r{}.csv'.format(location, file_prefix, data_set), new_data_r, delimiter = ",")
	print('Growth rate csv generated and exported.')

def get_recent_exp(recent):
	exp_list = os.listdir('Data/')
	recent_split = recent.split('-')
	for exp in exp_list:
		if exp[0].isdigit():
			split = exp.split('-')
			last = split[2][0:2]
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

def generate_graphs(data_set, location, output, limits):
	print('Beginning analysis...')
	df = pandas.read_csv('{}/{}{}.csv'.format(location, file_prefix, data_set), header = None,
						 names = ['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	for chamber in range(1, 9):
		df.plot.scatter(x='Time', y='{}'.format(chamber))
		if limits[0] != limits[1]:
			plt.xlim(limits[0], limits[1])
		if limits[2] != limits[3]:
			plt.ylim(limits[2], limits[3])
		plt.savefig('{}/ch{}.png'.format(output, chamber))
		plt.close()
	print('Graphs have completed.')

def analysis_parameters(location, argv, argv_count):
	data_set = auto_man_input(argv, argv_count, '<od> for OD, <u> for dilutions, <z> for something,' +
							 '\n\t<ru> for growth rate based on u, <rod> for growth rate based on od' +
						 '\n\tEnter data set to analyze: ')

	if (data_set == 'ru' or data_set == 'rod') and \
					os.path.exists('{}/{}{}.csv'.format(location, file_prefix, data_set)) == False:
		growth_rate_csv(location, data_set)
	machine_to_human(location, data_set)

	limits = [0,0,0,0]
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
		limit_dir += '-x-{}-{}'.format(limits[0],limits[1])

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

	if os.path.exists('{}/{}{}'.format(location,data_set,limit_dir)) == False:
		os.system('mkdir {}/{}{}'.format(location,data_set,limit_dir))
		print('Analysis folder not found, made new folder.')
	else:
		print('Analysis folder found, will overwrite previous graphs.')
	output = '{}/{}{}'.format(location,data_set,limit_dir)
	generate_graphs(data_set, location, output, limits)


decision = auto_man_input(argv, argv_count, '<1> to generate growth rate csv with u\n\t' +
				'<2> to generate growth rate csv with od\n\tor <Enter> to start data set analysis: ')
experiment = auto_man_input(argv, argv_count, 'Enter experiment date to analyze \n\tor <Enter> to analyze latest one: ')

if experiment == '' or experiment == 'recent':
	experiment = get_recent_exp('00-00-00')
location = 'Data/{}'.format(experiment)

if decision == '1':
	machine_to_human(location, 'u')
	growth_rate_csv(location, 'u')
elif decision == '2':
	machine_to_human(location, 'od')
	growth_rate_csv(location, 'od')
else:
	analysis_parameters(location, argv, argv_count)
print('Program end.')
