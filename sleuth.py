import collections
import sys
import types

from functools import wraps
import logging


def junk():
    '''
    For testing purposes only.
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print('decorator start')
            result = func(*args, **kwargs)
            print('decorator end')
            return result
        return wrapper
    return decorator


def logCalls(func=None, *, enterFmtStr=None, exitFmtStr=None):
    '''
    A decorator that logs call information about a function. Logging is
    performed when the decorated function is entered as well as exited.  The
    total number of times that the function has been called and the time that
    each call takes is logged in addition to the name of the function.

    enterFmtStr : A formatted string to output when the decorated function is
        entered. The format() function is called on the string with the call
        number and the name of the function. If not specified, this argument
        is set to '[{}] Calling {}()'.

    enterFmtStr : A formatted string to output when the decorated function is
        exited. The format() function is called on the string with the call
        number, the name of the function, and the total time the function took
        to execute. If not specified, this argument is set to
        '[{}] Exiting {}()\t[{} seconds]'.
    '''

    if func is None:
        return partial(func, enterFmtStr=enterFmtStr, exitFmtStr=exitFmtStr)

    import time

    # The number of times the wrapped function has been called
    nCalls = 0

    if enterFmtStr is None:
        enterFmtStr = '[{}] Calling {}()'

    if exitFmtStr is None:
        exitFmtStr = '[{}] Exiting {}()\t[{} seconds]'

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal nCalls
        logger = logging.getLogger(func.__module__)

        logger.debug(enterFmtStr.format(nCalls, func.__name__))
        callNumber = nCalls
        nCalls = nCalls + 1
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.debug(exitFmtStr.format(callNumber, func.__name__,
                                       round(end-start, 4)))

        return result
    return wrapper


def breakOnEnter(func=None, *, debugger='pdb'):
    '''
    A decorator that causes debug mode to be entered when the decorated
    function is called.

    func : The function to be decorated.
    debugger : The debugger to use when debug mode is entered. This can be
        either the debugging module itself or a string containing the name of
        the debugging module. Currently, pdb and ipdb are supported.
    '''

    if func is None:
        return partial(breakOnEnter, debugger=debugger)

    debugger = _import(debugger)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return debugger.runcall(func, *args, **kwargs)
    return wrapper


def breakOnExit(func=None, *, debugger='pdb'):
    '''
    A decorator that causes debug mode to be entered when the decorated
    function exits.

    func : The function to be decorated.
    debugger : The debugger to use when debug mode is entered. This can be
        either the debugging module itself or a string containing the name of
        the debugging module. Currently, pdb and ipdb are supported.
    '''
    if func is None:
        return partial(breakOnExit, debugger=debugger)

    debugger = _import(debugger)

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        debug_frame = sys._getframe.f_back
        _set_trace(debug_frame, debugger)

        return result
    return wrapper


def breakOnResult(func=None, *, compare=None, debugger='pdb'):
    '''
    A decorator that causes debug mode to be entered when the decorated
    function returns a certain result.

    func : The function to be decorated.
    compare : A function to perform the comparison. When the decorated function
        returns, this function is called with the result. Debug mode is entered
        if the compare function returns True.
    debugger : The debugger to use when debug mode is entered. This can be
        either the debugging module itself or a string containing the name of
        the debugging module. Currently, pdb and ipdb are supported.
    '''

    if func is None:
        return partial(breakOnResult, compare=compare, debugger=debugger)

    debugger = _import(debugger)

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if compare(result):
            debug_frame = sys._getframe.f_back
            _set_trace(debug_frame, debugger)

        return result
    return wrapper


def breakOnException(func=None, *, exceptionList=Exception, debugger='pdb'):
    '''
    A decorator that causes debug mode to be entered when the decorated
    function throws a specified exception.

    func : The function to be decorated.
    exceptionList : A tuple of exceptions to break on.
    debugger : The debugger to use when debug mode is entered. This can be
        either the debugging module itself or a string containing the name of
        the debugging module. Currently, pdb and ipdb are supported.
    '''

    if func is None:
        return partial(breakOnException, exceptionList=exceptionList,
                       debugger=debugger)

    debugger = _import(debugger)

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptionList as e:
            debug_frame = sys._getframe.f_back
            _set_trace(debug_frame, debugger)
    return wrapper


def callOnEnter(func=None, *, callback=None):
    '''
    A decorator that calls a callback function before the decorated function
    is called.

    func : The function to be decorated.
    callback : The callback function to call. This function is called with the
        same arguments as the decorated function.
    '''

    if func is None:
        return partial(callOnEnter, callback=callback)

    @wraps(func)
    def wrapper(*args, **kwargs):
        callback(*args, **kwargs)  # TODO: add attribute for retval
        return func(*args, **kwargs)
    return wrapper


def callOnExit(func=None, *, callback=None):
    '''
    A decorator that calls a callback function after the decorated function is
    called.

    func : The function to be decorated.
    callback : The callback function to call. This function is called with the
        return value of the decorated function. The return value of the
        callback function is ultimately returned to the caller of the decorated
        function.
    '''

    if func is None:
        return partial(callOnExit, callback=callback)

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return callback(result)
    return wrapper


def callOnResult(func=None, *, compare=None, callback=None):
    '''
    A decorator that calls a callback function when the decorated function
    returns a certain result.

    func : The function to be decorated.
    compare : A function to perform the comparison. When the decorated function
        returns, this function is called with the result. The callback function
        is called if the compare function returns True.
    callback : The callback function to call. This function is called with the
        return value of the decorated function if the compare function returns
        True. If called, the return value of the callback function is
        ultimately returned to the caller of the decorated function.
    '''

    if func is None:
        return partial(callOnResult, compare=compare, callback=callback)

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if compare(result):
            callback(result)

        return result
    return wrapper


def callOnException(func=None, *, exceptionList=Exception, callback=None):
    '''
    A decorator that calls a callback function when the decorated function
    throws a specified exception.

    func : The function to be decorated.
    exceptionList : A tuple of exceptions on which to call the callback
        function.
    callback : The callback function to call. This function is called with the
        exception thrown by the decorated function. After the callback function
        returns, the exception is reraised if the return value of the callback
        function was False. Otherwise, the exception is caught and suppressed.
        By default, the exception is reraised if the callback function returns
        no value.
    '''

    if func is None:
        return partial(callOnException, exceptionList=exceptionList,
                       callback=callback)

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptionList as e:
            if not callback(e):
                raise e


def skip(func=None, *, returnValue=None):
    '''
    A decorator that causes the call to the decorated function to be skipped.

    func : The function to be decorated.
    returnValue : A value to return in place of the value that would normally
        be returned by the decorated function. This is None by default.
    '''

    if func is None:
        return partial(skip, returnValue=returnValue)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return returnValue
    return wrapper


def substitute(func=None, *, replacement=None):
    '''
    A decorator that substitutes calls to the decorated function with calls to
    a replacement funciton.

    func : The function to be decorated.
    replacement : A function to be substituted for the decorated function. The
        replacement function is called with the same arguments as would be
        passed to the decorated function.
    '''

    if func is None:
        return partial(substitute, replacement=replacement)

    @wraps
    def wrapper(func):
        return replacement(*args, **kwargs)
    return wrapper


class Sleuth:
    def parseConfig(self, configFile):
        import configparser
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(configFile)
        modules = list(config['MODULES'])

        for module in module:
            __import__(module)

    def set_env(self, filename):
        '''
        import __main__
        __main__.__dict__.clear()
        __main__.__dict__.update({'__name__': '__main__',
                                  '__file__': filename,})
                                  #'__builtins__': __builtins__})
        '''

        import __main__
        globals = __main__.__dict__
        locals = globals

        with open(filename) as f:
            code = f.read()
            exec(code, globals, locals)


def tap(func, dec, *args, **kwargs):
    '''
    import pdb
    pdb.set_trace()
    '''

    module = sys.modules[func.__module__]
    wrapped = dec(*args, **kwargs)(func)

    parent = _get_parent_scope(func, module)
    setattr(parent, func.__name__, wrapped)
    # TODO: is func.__name__ always correct?


def _get_parent_scope(func, module):
    path = None
    if hasattr(func, '__qualname__'):
        qualname = func.__qualname__
        attrs = qualname.split('.')
        path = [module]

        for attr in attrs:
            path.append(getattr(path[-1], attr))
    else:
        path = search(func, module, limit=100)

    if path is not None:
        return path[-2]
    else:
        raise ValueError('Function not found.')


def search(func, module, limit):

    def search_helper(goal, node, path, depth, limit, seen):
        # Cut off redundant searches
        if node in seen:
            return None

        # Cut off deep searches
        if limit is not None and depth > limit:
            return None

        # Keep track of searched nodes and search path
        seen.add(node)
        path.append(node)

        if node is goal:
            return path

        for attr in dir(node):
            try:
                child = getattr(node, attr)

                # Only search modules, classes, and functions
                if (isinstance(child, type) or
                        isinstance(child, types.ModuleType) or
                        isinstance(child, types.FunctionType)):

                    child_path = search_helper(goal, child, path, depth + 1,
                                               limit, seen)

                    if child_path is not None:
                        return child_path
            except AttributeError:
                # Ignore attribute errors
                pass

        # Solution path does not contain this node
        path.pop()
        return None

    for i in range(1, limit):
        path = search_helper(func, module, [], 0, i, set())

        if path is not None:
            return path

    return None


def run(filename):
    import __main__
    globals = __main__.__dict__
    locals = globals

    code = ''
    with open(filename) as f:
        code = f.read()

    exec(code, globals, locals)


def _import(module):
    if isinstance(module, types.ModuleType):
        return module
    elif isinstance(module, str):
        major, minor, *junk = sys.version_info
        if major >= 3 and minor >= 1:
            import importlib
            return importlib.import_module(module)
        else:
            return __import__(module)
    else:
        raise ImportError


def _set_trace(frame, debugger):
    if debugger.__name__ == 'pdb':
        debugger.Pdb().set_trace(frame)
    else:
        debugger.set_trace(frame)


if __name__ == '__main__':
    import config
    filename = sys.argv[1]

    run(filename)

    # sleuth = Sleuth()
    # sleuth.parseConfig('sleuth.cfg')
    # Sleuth().set_env(filename)
