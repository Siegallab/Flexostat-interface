import numpy
import matplotlib.pyplot as plt
import pandas
import sys
import matplotlib

location = '~/Documents/Shmoo_Lab/Flexostat-interface/test_data_'
od_df = pandas.read_csv('{}od.csv'.format(location), header = None, names = ["Time", "1", "2", "3", "4", "5", "6", "7", "8"])
u_df = pandas.read_csv('{}u.csv'.format(location), header = None, names = ["Time", "1", "2", "3", "4", "5", "6", "7", "8"])
z_df = pandas.read_csv('{}z.csv'.format(location), header = None, names = ["Time", "1", "2", "3", "4", "5", "6", "7", "8"])

for chamber in range(1,9):
	od_df.plot.scatter(x='Time', y='{}'.format(chamber))
	plt.savefig('ch{}_scatter.png'.format(chamber))

test_data_r = []
start = u_df.ix[0,0]

for row in u_df.itertuples():
	new_row = []
	for element in row:
		if len(new_row) == 0:
			new_row.append(element-start)
			continue
		if element == 0 or new_row[0] == 0:
			new_row.append(0)
		else:
			new_row.append(round((numpy.log(element)/new_row[0]),6))
	test_data_r.append(new_row)

numpy.savetxt("test_data_r.csv", test_data_r, delimiter=",")

r_df = pandas.read_csv('{}r.csv'.format(location), header = None, names = ["Time", "1", "2", "3", "4", "5", "6", "7", "8"])

for chamber in range(1,9):
	r_df.plot.scatter(x='Time', y='{}'.format(chamber))
	plt.savefig('ch{}_growth_rate.png'.format(chamber))
