
"""
BACKGROUND

	Created March 13, 2018
		by David Klein, using previous code from Maxwell Raderstorf
		contributions found at https://github.com/Siegallab/Flexostat-interface
	An open source feature contribution to the Klavins Lab Flexostat project
		project found at https://github.com/Flexostat/Flexostat-interface

INSTRUCTIONS

	Run using Python 3 on the command line as such
	$ python3 Media-Reporter.py -h
"""

import csv
from datetime import datetime
from numpy import array


def main():
	"""
	Defines the command line arguments intaken by the program.
	Ensures there is a config file to work with before continuing.
	"""

	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
					description="""
			Media Reporter Program
			-----------------------------
			Select at least one communication method: --print (-p), --text (-t), --email (-e)
			Select at least one reporting function: --report (-r), --percent (-p), --limit (-m), --amount (-a)
			Optional parameters: --config (-c), --log (l), --start (-s), 
						""")

	parser.add_argument('-p', '--print', action='store_true', 'print out media report to command line')
	parser.add_argument('-t', '--text', default='0', 'send SMS text message media report to specified number (must set Twilio parameters inside code)')
	parser.add_argument('-e', '--email', action='store_true', 'email media report (must set parameters inside code)')
	parser.add_argument('-c', '--config', default='config.ini', help="change config file from default 'config.ini'")
	parser.add_argument('-l', '--log', default='media.log', help="change exported media log file from 'media.log'")
	parser.add_argument('-s', '--start', default='0', help='start program with new starting media amount in ml amount if no log file exists')
	parser.add_argument('-r', '--report', action='store_true', help='program will report media whenever it run (specify time interval with crontab)')
	parser.add_argument('-p', '--percent', default='0', help="specify percent limit when report wanted (e.g. '10' reports when 10% of starting media is left)")
	parser.add_argument('-m', '--limit', default='0', help="specify ml limit when report wanted (e.g. '100' reports when 100 mls has been reached)")
	parser.add_argument('-a', '--amount', default='0', help="specify ml amount interval when report wanted (e.g. '100' reports every time 100 mls are consumed)")

	args = parser.parse_args()

	if os.path.exists(args.config) and (args.report or float(args.percent) > 0 or float(args.limit) > 0 or float(args.amount) > 0):
		config = ConfigParser()
		config.read(args.config)
		config_log = dict(config.items('log'))

		if (args.report or float(args.percent) > 0 or float(args.limit) > 0 or float(args.amount) > 0) and (args.print or len(args.email) > 1 or len(args.text) > 1):
			if os.path.exists(args.log):
				# each media log entry occurs when there is a report and is formatted as such: 
				#	[time and date, machine time, media starting amount in ml, ml of last report, ml of last --amount report, report message]
				media_log = open(args.log, 'r')
				reader = csv.reader(media_log)
				last_report = list(reader)[-1]
				media_log.close()
			else:
				print('No media log file exists. Will create new one with starting amount specified from --start parameter.')
				dilutions = parse_u(config_log, 0)
				media_log = open(args.log, 'a')
				writer = csv.writer(media_log)
				date_time = datetime.now().strftime("%Y-%m-%d %H:%M")
				report = [date_time, dilutions[0][0], float(args.start), float(args.start), float(args.start), 'Starting media reporting at {} with {}ml of media.'.format(date_time, args.start), args.start]
				writer.writerow(report)
				media_log.close()
			try:
				last_report
			except NameError:
				print('First report made.')
			else:
				dilutions = parse_u(config_log, last_report[1])
				decision, report_str, report = report_build(args, dilutions, last_report)
				if decision:
					media_log = open(args.log, 'a')
					writer = csv.writer(media_log)
					writer.writerow(report)
					media_log.close()
					if args.print:
						print(report_str)
					if len(args.text) > 1:
						text_report(args.text, report_str)
					if len(args.email) > 1:
						email_report(args.text, report_str)
		else:
			print('ERROR: Communication or reporting method not specified.')
	else:
		print('ERROR: Config file not found.')
	print('Program end.\n')


