import os.path
import sys
from collections import defaultdict


__all__ = ['breakAt', 'printAt', 'logAt', 'callAt', 'commentAt', 'injectAt']


def breakAt(filename, line, indent=None):
    stmt = 'import pdb; pdb.set_trace()'
    _injector.add(filename, line, stmt)


def printAt(filename, line, fmtStr, indent=None):
    stmt = 'print("{0}".format(**locals()))'.format(fmtStr)
    _injector.add(filename, line, stmt)


def logAt(filename, line, fmtStr, indent=None):
    pass


def callAt(filename, line, func, args=None, kwargs=None, indent=None):
    pass


def commentAt(filename, start, end=None, indent=None):
    pass


def injectAt(filename, line, code, indent=None):
    _injector.add(filename, line, code)


class _Injector:
    def __init__(self):
        # self._code[filename][line] -> [statement_1, ..., statement_n]
        self._code = defaultdict(lambda: defaultdict(list))

        self._enabled = False

    def add(self, filename, line, stmt):
        if not stmt.endswith('\n'):
            stmt += '\n'
        self._code[filename][line].append(stmt)

    def inject(self, filename):
        modified_file = ''
        statements = self._code[filename]
        with open(filename, 'rt') as f:
            for lineno, line in enumerate(f, start=1):
                indent_len = len(line) - len(line.lstrip())
                indent = line[0: indent_len]

                if lineno in statements:
                    lines = [indent + statement for statement in
                             statements[lineno]]
                    modified_file += ''.join(lines)
                modified_file += line

        return modified_file

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False


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
