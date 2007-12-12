"""JMC test module"""
__revision__ = ""

import unittest

from jmc.tests import lang, runner
from jmc.jabber import tests as jabber
from jmc.model import tests as model

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(lang.suite())
    test_suite.addTest(runner.suite())
    test_suite.addTest(jabber.suite())
    test_suite.addTest(model.suite())
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
