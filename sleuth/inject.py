import os.path
import sys
from collections import defaultdict


__all__ = ['trace', 'breakAt', 'printAt', 'logAt', 'callAt', 'commentAt',
           'injectAt']


def breakAt(filename, line):
    pass


def printAt(filename, line, fmtStr):
    _injector.print(filename, line, fmtStr)


def logAt(filename, line, fmtStr):
    pass


def callAt(filename, line, func, args=None, kwargs=None):
    pass


def commentAt(filename, start, end=None):
    pass


def injectAt(filename, line, code):
    pass


class _Injector:
    """
    Inject code into a running program by using CPython's tracing
    functionality. This class should only be used internally by this module.
    """

    def __init__(self):
        # (filename, line): [(func, args), ...]
        self.actions = defaultdict(list)
        self._enabled = False

    def _settrace(self, trace):
        # TODO: implement wrapper for sys.settrace() to manage other clients
        # of sys.settrace().
        pass

    def enable(self):
        sys.settrace(self.trace)
        sys.settrace = self._settrace
        self._enabled = True

    def disable(self):
        sys.settrace(None)
        self._enabled = False

    def trace(self, frame, event, arg):
        if self._enabled and event == 'line':
            code = frame.f_code
            filename = os.path.realpath(code.co_filename)
            lineno = frame.f_lineno

            loc = (filename, lineno)
            if loc in self.actions:
                for func, args in self.actions[loc]:
                    func(frame, *args)

        return self.trace

    def print(self, filename, line, fmtStr, where):
        loc = (os.path.realpath(filename), line)
        args = (fmtStr, where,)
        self.actions[loc].append((self.do_print, args))

    def do_print(self, frame, fmtStr, where):
        print(fmtStr)


# The global _Injector instance. This should be accessed by clients via the
# Injector context manager.
_injector = _Injector()


class Injector:
    """
    Provides a context for accessing the _Injector instance contained in the
    sleuth.inject module.
    """

    def __init__(self):
        self._injector = _injector

    def __enter__(self):
        self._injector.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        self._injector.disable()
