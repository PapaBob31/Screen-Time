from unittest import TestCase, mock
from unittest.mock import Mock, patch, mock_open
from datetime import datetime, timedelta
from io import StringIO
import subprocess, json
import screen_time_bg as test

Monitor = test.Monitor

class TestTime:
	def strftime(arg1, arg2):
		return "0:00"

	def date(arg):
		return "2022-11-21"

class TestData:
	stdout = ('"SynTPEnh.exe","6268","Console","54","15,832 K"\n' +
			  '"sublime_text.exe","3780","Console","54","50,436 K"\n' +
			  '"YouCamService.exe","6020","Console","54","10,360 K"\n' +
			  '"firefox.exe","6980","Console","54","3,476 K"\n' +
			  '"chrome.exe","2116","Console","54","125,788 K"\n' +
			  '"HPMSGSVC.exe","5740","Console","54","6,748 K"\n' +
			  '"plugin_host-3.3.exe","3140","Console","54","37,212 K"\n' +
			  '"chrome.exe","1872","Console","54","5,824 K"\n' +
			  '"plugin_host-3.8.exe","4612","Console","54","25,000 K"\n' +
			  '"chrome.exe","4976","Console","54","50,464 K"\n' +
			  '"chrome.exe","1016","Console","54","23,808 K"\n' +
			  '"cmd.exe","7088","Console","54","2,396 K"\n' +
			  '"conhost.exe","5576","Console","54","5,612 K"\n')
	now = TestTime


