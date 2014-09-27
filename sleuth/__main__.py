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
    parser.add_argument('pyfile', help='The Python script to run')
    parser.add_argument('progargs', metavar='arg', nargs='*',
                        help='An argument for the Python script')
    args = parser.parse_args()

    print(args.pyfile)
    print(args.progargs)

    return args


def _run(pyfile):
    with open(pyfile, 'rb') as f:
        code = compile(f.read(), pyfile, 'exec')

    # Set the context for executing the Python file. This cleans up some of
    # the effects to __main__.__dict__ caused by Sleuth.
    import __main__
    exec_context = {'__name__': '__main__', '__file__': pyfile,
                    '__builtins__': __builtins__}
    __main__.__dict__.clear()
    __main__.__dict__.update(exec_context)
    globals = locals = __main__.__dict__
    exec(code, globals, locals)


def main():
    # TODO
    # Modify sys.argv to hide sleuth params
    # Set sys.path to change cwd
    # Load sleuth config file

    args = _parse_args()
    pyfile = args.pyfile
    sys.argv[:] = [pyfile] + args.progargs

    if not os.path.exists(pyfile):
        raise SystemExit('Error: {0} does not exist.'.format(pyfile))

    _run(pyfile)


if __name__ == '__main__':
    main()
