
"""
BACKGROUND

	Created April 17, 2018
		by David Klein
		contributions found at https://github.com/Siegallab/Flexostat-interface

INSTRUCTIONS

	Takes in a special full log file in json format of experiment data that is only from periods of dilution
		In this example, we would only use chambers 0, 1, 3, 6, and 7 because they produce dilutions
			{"timestamp": 1508560967, "ods": [0.5044, 0.5004, 0.3671, 0.5025, 0.0644, 0.1677, 1.0012, 1.0023],
			"u": [13, 42, 0, 47, 0, 0, 85, 50],
			"z": ["0.4915", "41.1331", "0.0000", "40.2680", "0.0000", "0.0000", "81.7548", "43.1188"]}
	Calculates the optical density subtraction impact of the dilution based on a 0.4 growth per hour estimation
	Fits linearly and gives the coefficients for use in simulations
"""

import csv
import json
import numpy
import pandas

hour_GR = .4 ### <-- 0.4 growth per hour is estimated, change if desired
chambers = [0, 6] ### <-- Fill in this list only with chambers that are experiencing dilution in the data
input_file = 'impact.txt' ### <-- Specify the file of selected full log data you are reading in
output_file1 = 'impact.csv' ### <-- Your output file name
output_file2 = 'good_impact.csv' ### <-- Your output file name of only dilutions that caused lower optical density

file = open(input_file, 'r')
content = file.readlines()
file.close()

data = []
for chamber in chambers:
	first = True
	for line in content:
		line_data = json.loads(line)
		od = line_data['ods'][chamber]
		u = line_data['u'][chamber]
		impact = 0
		if first:
			first = False
		else:
			true_GR = hour_GR / 60
			true_OD = data[-1][0] * numpy.exp(true_GR)
			impact = true_OD - od
			data[-1][2] = impact
		data.append([od, u, impact])
output1 = [['OD', 'Dilution', 'Impact']] + data
dataf = open(output_file1, 'w')
writer = csv.writer(dataf)
writer.writerows(output1)
dataf.close()

pos_data = []
first = True
for row in data:
	if first:
		first = False
		continue
	if float(row[2]) >= 0:
		pos_data.append(row)
output2 = [['OD', 'Dilution', 'Impact']] + pos_data
dataf = open(output_file2, 'w')
writer = csv.writer(dataf)
writer.writerows(output2)
dataf.close()

df = pandas.DataFrame(pos_data, columns=['OD', 'Dilution', 'Impact'])
x = numpy.asarray(df['Dilution'].tolist())
y = numpy.asarray(df['Impact'].tolist())
coefficients = numpy.polyfit(x, y, 1)
print("Linear fit: y (subtract from OD) = [ {} * x (dilution) ] + {}".format(coefficients[0], coefficients[1]))