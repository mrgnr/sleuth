import os.path
import sys
from collections import defaultdict


__all__ = ['break_at', 'print_at', 'log_at', 'call_at', 'comment_at',
           'inject_at']


def break_at(filename, line, indent=None):
    action = _Break()
    _injector.add(filename, line, action)


def print_at(filename, line, fmtStr, file=None, indent=None):
    action = _Print(fmtStr, file, indent)
    _injector.add(filename, line, action)


def log_at(filename, line, fmtStr, indent=None):
    pass


def call_at(filename, line, func, args=None, kwargs=None, indent=None):
    pass


def comment_at(filename, start, end=None, indent=None):
    pass


def inject_at(filename, line, code, indent=None):
    _injector.add(filename, line, code)


class _Action:
    @property
    def indent(self):
        return None

    def __call__(self, locals_, globals_):
        pass


class _Break(_Action):
    def __init__(self, indent=None):
        self._indent = indent

    @property
    def indent(self):
        return self._indent

    def __call__(self, locals_, globals_):
        pdb.set_trace()


class _Print(_Action):
    def __init__(self, fmtStr, file=None, indent=None):
        self._fmtStr = fmtStr
        self._file = file if file is not None else sys.stdout
        self._indent = indent

    @property
    def indent(self):
        return self._indent

    def __call__(self, locals_, globals_):
        vars_ = dict(globals_)
        vars_.update(locals_)

        if type(self._file) is str:
            with open(self._file, 'a') as f:
                print(self._fmtStr.format(**vars_), file=f)
        else:
            print(self._fmtStr.format(**vars_), file=self._file)


class _Injector:
    def __init__(self):
        # self._actions[filename][line] -> [statement_1, ..., statement_n]
        self._actions = defaultdict(lambda: defaultdict(list))

        self._enabled = False

    def add(self, filename, line, action):
        self._actions[filename][line].append(action)

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

                if lineno in actions:
                    injection = indent
                    injection += 'import sleuth.inject; '
                    injection += ('sleuth.inject._hook("{0}", {1}, globals(), '
                                  'locals())\n'.format(filename, lineno))
                    modified_file += injection
                modified_file += line

        return modified_file

    def hook(self, filename, lineno, globals_, locals_):
        if self._enabled:
            for action in self._actions[filename][lineno]:
                action(globals_, locals_)


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


def _hook(filename, line, locals_, globals_):
    """Hook function to be injected into client code."""
    _injector.hook(filename, line, locals_, globals_)
