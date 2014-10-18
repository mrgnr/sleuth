# Sleuth
[![Build Status](https://travis-ci.org/emrob/sleuth.svg?branch=master)](https://travis-ci.org/emrob/sleuth)
[![Coverage Status](https://img.shields.io/coveralls/emrob/sleuth.svg)](https://coveralls.io/r/emrob/sleuth)

The principle behind Sleuth is simple: You shouldn't have to modify your code
to debug it. Sometimes it's just easier to insert `print()` statements than it
is to fire up a debugger, but then your code becomes littered with debugging
statements that must be removed later. With Sleuth, all of your debugging code
goes into a Sleuth config file, freeing you of cleaning up the mess resulting
from a long debugging session.


## How does it work?
Right now, Sleuth is mostly a collection of function wrappers (also known as
decorators in Python-speak) that allow you to perform debugging operations when
a function is called. All of your debugging code goes into a file called
`sleuthconfig.py`, and the Sleuth wrappers are applied to your functions
dynamically at runtime with the `tap()` function. For example, if you want to
log calls to `subprocess.check_call()` to see when your program is calling
subprocesses, you might put the following in your `sleuthconfig.py`:

```python
import logging
import subprocess
from sleuth import tap, logCalls

tap(subprocess.check_call, logCalls)
logging.basicConfig(level=logging.DEBUG)
```

Then run your program with Sleuth:

```
$ python -m sleuth myProgram.py
```

Whenever `subprocess.check_call()` is called or exits, you get logging output
like this:

```
DEBUG:subprocess:[0] Calling check_call()
DEBUG:subprocess:[0] Exiting check_call()	[0.0038 seconds]
```

## Cool, what else can I do?
- Logging
    - `logCalls()` - Write to the log when a wrapped function is called or exits
    - `logOnException()` - Write to the log when a wrapped function raises an exception
- Break into debug mode
    - `breakOnEnter()` - Break into debug mode when a wrapped function is entered
    - `breakOnException()` - Break into debug mode when a wrapped function raises an exception
    - `breakOnExit()` - Break into debug mode immediately after a wrapped function exits
    - `breakOnResult()` - Break into debug mode when a wrapped function returns a certain result
- Call other functions
    - `callOnEnter()` - Call a function before a wrapped function is entered
    - `callOnException()` - Call a function when a wrapped function raises an exception
    - `callOnExit()` - Call a function immediately after a wrapped function exits
    - `callOnResult()` - Call a function when a wrapped function returns a certain result
- Skip or substitute a function call
    - `skip()` - Skip any calls to the wrapped function
    - `substitute()` - Substitute calls to the wrapped function with a different function


## Sleuth is flexible and extensible

Sleuth is designed to require minimal effort to get up and running, but many
functions take optional parameters to allow for full customization.
`logCalls()` and `logOnException()` come with sane defaults out of the box,
but you can customize things like the logging output and logging level. And if
the optional parameters don't give you enough flexibility, you can use
`callOnEnter()` and `callOnExit()` to implement custom functionality. Since
Sleuth wrappers are just normal Python decorators, you can even write your own
function wrappers that work with the `tap()` function.


## Sleuth plays nicely with others

Sleuth uses the standard `logging` module, so there's no extra work to do if
you've already configured logging for your project. Simply `tap` your functions
with `logCalls()` or `logOnException()` and Sleuth and `logging` will do the
rest.  For debugging, the `breakOn...()` wrappers have baked-in support for
Python's standard `pdb` module and IPython's `ipdb` module. You can also use
your own debugging module with Sleuth as long as it supports a similar
interface.


## In development!

Sleuth is still very much in development, but you can find stable versions in
the releases. Please check back in the near future for updates :)
