import argparse
import os
import sys

from . import __version__
from .error import SleuthError, SleuthNotFoundError


def _parse_args():
    parser = argparse.ArgumentParser(prog='python -m {0}'.format(__package__),
                                     description='Sleuth: A debugging and '
                                     'diagnostic tool for Python 3.x')
    parser.add_argument('--version', '-v', action='version',
                        version='Sleuth {0}'.format(__version__))
    parser.add_argument('--config', '-c', metavar='SLEUTHCONFIG',
                        help='A Sleuth configuration file')
    parser.add_argument('--preserve', '-p', action='store_true',
                        help='Preserve the execution environment between the '
                        'execution of the configuration file and the '
                        'execution of the Python file')
    parser.add_argument('script', help='The Python script to run')
    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help='Arguments for the Python script')

    args = parser.parse_args()
    return args


def _find_config():
    configFile = 'sleuthconfig.py'
    for path in sys.path:
        configPath = os.path.join(path, configFile)
        if os.path.isfile(configPath):
            return configPath

    raise SleuthNotFoundError('{0} could not be found.'.format(configFile))


def _run(configFile, pyfile, preserve=False):
    def cleanup():
        # Set the context for executing the Python file. This cleans up some of
        # the effects to __main__.__dict__ caused by Sleuth.
        import __main__
        exec_context = {'__name__': '__main__', '__file__': pyfile,
                        '__builtins__': __builtins__}
        __main__.__dict__.clear()
        __main__.__dict__.update(exec_context)
        globals_ = locals_ = __main__.__dict__
        return globals_, locals_

    from sleuth.inject import Injector
    with Injector() as inj:
        # Execute the config file
        with open(configFile, 'rb') as f:
            code = compile(f.read(), configFile, 'exec')
        globals_, locals_ = cleanup()
        exec(code, globals_, locals_)

        # Execute the Python file
        modified_code = inj.inject_hooks(pyfile)
        code = compile(modified_code, pyfile, 'exec')
        globals_, locals_ = (globals_, locals_) if preserve else cleanup()
        exec(code, globals_, locals_)


def main():
    args = _parse_args()
    pyfile = args.script
    sys.argv[:] = [pyfile] + args.args
    sys.path[0] = os.path.dirname(os.path.realpath(pyfile))
    config = args.config if args.config else _find_config()

    if not os.path.exists(pyfile):
        raise SleuthNotFoundError('{0} could not be found.'.format(pyfile))

    _run(config, pyfile, args.preserve)


if __name__ == '__main__':
    main()
