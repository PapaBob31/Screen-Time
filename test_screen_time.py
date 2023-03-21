from unittest import TestCase
from unittest.mock import Mock
from io import StringIO
import screen_time
from screen_time import handle_file_exception as hfe
from screen_time import handle_screen_data_exception as hsde
import sys

def file_setup():
	screen_time.open = Mock(return_value=StringIO())
	hfe()

def mock_hsde():
	screen_time.open = Mock(return_value=StringIO())
	hsde()


class TestInterface(TestCase):

	def setUp(self):
		screen_time.sys.exit = Mock(side_effect=sys.exit)

	def tearDown(self):
		screen_time.open = open # It is usually mocked during tests so it needs to be restored to default
		screen_time.sys.exit = sys.exit # It is usually mocked during tests so it needs to be restored to default
		screen_time.handle_file_exception = hfe # It was mocked during a few tests so it needs to be restored to default

	def test_handle_file_exceptions(self):
		screen_time.open = Mock(return_value=StringIO())
		self.assertRaises(SystemExit, screen_time.handle_file_exception)
		screen_time.open.assert_called_with("target_processes.json", "w")
		screen_time.sys.exit.assert_called_with("No process has been added yet! Please add a process with the -add command.")

	def test_get_target_processes_bad_file(self):
		"""Test for get_target_processes function when target_processes.json file has invalid json content"""
		screen_time.handle_file_exception = Mock(side_effect=file_setup)
		dummy_file = StringIO('["chrome.exe", "firefox.exe", "sublime_text.exe"')
		screen_time.open = Mock(return_value=dummy_file)
		self.assertRaises(SystemExit, screen_time.get_target_processes)
		screen_time.handle_file_exception.assert_called()

	def test_get_target_processes_good_file(self):
		"""Test for get_target_processes function when target_processes.json file has valid and expected json content"""
		screen_time.handle_file_exception = Mock()
		dummy_file = StringIO('["chrome.exe", "firefox.exe", "sublime_text.exe"]')
		screen_time.open = Mock(return_value=dummy_file)
		self.assertEqual(screen_time.get_target_processes(), ["chrome.exe", "firefox.exe", "sublime_text.exe"])
		screen_time.handle_file_exception.assert_not_called()

	def test_get_target_processes_invalid_file(self):
		"""Test for get_target_processes function when target_processes.json file has valid but unexpected json content"""
		screen_time.handle_file_exception = Mock(side_effect=file_setup)
		dummy_file = StringIO('"sublime_text.exe"')
		screen_time.open = Mock(return_value=dummy_file)
		self.assertRaises(SystemExit, screen_time.get_target_processes)
		screen_time.handle_file_exception.assert_called()
		
	def test_get_target_processes_empty_data_file(self):
		"""Test for get_target_processes function when target_processes.json file has an empty list as content"""
		dummy_file = StringIO('[]')
		screen_time.open = Mock(return_value=dummy_file)
		self.assertRaises(SystemExit, screen_time.get_target_processes)
		screen_time.sys.exit.assert_called_with("No process has been added yet! Please add a process with the -add command.")

	def test_change_format(self):
		self.assertEqual(screen_time.change_format("02:00"), "02 hrs 00 mins")

	def test_handle_screen_data_exception(self):
		screen_time.print = Mock()
		screen_time.open = Mock(return_value=StringIO())
		self.assertRaises(SystemExit, screen_time.handle_screen_data_exception)
		screen_time.open.assert_called_with("screen_time_data.json", "w")
		screen_time.print.assert_called_with("Error! damaged or invalid file contents in screen_time_data.json. Reformatting the file...")
		screen_time.sys.exit.assert_called_with("File has been reformatted and all screen time data has been cleared.")

	def test_add_processes(self):
		"""Test for the add_processes function"""
		screen_time.target_processes = ["explorer.exe"]
		screen_time.save_data = Mock()
		def wrapper():
			screen_time.add_processes(["__filename__", "-add", "chrome.exe", "notepad.exe", "notepad.exe"])
		self.assertRaises(SystemExit, wrapper)
		self.assertEqual(screen_time.target_processes, ["explorer.exe", "chrome.exe", "notepad.exe", "notepad.exe"])
		screen_time.sys.exit.assert_called_with("process added successfully")
		screen_time.save_data.assert_called()

	def test_remove_processes(self):
		screen_time.target_processes = ["explorer.exe", "notepad.exe", "chrome.exe"]
		screen_time.save_data = Mock()
		def wrapper():
			screen_time.remove_processes(["__filename__", "-remove", "chrome.exe", "explorer.exe"])
		self.assertRaises(SystemExit, wrapper)
		self.assertEqual(screen_time.target_processes, ["notepad.exe"])
		screen_time.sys.exit.assert_called_with("All valid processes were removed successfully")
		screen_time.save_data.assert_called()

	def test_handle_file_read(self):
		return
		screen_time.open = Mock(return_value=StringIO('{"test": [1, 2, 3]}'))
		data = screen_time.handle_file_read("json_file")
		self.assertEqual(data, {"test": [1, 2, 3]})

		def wrapper():
			screen_time.handle_file_read("json_file")

		screen_time.open = Mock(return_value=StringIO('{"test": [1, 2, 3}'))
		screen_time.handle_file_exception = Mock(side_effect=file_setup)
		self.assertRaises(SystemExit, wrapper)
		screen_time.handle_file_exception.assert_called()

		screen_time.open = Mock(side_effect=FileNotFoundError)
		screen_time.handle_file_exception = Mock(side_effect=file_setup)
		self.assertRaises(SystemExit, wrapper)
		screen_time.handle_file_exception.assert_called()


	def test_read_data(self):
		good_data = StringIO('{"2022-10-21": {"chrome.exe": [false, "0:00"], "notepad.exe": [false, "00:22"]}}')
		screen_time.open = Mock(return_value=good_data)
		self.assertEqual(screen_time.read_data("2022-10-21"), {"chrome.exe": [False, "0:00"], "notepad.exe": [False, "00:22"]})

		good_data = StringIO('{"2022-10-21": {"chrome.exe": [false, "0:00"], "notepad.exe": [false, "00:22"]}}')
		screen_time.open = Mock(return_value=good_data)
		screen_time.current_date = "2022-10-21"
		self.assertEqual(screen_time.read_data(None), {"chrome.exe": [False, "0:00"], "notepad.exe": [False, "00:22"]})

		def wrapper():
			screen_time.read_data("2022-10-21")

		invalid_data = StringIO('"test"')
		screen_time.open = Mock(return_value=invalid_data)
		screen_time.handle_screen_data_exception = Mock(side_effect=mock_hsde)
		self.assertRaises(SystemExit, wrapper)
		screen_time.sys.exit.assert_called_with("File has been reformatted and all screen time data has been cleared.")

		empty_data = StringIO('{}')
		screen_time.open = Mock(return_value=empty_data)
		self.assertRaises(SystemExit, wrapper)
		screen_time.sys.exit.assert_called_with("No screen time data available. Run screen_time_bckground.exe to update screen time data")

	def test_print_process_data():
		return
		
	def with_invalid_command(self, cmd_list, error_text):
		screen_time.sys.argv = cmd_list
		self.assertRaises(SystemExit, screen_time.process_commands)
		screen_time.sys.exit.assert_called_with(error_text)

	def with_valid_add_and_remove_commands(self):
		screen_time.get_target_processes = Mock(return_value=["firefox.exe", "notepad.exe", "cmd.exe"])
		screen_time.save_data = Mock()

		screen_time.sys.argv = ["__filename__", "-add", "random.exe"]
		screen_time.add_processes = Mock(side_effect=screen_time.add_processes)
		self.assertRaises(SystemExit, screen_time.process_commands)
		screen_time.add_processes.assert_called()

		screen_time.sys.argv = ["__filename__", "-remove", "cmd.exe"]
		screen_time.remove_processes = Mock(side_effect=screen_time.remove_processes)
		self.assertRaises(SystemExit, screen_time.process_commands)
		screen_time.remove_processes.assert_called()	

	def with_list_command(self):
		screen_time.get_target_processes = Mock(return_value=["notepad.exe", "cmd.exe"])
		screen_time.sys.argv = ["__filename__", "list"]
		self.assertRaises(SystemExit, screen_time.process_commands)
		screen_time.print.assert_any_call("cmd.exe")
		screen_time.print.assert_any_call("notepad.exe")

	def with_help_command(self):
		screen_time.sys.argv = ["__filename__", "/?"]
		self.assertRaises(SystemExit, screen_time.process_commands)
		screen_time.print.assert_called_with(screen_time.HELP_TEXT)

	def with_date_command(self):
		screen_time.print_process_data = Mock(side_effect=screen_time.print_process_data)
		screen_time.sys.argv = ["__filename__", "-date", "2022-10-21", "notepad.exe"]
		screen_time.process_commands()
		screen_time.print_process_data.assert_called_with("notepad.exe", "2022-10-21")

		screen_time.print_process_data = Mock(side_effect=screen_time.print_process_data)
		screen_time.sys.argv = ["__filename__", "-date", "2022-10-21"]
		screen_time.process_commands()
		screen_time.print_process_data.assert_called_with("all", "2022-10-21")

	def test_process_commands(self):
		backup_code = screen_time.get_target_processes
		self.with_invalid_command(["__filename__", "wack"], "Invalid command!")
		self.with_invalid_command(["__filename__", "wack", "wack2"], "Invalid command!")
		self.with_invalid_command(["__filename__", "-add"], "Invalid use of command!")
		self.with_invalid_command(["__filename__", "-remove"], "Invalid use of command!")
		self.with_invalid_command(["__filename__", "list", "more_args"], "Invalid command!")
		self.with_invalid_command(["__filename__", "/?", "more_args"], "Invalid command!")
		self.with_invalid_command(["__filename__", "-date"], "Invalid use of command!")
		self.with_date_command()
		self.with_valid_add_and_remove_commands()
		self.with_list_command()
		self.with_help_command()
		screen_time.get_target_processes = backup_code
