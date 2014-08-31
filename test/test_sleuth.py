import importlib
import unittest
from functools import partial
from unittest.mock import MagicMock

import sleuth

import fakemodule


class TestSleuthCallOn(unittest.TestCase):
    def setUp(self):
        self.ARGS = (42, 'test', 3.14)
        self.KWARGS = {'arg1': 10, 'arg2': 'hi'}
        self.RETVAL = object()
        self.EXCEPTION = Exception()
        self.CALLBACK = MagicMock()

    def tearDown(self):
        self.ARGS = None
        self.KWARGS = None
        self.RETVAL = None
        self.EXCEPTION = Exception()
        self.CALLBACK = None
        importlib.reload(fakemodule)

    def test_callOnEnter(self):
        sleuth.tap(fakemodule.doNothing, sleuth.callOnEnter,
                   callback=self.CALLBACK)
        fakemodule.doNothing(self.ARGS, self.KWARGS)
        self.CALLBACK.assert_called_once_with(self.ARGS, self.KWARGS)

    def test_callOnExit(self):
        sleuth.tap(fakemodule.returnValue, sleuth.callOnExit,
                   callback=self.CALLBACK)
        fakemodule.returnValue(self.RETVAL)
        self.CALLBACK.assert_called_once_with(self.RETVAL)

    def test_callOnResult_true(self):
        def compare(result):
            return result is self.RETVAL

        sleuth.tap(fakemodule.returnValue, sleuth.callOnResult,
                   compare=compare, callback=self.CALLBACK)
        fakemodule.returnValue(self.RETVAL)
        self.CALLBACK.assert_called_once_with(self.RETVAL)

    def test_callOnResult_false(self):
        def compare(result):
            return result is self.RETVAL

        sleuth.tap(fakemodule.returnValue, sleuth.callOnResult,
                   compare=compare, callback=self.CALLBACK)
        fakemodule.returnValue(None)
        self.assertFalse(self.CALLBACK.called)

    def test_callOnException_with_exception(self):
        # Don't reraise exception in callback
        self.CALLBACK.return_value = True

        sleuth.tap(fakemodule.raiseException, sleuth.callOnException,
                   exceptionList=(Exception,), callback=self.CALLBACK)
        fakemodule.raiseException(self.EXCEPTION)
        self.CALLBACK.assert_called_once_with(self.EXCEPTION)

    def test_callOnException_other_exception(self):
        caughtException = False

        try:
            # Don't reraise exception in callback
            self.CALLBACK.return_value = True

            sleuth.tap(fakemodule.raiseException, sleuth.callOnException,
                       exceptionList=(ValueError,), callback=self.CALLBACK)
            fakemodule.raiseException(self.EXCEPTION)
        except Exception as e:
            caughtException = True
        finally:
            self.assertTrue(caughtException)
            self.assertFalse(self.CALLBACK.called)

    def test_callOnException_no_exception(self):
        sleuth.tap(fakemodule.doNothing, sleuth.callOnException,
                   exceptionList=(Exception,), callback=self.CALLBACK)
        fakemodule.doNothing()
        self.assertFalse(self.CALLBACK.called)


if __name__ == '__main__':
    unittest.main()
