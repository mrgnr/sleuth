import sys

import fakemodule
from fakemodule import returnValue


if __name__ == '__main__':
    for arg in sys.argv:
        print(arg)

    fakemodule.doNothing()
    returnValue(1)
