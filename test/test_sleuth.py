import importlib
import logging
import sys
import unittest
from functools import partial
from io import StringIO

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


class TestSleuthLogging(unittest.TestCase):
    def setUp(self):
        reload(logging)
        reload(fakemodule)
        self.ARGS = (42, 'test', 3.14)
        self.KWARGS = {'arg1': 10, 'arg2': 'hi'}
        self.RETVAL = object()
        self.EXCEPTION = Exception()
        self.LOGNAME = 'testlog'
        self.LOGGER = logging.getLogger(self.LOGNAME)
        self.LOG = StringIO()
        logging.basicConfig(level=logging.DEBUG, stream=self.LOG)

    def tearDown(self):
        self.ARGS = None
        self.KWARGS = None
        self.RETVAL = None
        self.EXCEPTION = None
        self.LOGNAME = None
        self.LOGGER = None
        self.LOG = None
        fakemodule = None
        logging = None

    def test_logCalls(self):
        enterRegex = r'\S*\[\d+\] Calling \S+\(\)'
        exitRegex = r'\S*\[\d+] Exiting \S+\(\)\s\[\d+\.\d+ seconds\]'
        sleuth.tap(fakemodule.doNothing, sleuth.logCalls, logName=self.LOGNAME)
        fakemodule.doNothing(*self.ARGS, **self.KWARGS)
        self.assertRegex(self.LOG.getvalue(), enterRegex)
        self.assertRegex(self.LOG.getvalue(), exitRegex)

    def test_logOnException_with_exception(self):
        caughtException = False
        logRegex = r"Exception raised in \S*(): '\S*: \S*'"
        sleuth.tap(fakemodule.raiseException, sleuth.logOnException,
                   exceptionList=(Exception,))

        try:
            fakemodule.raiseException(self.EXCEPTION)
        except Exception as e:
            caughtException = True
        finally:
            self.assertTrue(caughtException)
            self.assertRegex(self.LOG.getvalue(), logRegex)

    def test_logOnException_with_exception_suppress(self):
        logRegex = r"Exception raised in \S*(): '\S*: \S*'"
        sleuth.tap(fakemodule.raiseException, sleuth.logOnException,
                   exceptionList=(Exception,), suppress=True)
        fakemodule.raiseException(self.EXCEPTION)
        self.assertRegex(self.LOG.getvalue(), logRegex)

    def test_logOnException_other_exception(self):
        caughtException = False
        logRegex = r'^$'
        sleuth.tap(fakemodule.raiseException, sleuth.logOnException,
                   exceptionList=(ValueError,))

        try:
            fakemodule.raiseException(self.EXCEPTION)
        except Exception as e:
            caughtException = True
        finally:
            self.assertTrue(caughtException)
            self.assertRegex(self.LOG.getvalue(), logRegex)

    def test_logOnException_no_exception(self):
        logRegex = r'^$'
        sleuth.tap(fakemodule.doNothing, sleuth.logOnException,
                   exceptionList=(Exception,), suppress=True)
        fakemodule.doNothing()
        self.assertRegex(self.LOG.getvalue(), logRegex)


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
        fakemodule.doNothing(*self.ARGS, **self.KWARGS)
        self.assertTrue(sys.settrace.called)

    def test_breakOnExit(self):
        sleuth.tap(fakemodule.doNothing, sleuth.breakOnExit,
                   debugger='pdb')
        fakemodule.doNothing(*self.ARGS, **self.KWARGS)
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
        fakemodule.doNothing(*self.ARGS, **self.KWARGS)
        self.CALLBACK.assert_called_once_with(*self.ARGS, **self.KWARGS)

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


class TestSleuthMisc(unittest.TestCase):
    def setUp(self):
        reload(fakemodule)
        self.SKIP_RETVAL = object()
        self.RETVAL = object()

    def tearDown(self):
        self.SKIP_RETVAL = None
        self.RETVAL = None
        fakemodule = None

    def test_skip_no_retval(self):
        sleuth.tap(fakemodule.doNothing, sleuth.skip)
        fakemodule.doNothing()
        self.assertFalse(fakemodule.doNothing.called)

    def test_skip_with_retval(self):
        sleuth.tap(fakemodule.doNothing, sleuth.skip,
                   returnValue=self.SKIP_RETVAL)
        result = fakemodule.doNothing()
        self.assertFalse(fakemodule.doNothing.called)
        self.assertEqual(result, self.SKIP_RETVAL)

    def test_substitue(self):
        sleuth.tap(fakemodule.doNothing, sleuth.substitute,
                   replacement=fakemodule.returnValue)
        result = fakemodule.doNothing(self.RETVAL)
        self.assertFalse(fakemodule.doNothing.called)
        self.assertEqual(result, self.RETVAL)

if __name__ == '__main__':
    unittest.main()