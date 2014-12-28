import logging
import sys
import unittest
from io import StringIO

try:
    from unittest.mock import MagicMock, mock_open, patch
except ImportError:
    from mock import MagicMock, mock_open, patch

try:
    from importlib import reload
except ImportError:
    from imp import reload

from sleuth.inject import _Break, _Call, _Inject, _Log, _Print


class TestInjectionActions(unittest.TestCase):
    def setUp(self):
        reload(logging)
        self.frame = self._get_test_frame()
        self.test_str = 'INJECTION TEST'
        self.fmt_str = '{message} {magic_number}'
        self.log_name = 'testlog'
        self.log = StringIO()
        logging.basicConfig(level=logging.DEBUG, stream=self.log)

    def tearDown(self):
        self.log_name = None
        self.log = None
        logging = None

    def _get_test_frame(self):
        """
        Return this function's execution frame object for testing purposes.

        This function sets the following local variables:
            message = 'Hello Sleuth!'
            magic_number = 42
        """

        message = 'Hello Sleuth!'
        magic_number = 42

        return sys._getframe()

    def test_Print(self):
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            action = _Print(self.test_str)
            action(self.frame)

            self.assertEqual(fake_stdout.getvalue().strip(), self.test_str)

    def test_Print_formatting(self):
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            action = _Print(self.fmt_str)
            expected_out = self.fmt_str.format(**self.frame.f_locals)
            action(self.frame)

            self.assertEqual(fake_stdout.getvalue().strip(), expected_out)

    def test_Print_to_file(self):
        fake_open = mock_open(mock=MagicMock())
        with patch('sleuth.inject.open', fake_open, create=True):
            action = _Print(self.fmt_str, file='junk.txt')
            expected_out = self.fmt_str.format(**self.frame.f_locals)
            action(self.frame)

            fake_file = fake_open.return_value.__enter__.return_value
            fake_file.write.assert_any_call(expected_out)

    def test_Call(self):
        func = MagicMock()
        action = _Call(func, 'message', kwarg='magic_number')
        message = self.frame.f_locals['message']
        magic_number = self.frame.f_locals['magic_number']
        action(self.frame)

        func.assert_called_once_with(message, kwarg=magic_number)

    def test_Log(self):
        action = _Log(self.test_str)
        action(self.frame)

        self.assertRegex(self.log.getvalue(), self.test_str)

    def test_Log_formatting(self):
        action = _Log(self.fmt_str)
        expected_out = self.fmt_str.format(**self.frame.f_locals)
        action(self.frame)

        self.assertRegex(self.log.getvalue(), expected_out)

    def test_Log_with_logName(self):
        action = _Log(self.test_str, logName=self.log_name)
        expected_out = '\S*{0}\S*{1}'.format(self.log_name, self.test_str)
        action(self.frame)

        self.assertRegex(self.log.getvalue(), expected_out)


if __name__ == '__main__':
    unittest.main()
