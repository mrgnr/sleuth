from functools import partial
from functools import wraps

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock


def doNothing(*args, **kwargs):
    '''
    A test function that takes any arguments and does nothing.
    '''

    doNothing.called = True
doNothing.called = False


def returnValue(return_value):
    '''
    A test function that returns a value.
    '''

    return return_value


def raiseException(exception=None):
    '''
    A test function that raises an exception.
    '''

    if exception is not None:
        raise exception
    else:
        raise Exception


def decorator(func=None, **kwargs):
    '''
    A Sleuth-style decorator for testing purposes.
    '''

    if func is None:
        return partial(decorator, **kwargs)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def doNothing_callback():
    doNothing_callback.called = True
doNothing_callback.called = False


def returnValue_callback(result):
    returnValue_callback.called = True
returnValue_callback.called = False
