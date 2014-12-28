import logging
import os.path
import sys
from collections import defaultdict

from ._util import import_, set_trace


__all__ = ['break_at', 'print_at', 'log_at', 'call_at', 'comment_at',
           'inject_at']


def break_at(filename, line, debugger='pdb', indent=None):
    action = _Break(debugger)
    action.indent = indent
    _injector.add(filename, line, action)


def print_at(filename, line, fmtStr, file=None, indent=None):
    action = _Print(fmtStr, file)
    action.indent = indent
    _injector.add(filename, line, action)


def log_at(filename, line, fmtStr, level=logging.DEBUG, logName=None,
           indent=None):
    action = _Log(fmtStr, level, logName)
    action.indent = indent
    _injector.add(filename, line, action)


def call_at(filename, line, func, args=None, kwargs=None, indent=None):
    args = args if args is not None else []
    kwargs = kwargs if kwargs is not None else {}
    action = _Call(func, *args, **kwargs)
    action.indent = indent
    _injector.add(filename, line, action)


def inject_at(filename, line, code, indent=None):
    action = _Inject(code)
    action.indent = indent
    _injector.add(filename, line, action)


def comment_at(filename, start, end=None, indent=None):
    if end is None:
        end = start

    for lineno in range(start, end + 1):
        _injector.comment(filename, lineno)


def _getframe():
    """Get the execution frame of the caller."""
    return sys._getframe().f_back


class _Action:
    """Base class for injection actions."""
    def __init__(self):
        self.indent = None

    def __call__(self, frame):
        pass


class _Break(_Action):
    """
    Break into debug mode in a given execution frame.
    """
    def __init__(self, debugger='pdb'):
        super().__init__()
        self._debugger = import_(debugger)

    def __call__(self, frame):
        set_trace(frame, self._debugger)


class _Print(_Action):
    """
    Perform a printing action in the context of a given execution frame.
    """
    def __init__(self, fmtStr, file=None):
        super().__init__()
        self._fmtStr = fmtStr
        self._file = file if file is not None else sys.stdout

    def __call__(self, frame):
        vars_ = frame.f_globals
        vars_.update(frame.f_locals)

        if type(self._file) is str:
            with open(self._file, 'a') as f:
                print(self._fmtStr.format(**vars_), file=f)
        else:
            print(self._fmtStr.format(**vars_), file=self._file)


class _Log(_Action):
    """
    Perform a logging action in the context of a given execution frame.
    """
    def __init__(self, fmtStr, level=logging.DEBUG, logName=None):
        super().__init__()
        self._fmtStr = fmtStr
        self._level = level
        self._logName = logName

    def __call__(self, frame):
        vars_ = frame.f_globals
        vars_.update(frame.f_locals)

        logName = (self._logName if self._logName is not None
                   else vars_['__name__'])
        logger = logging.getLogger(logName)
        logMsg = self._fmtStr.format(**vars_)
        logger.log(self._level, logMsg)


class _Call(_Action):
    """
    Perform a function call in the context of a given execution frame.
    """
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def __call__(self, frame):
        vars_ = frame.f_globals
        vars_.update(frame.f_locals)
        args = [vars_[arg] for arg in self._args]
        kwargs = {key: vars_[val] for key, val in self._kwargs.items()}
        self._func(*args, **kwargs)


class _Inject(_Action):
    """
    Perform arbitrary code injection in the context of a given
    execution frame.
    """
    def __init__(self, code):
        super().__init__()

        if not code.endswith('\n'):
            code += '\n'
        self._code = compile(code, '<string>', 'exec')

    def __call__(self, frame):
        exec(self._code, frame.f_globals, frame.f_locals)


class _Injector:
    """Class to store, manage, and execute injection actions."""
    def __init__(self):
        # self._actions[filename][line] -> [statement_1, ..., statement_n]
        self._actions = defaultdict(lambda: defaultdict(list))
        self._commented = set()

        self._enabled = False

    def add(self, filename, line, action):
        self._actions[filename][line].append(action)

    def comment(self, filename, line):
        self._commented.add((filename, line))

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def inject_hooks(self, filename):
        modified_file = ''
        actions = self._actions[filename]
        with open(filename, 'r') as f:
            for lineno, line in enumerate(f, start=1):
                indent_len = len(line) - len(line.lstrip())
                indent = line[0: indent_len]

                if (filename, lineno) in self._commented:
                    line = indent + '# ' + line.lstrip()

                if lineno in actions:
                    injection = indent
                    injection += 'import sleuth.inject; '
                    injection += ('sleuth.inject._injector.hook("{0}", {1}, '
                                  'sleuth.inject._getframe()); '
                                  .format(filename, lineno))
                    modified_file += injection
                modified_file += line

        return modified_file

    def hook(self, filename, lineno, frame):
        if self._enabled:
            for action in self._actions[filename][lineno]:
                action(frame)


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
        return self._injector

    def __exit__(self, exc_type, exc_value, traceback):
        self._injector.disable()
