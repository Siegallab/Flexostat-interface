
"""
BACKGROUND

	Created April 12, 2018
		by David Klein
		contributions found at https://github.com/Siegallab/Flexostat-interface

INSTRUCTIONS

	Run using Python 3 on the command line as such
	$ python3 Growth-Pipe.py -h
"""

import numpy
import pandas
from datetime import datetime
import os
import argparse
from configparser import ConfigParser

def main():
	"""
	Defines the command line arguments intaken by the program.
	Ensures there is a config file to work with before calling the 'functions' function.
	"""
	args = command_line_parameters()
	start_time = datetime.now()
	last_time = datetime.now()
	while (last_time - start_time).seconds/60 < float(args.exp_len):
		now_time = datetime.now()
		diff = (now_time - last_time).seconds/60
		if diff >= float(args.data_time):
			produce_data(args)
		if diff >= float(args.block_time):
			analyze_block(args)
		last_time = now_time
	print('Program end.\n')


def command_line_parameters():
	"""
	Takes in command line argument parameters and displays help descriptions.

	:return: variable containing all command line argument parameters
	"""
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
					description="""
			Experiment Simulator Program
			----------------------------
			Defaults: 0.4 true growth, 20 SD for OD noise, 
				1 minute data production, 2 minute block analysis, 2 hour experiment length,
				'config.ini' for config file
			
			Optional parameters: 
						""")

	parser.add_argument('--growth', default='0.4', help='true growth rate, defaults to 0.4')
	parser.add_argument('--noise', default='20', help='standard deviation of OD noise, defaults to 20')
	parser.add_argument('--data_time', default='1', help='minute interval for each data production, defaults to 1')
	parser.add_argument('--block_time', default='2', help='minute interval for each block analysis, defaults to 2')
	parser.add_argument('--exp_len', default='120', help='minute length for entire simulated experiment, defaults to 120')
	parser.add_argument('--config', default='config.ini', help='experiment config file, defaults to config.ini')

	args = parser.parse_args()
	return args


def produce_data(args):
	"""
	Generate OD and U data as if from a normal experiment run

	:param args: command line arguments for program
	"""
	config = ConfigParser()
	config.read(args.config)
	controller = dict(config.items('controller'))
	log = dict(config.items('log'))

	true_GR = .4/60
	start_OD = 1
	timepoints = numpy.arange(1000)

	true_OD = start_OD * numpy.exp(true_GR*timepoints)
	OD_noise = numpy.random.normal(0, 20, (len(timepoints),))
	observed_OD = true_OD+OD_noise


def analyze_block(args):
	"""
	Run the Block-Dilutions.py program with specific inputs

	:param args: command line arguments for program
	"""
	os.system("python3 Block-Dilutions.py")


main()