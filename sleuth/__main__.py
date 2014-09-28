import argparse
import os
import sys

from . import __version__


def _parse_args():
    parser = argparse.ArgumentParser(prog='python -m {0}'.format(__package__),
                                     description='Sleuth: A debugging and '
                                     'diagnostic tool for Python 3.x')
    parser.add_argument('--version', '-v', action='version',
                        version='Sleuth {0}'.format(__version__))
    parser.add_argument('--config', '-c', metavar='SLEUTHCONFIG',
                        default='sleuthconfig.py',
                        help='A Sleuth configuration file')
    parser.add_argument('--preserve', '-p', action='store_true',
                        help='Preserve the execution environment between the '
                        'execution of the configuration file and the '
                        'execution of the Python file')
    parser.add_argument('pyfile', help='The Python script to run')
    parser.add_argument('progargs', metavar='arg', nargs='*',
                        help='An argument for the Python script')

    args = parser.parse_args()
    return args


def _run(configFile, pyfile, preserve=False):
    def cleanup():
        # Set the context for executing the Python file. This cleans up some of
        # the effects to __main__.__dict__ caused by Sleuth.
        import __main__
        exec_context = {'__name__': '__main__', '__file__': pyfile,
                        '__builtins__': __builtins__}
        __main__.__dict__.clear()
        __main__.__dict__.update(exec_context)
        g = l = __main__.__dict__
        return g, l

    #g = globals()
    #l = locals()

    # Execute the config file
    with open(configFile, 'rb') as f:
        code = compile(f.read(), configFile, 'exec')
    g, l = cleanup()
    #g, l = (g, l) if preserve else cleanup()
    exec(code, g, l)
    #import sleuthconfig

    # Execute the Python file
    with open(pyfile, 'rb') as f:
        code = compile(f.read(), pyfile, 'exec')
    g, l = (g, l) if preserve else cleanup()
    exec(code, g, l)

    '''
    if preserve:
        exec(code)
    else:
        globals, locals = cleanup()
        exec(code, globals, locals)
    '''


def main():
    # TODO
    # Modify sys.argv to hide sleuth params
    # Set sys.path to change cwd
    # Load sleuth config file

    args = _parse_args()
    pyfile = args.pyfile
    config = args.config
    sys.argv[:] = [pyfile] + args.progargs

    if not os.path.exists(pyfile):
        raise SystemExit('Error: {0} does not exist.'.format(pyfile))

    _run(config, pyfile, args.preserve)


if __name__ == '__main__':
    main()
