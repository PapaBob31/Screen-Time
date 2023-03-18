import sys, json
from datetime import datetime

current_date = str(datetime.now().date())
HELP_TEXT = ("This Program monitors how long a process runs for a day.\n\n" 
			 " screen_time [-add process] | [-remove process] | [process] | [list]\n\n" + 
			 " -add          Adds a process to the list of processes that's been monitored.\n" +
			 "                If a process is not added with this command, It can't be \n" +
			 "                monitored. It takes at least one process name as a parameter.\n\n" +
			 " -remove       removes a process from the list of processes that's been \n" +
			 "                monitored. It takes at least one process name as a parameter.\n\n" +
			 " list          Lists all the processes being monitored.\n\n"+
			 " process       Outputs the total amount of time a process has spent running\n" + 
			 "                for the day. The time is calculated from when the process\n"+
			 "                was added if it was added to the processes being monitored\n" +
			 "                that day else the time is calculated from when \n" + 
			 "                screen_time_bg.exe starts running which is on OS startup.\n" + 
			 " reset         Resets the program's data to default. Removes all monitored \n" + 
			 "                process. Clears screen_time data about all monitored processes\n\n" + 
			 "For the program to be able to monitor a process, screen_time_bg.exe \n" + 
			 "background process must always be running and the process must have \n" +
			 "been added with the -add command. If no commands are supplied, \n" +
			 "It prints how long all the processes being monitored have been running.")


command_list = ["-add", "-remove", "list", "/?"]

def handle_file_exception():
	"""Sets target_processes.json data to an empty list"""
	with open("target_processes.json", "w") as file:
		json.dump([], file)
	sys.exit("No process has been added yet! Please add a process with the -add command.")

def get_target_processes():
	"""Returns the list of target processes"""
	try:
		with open("target_processes.json") as file:
			try:
				target_processes = json.load(file)
			except json.decoder.JSONDecodeError:
				handle_file_exception()
	except FileNotFoundError:
		handle_file_exception()
	else:
		if not target_processes: 
			sys.exit("No process has been added yet! Please add a process with the -add command.")
	return target_processes

def change_format(time_string):
	"""Changes the time string command format from 00:00 to 0 hrs 0 mins"""
	new_string = time_string.split(":")
	return new_string[0] + " hrs " + new_string[1] + " mins"

def print_process_data(data, process_name):
	"""
	Prints out a process's screen_time_data onto the console
	param data: the dictionary that contains the screen_time_data
	param process_name: the key to get the process's screen_time_data from the dictionary
	"""
	if process_name == "all":
		for key, value in data.items():
			print(key + (" " * (44-len(key))) + change_format(value[1]))
		return

	print(process_name + (" " * (44-len(process_name))) + change_format(data[process_name][1]))

def handle_screen_data_exception():
	print("Error! damaged or invalid file contents in screen_time_data.json. Reformatting the file...")
	with open("screen_time_data.json", "w") as file:
		json.dump({}, file)
	sys.exit("File has been reformatted and all screen time data has been cleared.")

def read_data(process_name):
	"""Reads a process's screen_time_data from a file"""
	try:
		with open("screen_time_data.json", "r") as file:
			try:
				screen_time_data = json.load(file)
			except json.decoder.JSONDecodeError:
				handle_screen_data_exception()
	except FileNotFoundError:
		handle_screen_data_exception()

	if type(screen_time_data) != dict:
	# if the content of the json file is valid json but doesn't return a dict type
		handle_screen_data_exception()
	elif not screen_time_data:
		sys.exit("No screen time data available. Run screen_time_bckground.exe to update screen time data")

	data = screen_time_data.get(current_date) # Get the current date's screen_time_data for all target processes
	print_process_data(data, process_name)	

def save_data():
	with open("target_processes.json", "w") as file:
		json.dump(target_processes, file)


def add_or_remove_processes(args, target_processes):
	"""
	Adds or removes a process from target_processes parameter 
	based on the content of args parameter
	"""
	if args[1] == "-add":
		target_processes += args[2:]
		print("process added successfully")
	elif args[1] == "-remove":
		removed_processes = []
		for process in args[2:]:
			if process in removed_processes: # if -remove receives more than one process name that are the same
				continue 
			try:
				target_processes.remove(process)
				removed_processes.append(process)
			except ValueError:
				print(f"Error: {process} is not being monitored!")
		
		if removed_processes:
			print("All valid processes were removed successfully")
	else:
		sys.exit(f"Invalid command: '{process}'!")
	save_data()

if __name__ == "__main__":
	target_processes = get_target_processes()
	if len(sys.argv) > 2: # only the commands to add or remove process take parameters
		add_or_remove_processes(sys.argv, target_processes)

	elif len(sys.argv) == 2:
		if sys.argv[1] in target_processes:
			read_data(sys.argv[1])
		elif sys.argv[1].lower() == "list":
			for process in target_processes:
				print(process)
		elif sys.argv[1] == "/?":
			print(HELP_TEXT)
		elif sys.argv[1] == "-add" or sys.argv[1] == "-remove":
		# if -add or -remove commands were used and no parameters were supplied
			sys.exit("Error! Invalid use of command. Use /? for more info")
		else:
			sys.exit("Error! process is not being monitored.")

	else: # if no parameters/commands were supplied
		read_data("all")
