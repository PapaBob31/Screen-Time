import subprocess, time, json, copy, sys
from datetime import datetime, timedelta

ONE_MINUTE = timedelta(minutes=1)

def get_target_processes():
	try:
		with open("target_processes.json") as file:
			try:
				user_target_processes = json.load(file)
			except json.decoder.JSONDecodeError:
				sys.exit()
	except FileNotFoundError:
		sys.exit()
	else:
		if not user_target_processes:
			# if user_target_processes is empty, no need to continue execution
			sys.exit()
	return user_target_processes

def check_for_multiple_instances():
	"""Checks if the process is already running on the computer"""

	all_processes = subprocess.run("tasklist /fi \"sessionname eq console\" /fo csv /nh", stdout=subprocess.PIPE, text=True)
	all_processes = all_processes.stdout.split('\n')
	# '"SynTPEnh.exe","6268","Console","54","15,832 K"' : This is how each item in all_processes list is formated

	process_name = ''
	for process_description in all_processes:
		for char in process_description:
			if char == ',':
				# The first comma we encounter means we already have the process complete name
				process_name = process_name.strip('"')
				if process_name == "cmd.exe":
					sys.exit()
			process_name += char
		process_name = ''

class Monitor:
	"""
	This class monitors all target processes that are currently running and stores how long they've been
	running in a json file. This json file is updated everyday as long as the program runs.
	"""
	current_date = str(datetime.now().date())
	target_processes = get_target_processes()

	processes_data = {}
	# example_data: {"chrome.exe": [False, "0:00"], "firefox.exe": [False, "0:00"], "sublime_text.exe": [False, "0:00"]}
	# For each entry in the dictionary, The first list item (the running flag) is used to indicate whether the process is running or not.
	# The second list item is how long it ran when it was running or how long it has been running if it's still running.

	screen_time_data = {}

	@staticmethod
	def create_entries_for_target_processes():
		processes_data = {}
		for process in Monitor.target_processes:
			processes_data[process] = [False, "0:00"]
		Monitor.screen_time_data[Monitor.current_date] = processes_data
		Monitor.processes_data = Monitor.screen_time_data[Monitor.current_date]

	@staticmethod
	def update_processes_data():
		new_dict = {}

		for process in Monitor.target_processes:
			process_data = Monitor.screen_time_data[Monitor.current_date].get(process)
			if not process_data:
				new_dict[process] = [False, "0:00"]
			else:
				new_dict[process] = process_data

		Monitor.screen_time_data[Monitor.current_date] = new_dict
		Monitor.processes_data = Monitor.screen_time_data[Monitor.current_date]
			
	@staticmethod
	def get_processes_data():
		"""Gets the screen time data for the target processes."""
		try:
			with open("screen_time_data.json") as file:
				try:
					Monitor.screen_time_data = json.load(file)
				except json.decoder.JSONDecodeError:
					Monitor.screen_time_data = {}
		except FileNotFoundError:
			Monitor.screen_time_data = {}

		if type(Monitor.screen_time_data) != dict:
			Monitor.screen_time_data = {}
			Monitor.create_entries_for_target_processes()
			return
		
		if Monitor.screen_time_data.get(Monitor.current_date):
			Monitor.update_processes_data()
		else:
			# If the current date (today) doesn't have an entry in the dictionary already.	
			# one is created for it
			Monitor.create_entries_for_target_processes()
		

	@staticmethod
	def reset_running_flags():
		"""
		Resets the running flag of each process in the processes_data dictionary to False. Because the program 
		doesn't have a way of detecting if it's about to be closed, whenever the program starts, this method must  
		be called to reset any process's running flag that's still True from the last time the program ran.
		"""
		for process in Monitor.processes_data:
			if Monitor.processes_data[process][0]:
				Monitor.processes_data[process][0] = False

	@staticmethod
	def save_screen_time_data():
		with open("screen_time_data.json", "w") as screen_data_file:
			json.dump(Monitor.screen_time_data, screen_data_file)

	@staticmethod
	def create_timedelta(string):
		"""
		Splits the string parameter (that's in time format) into it's different components (hours, minutes, seconds).
		It then uses the hours and minutes parts to create a timedelta object and return it.
		"""
		string = string.split(":")
		return timedelta(hours=int(string[0]), minutes=int(string[1]))

	@staticmethod
	def scan_processes():
		"""Scans the processes on the computer to check if a target process is among them """

		all_processes = subprocess.run("tasklist /fi \"sessionname eq console\" /fo csv /nh", stdout=subprocess.PIPE, text=True)
		all_processes = all_processes.stdout.split('\n')
		# '"SynTPEnh.exe","6268","Console","54","15,832 K"' : This is how each item in all_processes list is formated
		
		process_name = ''
		for process_description in all_processes:
			for char in process_description:
				if char == ',':
					# The first comma we encounter means we already have the process complete name
					process_name = process_name.strip('"')
					Monitor.validate_and_update_process_data(process_name)
					break
				process_name += char
			process_name = ''

			# if all target processes has been found
			if len(Monitor.target_processes) == 0:
				break

	@staticmethod
	def validate_and_update_process_data(process_name):
		"""Checks if process_name parameter is in target processes and then updates the process data if it is."""

		for i in range(len(Monitor.target_processes)):
			if Monitor.target_processes[i] == process_name:
				if Monitor.processes_data[process_name][0]: # if the process is running
					Monitor.processes_data[process_name][1] = str(Monitor.create_timedelta(Monitor.processes_data[process_name][1]) + ONE_MINUTE)[:4]
				else:
					# We don't add ONE_MINUTE to the time here bcos the process was just discovered
					# We must wait for one minute in the while loop's time.sleep function
					# before we add ONE_MINUTE to the process's time
					Monitor.processes_data[process_name][0] = True

				# Removes any process found in target processes incase of multiple instances of a process
				# This action is also a means of prepping data for the update_closed_processes_data function
				del Monitor.target_processes[i]
				return

	@staticmethod
	def update_closed_processes_data():
		"""
		Sets a process's running flag to False if that process is currently not running but has a running flag set to True. 
		By the time this method is called, every process left in Monitor.target_processes is not running.
		"""
		for process in Monitor.target_processes:
			if Monitor.processes_data[process][0]:
				Monitor.processes_data[process][0] = False

	@staticmethod
	def check_and_update_current_date():
		"""Updates the screen_time_data if a new day starts while the program is running."""
		if datetime.now().strftime("%H:%M") == "0:00":
			Monitor.reset_data_for_new_day()
			Monitor.save_screen_time_data()

	@staticmethod
	def reset_data_for_new_day():
		"""
		Resets the Monitor.screen_time_data dictionary by creating a new date entry in the dictionary 
		and resetting all process's time
		"""
		for process in Monitor.processes_data:
			Monitor.processes_data[process][0] = False
			Monitor.processes_data[process][1] = "0:00"

		Monitor.current_date = str(datetime.now().date())
		Monitor.screen_time_data[Monitor.current_date] = {}

if __name__ == "__main__":
	# check_for_multiple_instances()
	Monitor.get_processes_data()
	Monitor.reset_running_flags()

	while True:
		Monitor.target_processes = get_target_processes() # Monitor.target_processes needs to be updated regularly
		Monitor.update_processes_data()
		Monitor.scan_processes()
		Monitor.update_closed_processes_data()
		Monitor.save_screen_time_data()
		Monitor.check_and_update_current_date()
		time.sleep(50)
