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
        self.LOGNAME = 'testlog'
        self.LOG = StringIO()
        logging.basicConfig(level=logging.DEBUG, stream=self.LOG)

    def tearDown(self):
        self.LOGNAME = None
        self.LOG = None
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
            # Create the action
            fmtStr = 'PRINT INJECTION TEST'
            action = _Print(fmtStr)

            # Perform the action
            frame = self._get_test_frame()
            expected_out = fmtStr
            action(frame)

            self.assertEqual(fake_stdout.getvalue().strip(), expected_out)

    def test_Print_formatting(self):
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            # Create the action
            fmtStr = '{message} {magic_number}'
            action = _Print(fmtStr)

            # Perform the action
            frame = self._get_test_frame()
            expected_out = '{message} {magic_number}'.format(**frame.f_locals)
            action(frame)

            self.assertEqual(fake_stdout.getvalue().strip(), expected_out)

    def test_Print_to_file(self):
        fake_open = mock_open(mock=MagicMock())
        with patch('sleuth.inject.open', fake_open, create=True):
            # Create the action
            fmtStr = '{message} {magic_number}'
            action = _Print(fmtStr, file='junk.txt')

            # Perform the action
            frame = self._get_test_frame()
            expected_out = '{message} {magic_number}'.format(**frame.f_locals)
            action(frame)

            fake_file = fake_open.return_value.__enter__.return_value
            fake_file.write.assert_any_call(expected_out)

    def test_Call(self):
        # Create the action
        func = MagicMock()
        action = _Call(func, 'message', kwarg='magic_number')

        # Perform the action
        frame = self._get_test_frame()
        message = frame.f_locals['message']
        magic_number = frame.f_locals['magic_number']
        action(frame)

        func.assert_called_once_with(message, kwarg=magic_number)

    def test_Log(self):
        # Create the action
        fmtStr = 'LOG INJECTION TEST'
        action = _Log(fmtStr)

        # Perform the action
        frame = self._get_test_frame()
        expected_out = fmtStr
        action(frame)

        self.assertRegex(self.LOG.getvalue(), expected_out)

    def test_Log_formatting(self):
        # Create the action
        fmtStr = '{message} {magic_number}'
        action = _Log(fmtStr)

        # Perform the action
        frame = self._get_test_frame()
        expected_out = '{message} {magic_number}'.format(**frame.f_locals)
        action(frame)

        self.assertRegex(self.LOG.getvalue(), expected_out)

    def test_Log_with_logName(self):
        # Create the action
        fmtStr = 'LOG INJECTION TEST'
        action = _Log(fmtStr, logName=self.LOGNAME)

        # Perform the action
        frame = self._get_test_frame()
        expected_out = '\S*{0}\S*{1}'.format(self.LOGNAME, fmtStr)
        action(frame)

        self.assertRegex(self.LOG.getvalue(), expected_out)


if __name__ == '__main__':
    unittest.main()
