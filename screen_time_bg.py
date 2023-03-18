import subprocess, time, json, copy, sys
from datetime import datetime, timedelta

ONE_MINUTE = timedelta(minutes=1)

def remove_duplicates(list_item):
	"""Removes duplicate items from a list and returns a new list"""
	unique_list = []
	unique_list.append(list_item[0])
	list_item.sort()
	for i in range(1, len(list_item)):
		if list_item[i] != list_item[i-1]:
			unique_list.append(list_item[i])
	return unique_list

def handle_file_io(file_name):
	try:
		with open(file_name) as file:
			try:
				data = json.load(file)
			except json.decoder.JSONDecodeError:
				return None
	except FileNotFoundError:
		return None
	return data

def get_target_processes():
	"""Gets the list of processes that are being monitored by the program from a json file"""
	user_target_processes = handle_file_io("target_processes.json")

	if type(user_target_processes) == list:
		if not user_target_processes:
			# if user_target_processes is empty, no need to continue execution
			sys.exit()
	else: # user_target_processes is not a list type
		sys.exit()
	return remove_duplicates(user_target_processes)

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
					sys.exit() # Two instances of the program can't be allowed to run at the same time
			process_name += char
		process_name = ''

class Monitor:
	"""
	This class monitors all target processes that are currently running and stores how long they've been
	running in a json file. This json file is updated every one minute as long as the program runs.
	"""
	current_date = str(datetime.now().date())
	target_processes = get_target_processes() # List that stores the name of the process the program is monitoring

	processes_data = {} # Stores data about each process in target_processes list e.g {"chrome.exe": [False, "0:00"], "firefox.exe": [False, "0:00"]}
	# First item in each list stores if the process is running or not and the second item stores how long it has run since the program started monitoring it.

	screen_time_data = {} # Stores a date and processes_data variable content as a key-value pair as shown below
	# {"2022-10-21": {"chrome.exe": [false, "0:00"], "firefox.exe": [false, "0:30"]}}

	@staticmethod
	def create_entries_for_target_processes():
		"""Adds data of the processes being monitored for the current date in Monitor.screen_time_data"""
		processes_data = {}
		for process in Monitor.target_processes:
			processes_data[process] = [False, "0:00"]
		Monitor.screen_time_data[Monitor.current_date] = processes_data
		Monitor.processes_data = Monitor.screen_time_data[Monitor.current_date]

	@staticmethod
	def update_processes_data():
		"""
		Removes the data of processes no longer in Monitor.target_processes and adds the data of the 
		new processes in Monitor.target_processes to the Monitor.screen_time_data entry for the current date
		"""
		new_dict = {}

		for process in Monitor.target_processes:
			process_data = Monitor.screen_time_data[Monitor.current_date].get(process)
			if process_data: # if process is not new 
				new_dict[process] = process_data
			else: # if process is new 
				new_dict[process] = [False, "0:00"] # Set the new process data to default values

		Monitor.screen_time_data[Monitor.current_date] = new_dict # Data for only the processes in Monitor.target_processes
		Monitor.processes_data = Monitor.screen_time_data[Monitor.current_date]
			
	@staticmethod
	def get_processes_data():
		"""Gets the screen time data for the target processes from a json file."""
		Monitor.screen_time_data = handle_file_io("screen_time_data.json")

		if type(Monitor.screen_time_data) == dict:
			if Monitor.screen_time_data.get(Monitor.current_date):
				Monitor.update_processes_data()
				return
	
		Monitor.screen_time_data = {}
		Monitor.create_entries_for_target_processes()

	@staticmethod
	def reset_running_flags():
		"""
		Resets the running flag of each process in the processes_data dictionary to False. This method is 
		called to reset any process's running flag that's still True from the last time the program ran.
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
				if Monitor.processes_data[process_name][0]: # if the process was running before
					# Add one minute to the time spent running by the program and truncate the result; the seconds part is not needed 
					Monitor.processes_data[process_name][1] = str(Monitor.create_timedelta(Monitor.processes_data[process_name][1]) + ONE_MINUTE)[:4]
				else:
					Monitor.processes_data[process_name][0] = True # Set the process as running

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
		# Monitor.target_processes needs to be updated regularly as it gets it's content
		# from an external file that can be modified outside of this program
		Monitor.target_processes = get_target_processes() 
		
		Monitor.update_processes_data()
		Monitor.scan_processes()
		Monitor.update_closed_processes_data()
		Monitor.save_screen_time_data()
		Monitor.check_and_update_current_date()
		time.sleep(50)
