import logging
import sys
import textwrap
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

import sleuth.inject
from sleuth.inject import (_Break, _Call, _Inject, _Log, _Print, break_at,
                           call_at, comment_at, inject_at, log_at, print_at)

import fakescript_inj


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

    def test_Break(self):
        with patch('sleuth.inject.set_trace', MagicMock()) as fake_set_trace:
            action = _Break()
            action(self.frame)

            import pdb
            fake_set_trace.assert_called_once_with(self.frame, pdb)

    def test_Break_ipdb(self):
        with patch('sleuth.inject.set_trace', MagicMock()) as fake_set_trace:
            action = _Break(debugger='ipdb')
            action(self.frame)

            import ipdb
            fake_set_trace.assert_called_once_with(self.frame, ipdb)

    def test_Inject(self):
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            code = 'print("{0}")'.format(self.test_str)
            action = _Inject(code)
            action(self.frame)

            self.assertEqual(fake_stdout.getvalue().strip(), self.test_str)

    def test_Inject_multiline(self):
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            lines_to_print = 3
            code = """\
                   for i in range({0}):
                       print("{1}", i)
                   """.format(lines_to_print, self.test_str)
            code = textwrap.dedent(code)
            action = _Inject(code)
            action(self.frame)

            fake_stdout.seek(0)
            for i in range(lines_to_print):
                line = fake_stdout.readline()
                self.assertEqual(line.strip(), '{0} {1}'.format(self.test_str,
                                                                i))


class TestInjectionFunctions(unittest.TestCase):
    def setUp(self):
        reload(sleuth.inject)  # Nuke state stored within sleuth.inject
        self._path = list(sys.path)
        self._argv = list(sys.argv)
        sys.argv[:] = [sleuth.__main__.__file__, fakescript_inj.__file__]
        self.test_str = 'INJECTION TEST'
        self.first_msg = 'FIRST MESSAGE'
        self.second_msg = 'SECOND MESSAGE'
        self.test_script = fakescript_inj.__file__

    def tearDown(self):
        sys.path[:] = self._path
        sys.argv[:] = self._argv
        self.test_str = None
        self.first_msg = None
        self.second_msg = None
        self.test_script = None

    def test_print_at(self):
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            print_at(self.test_script, 3, self.test_str)
            sleuth.main()

            fake_stdout.seek(0)
            self.assertEqual(fake_stdout.readline().strip(), self.first_msg)
            self.assertEqual(fake_stdout.readline().strip(), self.test_str)
            self.assertEqual(fake_stdout.readline().strip(), self.second_msg)

    def test_call_at(self):
        def func():
            print(self.test_str)

        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            call_at(self.test_script, 3, func)
            sleuth.main()

            fake_stdout.seek(0)
            self.assertEqual(fake_stdout.readline().strip(), self.first_msg)
            self.assertEqual(fake_stdout.readline().strip(), self.test_str)
            self.assertEqual(fake_stdout.readline().strip(), self.second_msg)


if __name__ == '__main__':
    unittest.main()
