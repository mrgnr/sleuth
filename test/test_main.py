import importlib
import sys
import unittest

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
        self._path = sys.path[0]
        self._argv = sys.argv
        sys.argv[:] = [sleuth.__main__.__file__, fakescript.__file__]

    def tearDown(self):
        sys.path[0] = self._path
        sys.argv[:] = self._argv
        fakemodule = None

    def test_main(self):
        sleuth.main()
        self.assertTrue(fakemodule.doNothing_callback.called)
        self.assertTrue(fakemodule.returnValue_callback.called)
