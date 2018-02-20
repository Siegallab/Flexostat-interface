# Temporary Brainstorming
1. Is an average being taken of ODs for reporting?

	a. What does tx_val and rx_val do?

	b. Are the data points for the average being stored locally?

	c. Are the data points being averaged from the odlog?

2. Do we want to keep the data of these ODs if they're not logged?

	a. If so, do we mark dilutions as 0 and only dilute every 60 while logging ODs every 3?

	b. If so, should we just parse the odlog instead of the log?

	c. If no, is what it's doing fine (averaging or not)?

3. Is it possible to make another program to implement the large dilutions only?

	a. Can the machine take two sources of input at once?

	b. Do we pause the servostat and stop the controller until large dilutions are done?

4. Is it better to implement large dilutions inside the current config by changing setpoint? (safer)

	a. Can the computeControl take in different set points?

	b. Can the controller dynamically update set points based on time?

	c. Do we set a time limit until reverse to upper limit or switch each chamber independently when they reach lower limit?
	