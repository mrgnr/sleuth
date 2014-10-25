"""
Sleuth: A debugging and diagnostic tool for Python.
------
"""

import sys
if sys.version_info[:2] < (3, 0):
    raise ImportError("Sleuth requires Python 3.")
del sys

__version__ = '0.2.0d'

from .__main__ import main
from .error import *
from .inject import *
from .sleuth import *