class TestScreenTime(TestCase):
	def setUp(self):
		Monitor.processes_data = {"chrome.exe": [False, "0:00"], "firefox.exe": [False, "0:00"], "sublime_text.exe": [False, "0:00"]}
		Monitor.target_processes = []

	def with_valid_data(self):
		test.open = Mock(return_value=StringIO('["chrome.exe", "firefox.exe", "sublime_text.exe"]'))
		Monitor.target_processes = test.get_target_processes()
		self.assertEqual(Monitor.target_processes, ["chrome.exe", "firefox.exe", "sublime_text.exe"])

	def with_invalid_data(self):
		test.open = Mock(return_value=StringIO('["chrome.exe", "firefox.exe", "sublime_text.exe"'))
		self.assertRaises(SystemExit, test.get_target_processes)

	def with_empty_data(self):
		test.open = Mock(return_value=StringIO('[]'))
		self.assertRaises(SystemExit, test.get_target_processes)

	def when_file_not_found(self):
		test.open = Mock(side_effect=FileNotFoundError)
		self.assertRaises(SystemExit, test.get_target_processes)

	def test_remove_duplicates(self):
		test_list = [1, 2, 3, 4, 1, 1, 5, 2, 3, 4]
		returned_list = test.remove_duplicates(test_list)
		expected_result = [1, 2, 3, 4, 5]
		self.assertEqual(expected_result, returned_list)
		test_list = ['a', 'b', 'a', 'c', 'c', 'd', 'b']
		returned_list = test.remove_duplicates(test_list)
		expected_result = ['a', 'b', 'c', 'd']
		self.assertEqual(expected_result, returned_list)

	def test_get_target_processes(self):
		self.with_valid_data()
		self.with_invalid_data()
		self.when_file_not_found()
		self.with_empty_data()

	def test_create_entries_for_target_processes(self):
		Monitor.target_processes = ["chrome.exe", "firefox.exe", "sublime_text.exe"]
		self.assertEqual(Monitor.processes_data, {"chrome.exe": [False, "0:00"], "firefox.exe": [False, "0:00"], "sublime_text.exe": [False, "0:00"]})

	def check_data_based_on(self, current_date, dummy_file_data, expected_output, processes_list, side_effect=None):
		Monitor.current_date = current_date
		Monitor.target_processes = processes_list
		dummy_file = StringIO()
		json.dump(dummy_file_data, dummy_file)
		dummy_file.seek(0, 0)
		if not side_effect:
			test.open = Mock(return_value=dummy_file)
		else:
			test.open = Mock(side_effect=side_effect)
		Monitor.get_processes_data()
		self.assertEqual(Monitor.screen_time_data[Monitor.current_date], expected_output)
		self.assertIs(Monitor.processes_data, Monitor.screen_time_data[Monitor.current_date])

	def test_get_processes_data(self):
		processes_list = ["chrome.exe", "firefox.exe", "sublime_text.exe"]
		file_data = {"2022-10-21": {"chrome.exe": [False, "0:00"], "firefox.exe": [False, "0:30"], "sublime_text.exe": [False, "2:22"]}}
		new_data = {"chrome.exe": [False, "0:00"], "firefox.exe": [False, "0:00"], "sublime_text.exe": [False, "0:00"]}

		self.check_data_based_on("2022-10-21", file_data, file_data["2022-10-21"], processes_list)

		self.check_data_based_on("2022-11-32", file_data, new_data, processes_list)

		bad_file_data = '{"2022-10-21": {"chrome.exe": [False, "0:00"], "firefox.exe": [False, "0:30"], "sublime_text.exe": [False, "2:22"}'
		self.check_data_based_on("2022-10-21", bad_file_data, new_data, processes_list)

		self.check_data_based_on("2022-10-21", None, new_data, processes_list, side_effect=FileNotFoundError)

		processes_list = ["chrome.exe", "firefox.exe", "cmd.exe"]
		new_data = {"chrome.exe": [False, "0:00"], "firefox.exe": [False, "0:30"], "cmd.exe": [False, "0:00"]}
		self.check_data_based_on("2022-10-21", file_data, new_data, processes_list)

	def test_save_app_data(self):
		Monitor.screen_time_data = {"2022-10-21": {"chrome.exe": [False, "0:00"], "firefox.exe": [False, "0:30"], "sublime_text.exe": [False, "2:22"]}}
		test_file = StringIO()
		test.open = Mock(side_effect=open)
		Monitor.save_screen_time_data()
		test.open.assert_called_with("screen_time_data.json", "w")

	def test_create_timedelta(self):
		obj = Monitor.create_timedelta("10:30")
		self.assertIsInstance(obj, timedelta)

	def test_check_and_update_current_date(self):
		Monitor.screen_time_data = {"2022-10-21": {"chrome.exe": [False, "0:00"], "firefox.exe": [False, "0:30"], "sublime_text.exe": [False, "2:22"]}}
		new_screen_time_data = {"2022-10-21": {"chrome.exe": [False, "0:00"], "firefox.exe": [False, "0:30"], "sublime_text.exe": [False, "2:22"]}, "2022-11-21": {}}
		test.datetime = TestData
		Monitor.check_and_update_current_date()
		self.assertEqual(Monitor.current_date, "2022-11-21")
		self.assertEqual(Monitor.screen_time_data, new_screen_time_data)

	def test_reset_running_flags(self):
		Monitor.processes_data["firefox.exe"][0] = True
		Monitor.processes_data["chrome.exe"][0] = True
		Monitor.reset_running_flags()
		self.assertEqual(Monitor.processes_data["firefox.exe"][0], False)
		self.assertEqual(Monitor.processes_data["chrome.exe"][0], False)

	def test_scan_processes(self):
		subprocess.run = Mock(return_value=TestData)
		Monitor.target_processes = ["chrome.exe", "firefox.exe", "sublime_text.exe"]

		# The function still needs to do it's job outside this test function, that's the reason for the side_effect kwarg.
		# It's only mocked here to see if it was called with  some specific arguments.
		Monitor.validate_and_update_process_data = Mock(side_effect=Monitor.validate_and_update_process_data)

		Monitor.scan_processes()
		Monitor.validate_and_update_process_data.assert_any_call("chrome.exe")
		Monitor.validate_and_update_process_data.assert_any_call("firefox.exe")
		Monitor.validate_and_update_process_data.assert_any_call("sublime_text.exe")
 
	def test_validate_and_update_process_data(self):
		Monitor.target_processes = ["chrome.exe", "firefox.exe", "sublime_text.exe"]
		Monitor.validate_and_update_process_data("chrome.exe")
		self.assertEqual(Monitor.target_processes, ["firefox.exe", "sublime_text.exe"])
		self.assertEqual(Monitor.processes_data["chrome.exe"][0], True)

		Monitor.target_processes = ["chrome.exe", "firefox.exe", "sublime_text.exe"]
		Monitor.validate_and_update_process_data("random.exe")
		self.assertEqual(Monitor.target_processes, ["chrome.exe", "firefox.exe", "sublime_text.exe"])

	def test_update_closed_processes_data(self):
		Monitor.processes_data["firefox.exe"][0] = True
		Monitor.processes_data["sublime_text.exe"][0] = True
		Monitor.processes_data["chrome.exe"][0] = True
		Monitor.target_processes = ["firefox.exe"]
		Monitor.update_closed_processes_data()
		self.assertEqual(Monitor.processes_data["firefox.exe"][0], False)
		self.assertEqual(Monitor.processes_data["sublime_text.exe"][0], True)
		self.assertEqual(Monitor.processes_data["chrome.exe"][0], True)

	def test_reset_data_for_new_day(self):
		Monitor.processes_data["chrome.exe"][1] = "9:00"
		Monitor.processes_data["firefox.exe"][1] = "3:45"
		Monitor.processes_data["sublime_text.exe"][1] = "9:45"
		Monitor.reset_data_for_new_day()
		self.assertEqual(Monitor.processes_data["chrome.exe"][1], "0:00")
		self.assertEqual(Monitor.processes_data["firefox.exe"][1], "0:00")
		self.assertEqual(Monitor.processes_data["sublime_text.exe"][1], "0:00")

# open_mock = mock_open()
# json.dump = Mock()
# with patch("test.open", open_mock):
# 	Monitor.save_screen_time_data()
# open_mock.assert_called_with("screen_time_data.json", "w")