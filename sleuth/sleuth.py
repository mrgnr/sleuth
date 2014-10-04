import argparse
import logging
import sys
import types

from functools import wraps
from functools import partial

from error import SleuthError, SleuthNotFoundError


__all__ = ['breakOnEnter', 'breakOnException', 'breakOnExit', 'breakOnResult',
           'callOnEnter', 'callOnException', 'callOnExit', 'callOnResult',
           'logCalls', 'logOnException', 'skip', 'substitute', 'tap']


def logCalls(func=None, *, enterFmtStr=None, exitFmtStr=None,
             level=logging.DEBUG, logName=None, timerFunc=None):
    '''
    A decorator that logs call information about a function. Logging is
    performed when the decorated function is entered as well as exited.  The
    total number of times that the function has been called and the time that
    each call takes is logged in addition to the name of the function.

    enterFmtStr : A formatted string to output when the decorated function is
        entered. The format() function is called on the string with locals().
        If not specified, this argument is set to
        '[{callNumber}] Calling {funcName}()'.

    exitFmtStr : A formatted string to output when the decorated function is
        exited. The format() function is called on the string with locals(). If
        not specified, this argument is set to
        '[{callNumber}] Exiting {funcName}()\t[{callTime} seconds]'.

    level : The logging level to use for logging calls. This must be one of the
        logging level constants defined in the logging module.

    logName : The name of the log which is written to by logging calls. If not
        given, the name of the module in which the decorated function is
        defined is used, i.e. func.__module__.

    timerFunc : The function to use for timing the duration of function calls.
        This function is called before and after the decorated function is
        called. The difference between the two return values of the timing
        function is used as the duration of the function call. If not given,
        time.time is used.
    '''

    if func is None:
        return partial(logCalls, enterFmtStr=enterFmtStr,
                       exitFmtStr=exitFmtStr, level=level, logName=logName,
                       timerFunc=timerFunc)

    # The number of times the wrapped function has been called
    nCalls = 0

    if enterFmtStr is None:
        enterFmtStr = '[{callNumber}] Calling {funcName}()'

    if exitFmtStr is None:
        exitFmtStr = ('[{callNumber}] Exiting {funcName}()\t[{callTime} '
                      'seconds]')

    if logName is None:
        logName = func.__module__

    if timerFunc is None:
        import time
        timerFunc = time.time

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal nCalls
        funcName = func.__name__

        callNumber = nCalls
        logger = logging.getLogger(logName)
        logMsg = enterFmtStr.format(**locals())
        logger.log(level, logMsg)
        nCalls = nCalls + 1

        start = timerFunc()
        result = func(*args, **kwargs)
        end = timerFunc()

        callTime = round(end - start, 4)  # TODO: use string formatting instead
        logMsg = exitFmtStr.format(**locals())
        logger.log(level, logMsg)

        return result
    return wrapper


def logOnException(func=None, *, exceptionList=Exception, suppress=False,
                   fmtStr=None, level=logging.DEBUG, logName=None):
    '''
    A decorator that logs information when an exception is thrown by the
    decorated function.

    func : The function to be decorated.
    exceptionList : An exception or tuple of exceptions to be logged.
    suppress : A boolean indicating whether a caught exception should be
        suppressed. If False, the exception is reraised. This only applies to
        exceptions specified in exceptionList.
    fmtStr : A formatted string to output when the decorated function raises a
        specified exception.
    level : The logging level to use for logging calls. This must be one of the
        logging level constants defined in the logging module.
    logName : The name of the log which is written to by logging calls. If not
        given, the name of the module in which the decorated function is
        defined is used, i.e. func.__module__.
    '''

    if func is None:
        return partial(logOnException, exceptionList=exceptionList,
                       suppress=suppress, fmtStr=fmtStr, level=level,
                       logName=logName)

    if fmtStr is None:
        fmtStr = ("Exception raised in {funcName}(): '{exceptionType}: "
                  "{exception}'")

    if logName is None:
        logName = func.__module__

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptionList as exception:
            exceptionType = exception.__class__.__name__
            funcName = func.__name__
            logger = logging.getLogger(logName)
            logMsg = fmtStr.format(**locals())
            logger.log(level, logMsg)

            if not suppress:
                raise
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

        debug_frame = sys._getframe().f_back
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
            debug_frame = sys._getframe().f_back
            _set_trace(debug_frame, debugger)

        return result
    return wrapper


def breakOnException(func=None, *, exceptionList=Exception, debugger='pdb'):
    '''
    A decorator that causes debug mode to be entered when the decorated
    function throws a specified exception.

    func : The function to be decorated.
    exceptionList : An exception or tuple of exceptions to break on.
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
            debug_frame = sys._getframe().f_back
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
                raise
    return wrapper


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

    @wraps(func)
    def wrapper(*args, **kwargs):
        return replacement(*args, **kwargs)
    return wrapper


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


def _get_parent_scope(func, module):
    '''
    Obtain the parent scope of a function given the module in which it is
    defined.
    '''

    path = _search(func, module, limit=100)

    if path is not None:
        return path[-2]
    else:
        raise SleuthNotFoundError("The function '{0}' could not be found "
                                  "within module '{1}'."
                                  .format(func.__name__, module.__name__))


def _search(func, module, limit):
    '''
    Get the path of a function from the starting with the module in which it is
    defined; that is, the sequence of enclosing modules and classes that must
    be followed to reach the function from its module.

    Returns : A list of module and class objects which forms a path from the
        module in which a function is defined to the function itself. The
        first item in the list is the module in which the function is defined
        and the last item is the function itself. Each item in the list is an
        attribute of the previous item.
    '''

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


def tap(func, dec, *args, **kwargs):
    try:
        module = sys.modules[func.__module__]
        wrapped = dec(*args, **kwargs)(func)
    except (KeyError, AttributeError):
        raise SleuthNotFoundError("The module containing function '{0}' could "
                                  "not be found.".format(func.__name__))

    parent = _get_parent_scope(func, module)
    setattr(parent, func.__name__, wrapped)
    # TODO: is func.__name__ always correct?
