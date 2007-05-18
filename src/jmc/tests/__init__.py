"""JMC test module"""
__revision__ = ""

import unittest

from jmc.tests import lang, runner
from jmc.jabber import tests as jabber
from jmc.model import tests as model

def suite():
    suite = unittest.TestSuite()
    suite.addTest(lang.suite())
    suite.addTest(runner.suite())
    suite.addTest(jabber.suite())
    suite.addTest(model.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
