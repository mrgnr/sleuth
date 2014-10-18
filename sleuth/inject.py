__all__ = ['breakAt', 'printAt', 'logAt', 'callAt', 'commentAt', 'injectAt']


def breakAt(filename, line, where='before'):
    pass


def printAt(filename, line, fmtStr, where='before'):
    pass


def logAt(filename, line, fmtStr, where='before'):
    pass


def callAt(filename, line, func, args=None, kwargs=None, where='before'):
    pass


def commentAt(filename, start, end=None):
    pass


def injectAt(filename, line, code, where='before'):
    pass
