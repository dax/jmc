# -*- coding: utf-8 -*-
##
## run_tests.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Wed Aug  9 21:37:35 2006 David Rousselie
## $Id$
##
## Copyright (C) 2006 David Rousselie
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##

import coverage
coverage.erase()
coverage.start()

import logging
import unittest
from test import test_support

import sys
sys.path.append("src")
reload(sys)
sys.setdefaultencoding('utf8')
del sys.setdefaultencoding

import jmc
import jmc.jabber
import jmc.jabber.component

import jmc.tests

def suite():
    return jmc.tests.suite()

if __name__ == '__main__':
    class MyTestProgram(unittest.TestProgram):
        def runTests(self):
            """run tests but do not exit after"""
	    self.testRunner = unittest.TextTestRunner(verbosity=self.verbosity)
            self.testRunner.run(self.test)

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.CRITICAL)

    MyTestProgram(defaultTest='suite')

coverage.report(["src/jmc/__init__.py",
                 "src/jmc/lang.py",
                 "src/jmc/runner.py",
                 "src/jmc/jabber/__init__.py",
                 "src/jmc/jabber/command.py",
                 "src/jmc/jabber/component.py",
                 "src/jmc/jabber/disco.py",
                 "src/jmc/jabber/message.py",
                 "src/jmc/jabber/presence.py",
                 "src/jmc/jabber/presence.py",
                 "src/jmc/model/__init__.py",
                 "src/jmc/model/account.py"])