def parse_u(config_log, start_time):
	"""
	Parses dilution values from the log file.

	:param rdata: full log file from config file
	:param start_time: machine time of last media log report
	:return: array of all dilution values
	"""
	fulllog_file = open(config_log['fulllog'], 'r')
	fulllog = fulllog_file.readlines()
	fulllog_file.close()

	data = []
	for line in fulllog:
		d1 = line.split(":")
		d2 = [int(d1[1][:-7])]
		if d2[0] > start_time:
			us = d1[3][2:-6].split(",")
			for u in us:
				d2.append(float(u))
			data.append(d2)
	return data


def report_build(args, udata, last_report):
	"""
	Builds the media report and message from the dilution values and past report.

	:param args: command line argument parameters for more customized reports
	:param udata: matrix of dilution values since last report
	:param last_report: last media report data
	return: media report information as string and list
	"""
	decision = False
	date_time = datetime.now().strftime("%Y-%m-%d %H:%M")
	total_dilutions = 0
	amount_interval = float(last_report[4])
	udata = array(udata)
	for row in udata:
		total_dilutions += row[1:].sum()
	current_amount = float(last_report[3]) - total_dilutions
	local_percent = (total_dilutions // float(last_report[3]))*100
	total_percent = (current_amount // float(last_report[2]))*100
	report_str = "Current media level is at " + current_amount + "ml.\n" +
		"The experiment has consumed " + total_dilutions + "ml or " + local_percent + "% since the last report.\n" +
		"Total media level is at " + total_percent + "% of the starting amount of " + last_report[2] + "ml."
	if args.report:
		decision = True
	if float(args.amount) > 0:
		if (amount_interval - current_amount) >= float(args.amount):
			amount_interval = current_amount
			report_str += "\nThe amount interval of " + args.amount + "ml has been reached."
			decision = True
	if float(args.limit) > 0:
		if current_amount <= float(args.limit):
			report_str += "\nThe media limit of " + args.limit + "ml has been reached."
			decision = True
	if float(args.percent) > 0:
		if total_percent <= float(args.args.percent):
			report_str += "\nThe percent limit of " + args.percent + "% has been reached."
			decision = True
	report = [date_time, udata[-1][0], last_report[2], current_amount, amount_interval, report_str]
	return decision, report_str, report


def text_report(number, message):
	"""
	Sends a text message of media report using Twilio API.

	:param number: cell phone number of target recipient
	:param message: the media report in string form
	"""
	from twilio.rest import Client
	accountSID = 'yourAccountSID'
	authToken = 'yourAuthToken'
	twilioCli = Client(accountSID, authToken)
	myTwilioNumber = '+14955551234'
	msg = twilioCli.messages.create(body=message, from_=myTwilioNumber, to=number)


def email_report(address, message):
	"""
	Emails the media report message using SMTP with defined variables.

	:param address: email address for recipient
	:param message: the media report in string form
	"""
	import imaplib
	import time
	import smtplib
	import email
	import email.mime.multipart
	import email.mime.text

	# The variables below are for you to define to your preferences.
	account = 'yourEmail@gmail.com'
	password = 'yourPassword'
	subject = 'Turbidostat Media Report'
		# Gmail users will have to allow access to less secure apps from this link.
		#    https://myaccount.google.com/lesssecureapps
		# Gmail users with 2-Step Verification will have to generate a one-time App password.
		#    Simple follow the link above and click the lower 'Learn More' link.

	try:
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(account, password)

		msg = email.mime.multipart.MIMEMultipart()
		msg['From'] = account
		msg['To'] = address
		msg['Subject'] = subject
		body = message
		msg.attach(email.mime.text.MIMEText(body, 'plain'))

		text = msg.as_string()
		server.sendmail(account, address, text)
		server.quit()

	except Exception as e:
		print('send_mail error: ' + str(e))