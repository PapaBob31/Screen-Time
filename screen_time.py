import sys, json
from datetime import datetime

current_date = str(datetime.now().date())
HELP_TEXT = ("This Program monitors how long a process runs for a day.\n\n" 
			 " screen_time [-add process] | [-remove process] | [date[process]] | [list]\n\n" + 
			 " -add          Adds a process to the list of processes that's been monitored.\n" +
			 "                If a process is not added with this command, It can't be \n" +
			 "                monitored. It takes at least one process name as a parameter.\n\n" +
			 " -remove       removes a process from the list of processes that's been \n" +
			 "                monitored. It takes at least one process name as a parameter.\n\n" +
			 " list          Lists all the processes being monitored.\n\n"+
			 " date[process] A date (format: 'year-month-date'). It may be optionally followed\n"+
			 " 				  by the name of the process. If a name of a process follows, It\n" +
			 "                outputs how long a monitored process ran on that date. If not,\n" + 
			 "                it outputs how long all monitored process e.g screentime 2023-03-17 \n" +
			 " process       Outputs the total amount of time a process has spent running\n" + 
			 "                for the day as long as the process is in the list of processes\n" +
			 "                being monitored\n\n"+
			 " reset         Resets the program's data to default. Removes all monitored \n" + 
			 "                process. Clears screen_time data about all monitored processes\n\n" + 
			 "For the program to be able to monitor a process, screen_time_bg.exe background\n" + 
			 "process must always be running and the process must have been added with the\n" +
			 "-add command. If no commands were supplied, It prints how long all the\n" +
			 "processes being monitored have been running.") # needs to be edited


command_list = ["-add", "-remove", "list", "/?", "-date"] # 2023-03-17

def handle_file_exception():
	"""Sets target_processes.json data to an empty list"""
	with open("target_processes.json", "w") as file:
		json.dump([], file)
	sys.exit("No process has been added yet! Please add a process with the -add command.")

def handle_file_read(file_name):
	"""Handles reading of data from JSON file"""
	try:
		with open(file_name) as file:
			try:
				return json.load(file)
			except json.decoder.JSONDecodeError:
				handle_file_exception()
	except FileNotFoundError:
		handle_file_exception()

def get_target_processes():
	"""Returns the list of target processes"""
	target_processes = handle_file_read("target_processes.json")
	if type(target_processes) != list:
		# if the content of the json file is valid json but doesn't return a dict type
		handle_file_exception()
	elif not target_processes: 
		sys.exit("No process has been added yet! Please add a process with the -add command.")
	return target_processes

def change_format(time_string):
	"""Changes the time string command format from 00:00 to 00 hrs 00 mins"""
	new_string = time_string.split(":")
	return new_string[0] + " hrs " + new_string[1] + " mins"

def handle_screen_data_exception():
	print("Error! damaged or invalid file contents in screen_time_data.json. Reformatting the file...")
	with open("screen_time_data.json", "w") as file:
		json.dump({}, file)
	sys.exit("File has been reformatted and all screen time data has been cleared.")

def read_data(date):
	"""Reads a process's screen_time_data from a file"""
	screen_time_data = handle_file_read("screen_time_data.json")
	if type(screen_time_data) != dict:
	# if the content of the json file is valid json but doesn't return a dict type
		handle_screen_data_exception()
	elif not screen_time_data:
		sys.exit("No screen time data available. Run screen_time_bckground.exe to update screen time data")

	if date:
		data = screen_time_data.get(date)
	else:
		data = screen_time_data.get(current_date) # Get the current date's screen_time_data for all target processes
	if not data and date:# if there's no data for the date specified
		sys.exit("No record for the date specified!")
	return data

def print_process_data(process_name, date=None):
	""" Prints out a process's screen_time_data onto the console."""
	data = read_data(date)
	if process_name == "all":
		for key, value in data.items():
			print(key + (" " * (44-len(key))) + change_format(value[1]))
		return

	print(process_name + (" " * (44-len(process_name))) + change_format(data[process_name][1]))


def save_data():
	"""Saves the list of processes being monitored in a json file"""
	with open("target_processes.json", "w") as file:
		json.dump(target_processes, file)

def add_processes(args):
	"""Adds a process to target_processes list"""
	for process in args[2:]: # Loops through all arguments immediately following '-add'
		target_processes.append(process.lower())
	save_data()
	sys.exit("process added successfully")
		
def remove_processes(args):
	"""Removes a process from target_processes list"""
	removed_processes = []
	for process in args[2:]: # Loops through all arguments immediately following '-remove'	
		if process in removed_processes: # if -remove receives more than one process name arguments that are the same
			continue 
		try:
			target_processes.remove(process)
			removed_processes.append(process)
		except ValueError:
			sys.exit(f"Error: {process} is not being monitored!")

	save_data()
	sys.exit("All valid processes were removed successfully")

def process_commands(): # needs to be refactored!
	target_processes = get_target_processes()
	sys.argv[1] = sys.argv[1].lower()
	if len(sys.argv) > 2:
		if sys.argv[1] == "-add":
			add_processes(sys.argv)
		if sys.argv[1] == "-remove":
			remove_processes(sys.argv)
		if sys.argv[1] == "-date":
			if len(sys.argv) == 4:
				print_process_data(sys.argv[3], sys.argv[2])
			elif len(sys.argv) == 3:
				print_process_data("all", sys.argv[2])
	elif len(sys.argv) == 2:
		if sys.argv[1] == "list":
			for process in target_processes:
				print(process)
			sys.exit()
		elif sys.argv[1] == "/?":
			print(HELP_TEXT)
			sys.exit()
		elif sys.argv[1] in target_processes:
			print_process_data(sys.argv[1])
		elif sys.argv[1] in command_list:
			sys.exit("Invalid use of command!")
	else:
		print_process_data("all")
	sys.exit("Invalid command!")

if __name__ == "__main__":
	process_commands()
