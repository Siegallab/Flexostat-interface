import numpy
import matplotlib.pyplot as plt
import pandas
import sys
import matplotlib
import os

def make_growth_rate_csv():
	test_data_r = []
	time_start = u_df.ix[0, 0]

	for row in u_df.itertuples():
		new_row = []
		row_id = True
		for element in row:
			if row_id:
				row_id = False
			elif len(new_row) == 0:
				new_row.append(element - time_start)
			elif element == 0 or new_row[0] == 0:
				new_row.append(0)
			else:
				new_row.append(round((numpy.log(element) / new_row[0]), 6))
		test_data_r.append(new_row)
	numpy.savetxt('Data/10-20-17/test_data_r.csv', test_data_r, delimiter=",")

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

def graphs(data_set, location, output, limits):
	print('Beginning analysis...')
	df = pandas.read_csv('{}/test_data_{}.csv'.format(location, data_set), header=None, names=['Time', '1', '2', '3', '4', '5', '6', '7', '8'])
	for chamber in range(1, 9):
		if limits[0] != limits[1]:
			df.iloc[limits[0]:limits[1]].plot.scatter(x='Time', y='{}'.format(chamber))
		else:
			df.plot.scatter(x='Time', y='{}'.format(chamber))
		#if limits[0] != limits[1]:
		#	plt.xlim(limits[0], limits[1])
		if limits[2] != limits[3]:
			plt.ylim(limits[2], limits[3])
		plt.savefig('{}/ch{}.png'.format(output, chamber))
		plt.close()
	print('Graphs have completed.')

experiment = raw_input('Enter experiment date to analyze \n\tor <Enter> to analyze latest one: ')

if experiment == '':
	experiment = get_recent_exp('00-00-00')

location = 'Data/{}'.format(experiment)

data_set = raw_input('<od> for OD, <u> for dilutions, <z> for something, <r> for growth rate\n' +
					 '\tEnter data set to analyze: ')

if data_set == 'r' and os.path.exists('test_data_r.csv') == False:
	make_growth_rate_csv()

limits = [0,0,0,0]
limit_dir = ''
decision_01 = raw_input('Define x limits? <1> yes or <Enter> no: ')
if decision_01 != '':
	limits[0] = int(raw_input('\tEnter x lower limit: '))
	limits[1] = int(raw_input('\tEnter x upper limit: '))
	limit_dir += '-x-{}-{}'.format(limits[0],limits[1])
decision_01 = raw_input('Define y limits? <1> yes or <Enter> no: ')
if decision_01 != '':
	limits[2] = int(raw_input('\tEnter y lower limit: '))
	limits[3] = int(raw_input('\tEnter y upper limit: '))
	limit_dir += '-y-{}-{}'.format(limits[2], limits[3])

if os.path.exists('{}/{}{}'.format(location,data_set,limit_dir)) == False:
	os.system('mkdir {}/{}{}'.format(location,data_set,limit_dir))
	print('Analysis folder not found, made new folder.')
else:
	print('Analysis folder found, will overwrite previous graphs.')

output = '{}/{}{}'.format(location,data_set,limit_dir)
graphs(data_set, location, output, limits)

print('Ending program now...')
