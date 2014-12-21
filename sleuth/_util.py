import sys
import types


def import_(module):
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


def set_trace(frame, debugger):
    if debugger.__name__ == 'pdb':
        debugger.Pdb().set_trace(frame)
    else:
        debugger.set_trace(frame)
