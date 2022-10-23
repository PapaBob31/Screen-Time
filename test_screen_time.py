from unittest import TestCase
from unittest.mock import Mock
from io import StringIO
import screen_time


class TestInterface(TestCase):

	def test_handle_file_exceptioms(self):
		dummy_file = StringIO()
		screen_time.open = Mock(return_value=dummy_file)
		self.assertRaises(SystemExit, screen_time.handle_processes_file_exception)
		screen_time.open.assert_called_with("target_processes.json", "w")

	def test_get_target_processes(self):

		dummy_file = StringIO('["chrome.exe", "firefox.exe", "sublime_text.exe"]')
		screen_time.open = Mock(return_value=dummy_file)
		target_processes = screen_time.get_target_processes()
		self.assertEqual(target_processes, ["chrome.exe", "firefox.exe", "sublime_text.exe"])

		dummy_file = StringIO('["chrome.exe", "firefox.exe", "sublime_text.exe"')
		screen_time.open = Mock(return_value=dummy_file)
		screen_time.get_target_processes()
		self.assertRaises(SystemExit, screen_time.get_target_processes)

		dummy_file = StringIO('"sublime_text.exe"')
		screen_time.open = Mock(return_value=dummy_file)
		screen_time.get_target_processes()
		self.assertRaises(SystemExit, screen_time.get_target_processes)

		dummy_file = StringIO('[]')
		screen_time.open = Mock(return_value=dummy_file)
		screen_time.get_target_processes()
		self.assertRaises(SystemExit, screen_time.get_target_processes)

		dummy_file = StringIO('[]')
		screen_time.open = Mock(side_effect=FileNotFoundError)
		screen_time.get_target_processes()
		self.assertRaises(SystemExit, screen_time.get_target_processes)
		