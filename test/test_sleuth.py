import importlib
import sys
import unittest
from functools import partial

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

try:
    from importlib import reload
except ImportError:
    from imp import reload

import sleuth

import fakemodule


class TestSleuthBreakOn(unittest.TestCase):

    def setUp(self):
        reload(sys)
        reload(fakemodule)
        self.ARGS = (42, 'test', 3.14)
        self.KWARGS = {'arg1': 10, 'arg2': 'hi'}
        self.RETVAL = object()
        self.EXCEPTION = Exception()
        sys.settrace = MagicMock()

    def tearDown(self):
        self.ARGS = None
        self.KWARGS = None
        self.RETVAL = None
        self.EXCEPTION = None
        fakemodule = None
        sys = None

    def test_breakOnEnter(self):
        sleuth.tap(fakemodule.doNothing, sleuth.breakOnEnter,
                   debugger='pdb')
        fakemodule.doNothing(self.ARGS, self.KWARGS)
        self.assertTrue(sys.settrace.called)

    def test_breakOnExit(self):
        sleuth.tap(fakemodule.doNothing, sleuth.breakOnExit,
                   debugger='pdb')
        fakemodule.doNothing(self.ARGS, self.KWARGS)
        self.assertTrue(sys.settrace.called)

    def test_breakOnResult_true(self):
        def compare(result):
            return result is self.RETVAL

        sleuth.tap(fakemodule.returnValue, sleuth.breakOnResult,
                   compare=compare, debugger='pdb')
        fakemodule.returnValue(self.RETVAL)
        self.assertTrue(sys.settrace.called)

    def test_breakOnResult_false(self):
        def compare(result):
            return result is self.RETVAL

        sleuth.tap(fakemodule.returnValue, sleuth.breakOnResult,
                   compare=compare, debugger='pdb')
        fakemodule.returnValue(None)
        self.assertFalse(sys.settrace.called)

    def test_breakOnException_with_exception(self):
        sleuth.tap(fakemodule.raiseException, sleuth.breakOnException,
                   exceptionList=(Exception,), debugger='pdb')
        fakemodule.raiseException(self.EXCEPTION)
        self.assertTrue(sys.settrace.called)

    def test_breakOnException_other_exception(self):
        caughtException = False

        try:
            sleuth.tap(fakemodule.raiseException, sleuth.breakOnException,
                       exceptionList=(ValueError,), debugger='pdb')
            fakemodule.raiseException(self.EXCEPTION)
        except Exception as e:
            caughtException = True
        finally:
            self.assertTrue(caughtException)
            self.assertFalse(sys.settrace.called)

    def test_breakOnException_no_exception(self):
        sleuth.tap(fakemodule.doNothing, sleuth.breakOnException,
                   exceptionList=(Exception,), debugger='pdb')
        fakemodule.doNothing()
        self.assertFalse(sys.settrace.called)


class TestSleuthCallOn(unittest.TestCase):
    def setUp(self):
        reload(fakemodule)
        self.ARGS = (42, 'test', 3.14)
        self.KWARGS = {'arg1': 10, 'arg2': 'hi'}
        self.RETVAL = object()
        self.EXCEPTION = Exception()
        self.CALLBACK = MagicMock()

    def tearDown(self):
        self.ARGS = None
        self.KWARGS = None
        self.RETVAL = None
        self.EXCEPTION = None
        self.CALLBACK = None

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
