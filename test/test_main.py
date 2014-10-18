import importlib
import os
import sys
import unittest
from io import StringIO

try:
    from importlib import reload
except ImportError:
    from imp import reload

import sleuth

import fakemodule
import fakescript


class TestSleuthMain(unittest.TestCase):
    def setUp(self):
        reload(fakemodule)
        reload(fakescript)
        self._path = sys.path[0]
        self._argv = sys.argv
        self._stdout = sys.stdout
        sys.argv[:] = [sleuth.__main__.__file__, fakescript.__file__]
        sys.stdout = StringIO()

    def tearDown(self):
        sys.path[0] = self._path
        sys.argv[:] = self._argv
        sys.stdout = self._stdout
        fakemodule = None
        fakescript = None

    def test_main(self):
        # Test: Settings from the config file are applied to the script
        sleuth.main()
        self.assertTrue(fakemodule.doNothing_callback.called)
        self.assertTrue(fakemodule.returnValue_callback.called)

    def test_script_args(self):
        # Test: Arbitrary commandline args are passed to the script
        scriptArgs = ['--arg', 'blah', '-v']
        sys.argv[:] = sys.argv + scriptArgs
        sleuth.main()
        passedArgs = sys.stdout.getvalue().strip().split('\n')
        self.assertEqual(passedArgs, [fakescript.__file__] + scriptArgs)

    def test_syspath(self):
        # Test: sys.path[0] is set to the directory where the script lives
        sleuth.main()
        scriptDir = os.path.dirname(os.path.realpath(fakescript.__file__))
        self.assertEqual(sys.path[0], scriptDir)
