import numpy
import matplotlib.pyplot as plt
import pandas
import sys
import matplotlib


print "Python version: " + sys.version
location = '~/Documents/Shmoo_Lab/Flexostat-interface/test_data_od.csv'
df = pandas.read_csv(location, header=None, names = ["Time", "1", "2", "3", "4", "5", "6", "7", "8"])

#df.plot()
#plt.scatter(x = df.0, y = df.1, s = 10, c = 'green')
#plt.savefig('myfile.png')
df.plot.scatter(x='Time', y='1')
df.plot.scatter(x='Time', y='2', color='r')
df.plot.scatter(x='Time', y='3', color='g')
df.plot.scatter(x='Time', y='4', color='b')
df.plot.scatter(x='Time', y='5')
df.plot.scatter(x='Time', y='6')
df.plot.scatter(x='Time', y='7')
df.plot.scatter(x='Time', y='8')

plt.savefig('myfile.png')