import sys
import unittest
from io import StringIO

try:
    from unittest.mock import MagicMock, mock_open, patch
except ImportError:
    from mock import MagicMock, mock_open, patch

from sleuth.inject import _Break, _Call, _Inject, _Log, _Print


class TestInjectionActions(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

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


def _fake_open(*args, **kwargs):
    raise Exception()
    return StringIO()


if __name__ == '__main__':
    unittest.main()
