from functools import partial
from functools import wraps


def doNothing(*args, **kwargs):
    '''
    A test function that takes any arguments and does nothing.
    '''

    pass


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
