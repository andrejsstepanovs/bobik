import io
import sys
import unittest
from unittest.mock import Mock, patch
from src.my_print import print_text
from src.state import ApplicationState


class TestPrintText(unittest.TestCase):
    def setUp(self):
        self.state = Mock(spec=ApplicationState)

    def test_print_text_not_quiet(self):
        self.state.is_quiet = False
        expected_output: str = "Hello, world!\n"
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            print_text(self.state, "Hello, world!")
            self.assertEqual(mock_stdout.getvalue(), expected_output)

    def test_print_text_quiet(self):
        self.state.is_quiet = True
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            print_text(self.state, "Hello, world!")
            self.assertEqual(mock_stdout.getvalue(), "")

    def test_print_text_end_character(self):
        self.state.is_quiet = False
        expected_output: str = "Hello, world!"
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            print_text(self.state, "Hello, world!", end_character="")
            self.assertEqual(mock_stdout.getvalue(), expected_output)


if __name__ == '__main__':
    unittest.main()
