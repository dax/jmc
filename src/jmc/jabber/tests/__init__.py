"""JMC test module"""
__revision__ = ""

import unittest

from jmc.jabber.tests import component, disco, command, message

def suite():
    suite = unittest.TestSuite()
    suite.addTest(component.suite())
    suite.addTest(disco.suite())
    suite.addTest(command.suite())
    suite.addTest(message.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
