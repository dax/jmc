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
import logging
import unittest
from test import test_support

import sys
sys.path.append("src")
reload(sys)
sys.setdefaultencoding('utf8')
del sys.setdefaultencoding

import tests
from tests.jmc.jabber.test_component import *
from tests.jmc.model.test_account import *
from tests.jmc.test_lang import *

import jmc
import jmc.jabber
import jmc.jabber.component

def test_suite():
    mail_account_suite = unittest.makeSuite(MailAccount_TestCase, "test")
    imap_account_suite = unittest.makeSuite(IMAPAccount_TestCase, "test")
    pop3_account_suite = unittest.makeSuite(POP3Account_TestCase, "test")
    lang_suite = unittest.makeSuite(Lang_TestCase, "test")
    mail_component_suite = unittest.makeSuite(MailComponent_TestCase, "test")
    
#    jmc_suite = unittest.TestSuite((mail_component_suite))
#    jmc_suite = unittest.TestSuite()
#    jmc_suite.addTest(MailAccount_TestCase('test_format_message_summary_partial_encoded'))
    jmc_suite = unittest.TestSuite((lang_suite, \
                                    mail_account_suite, \
                                    imap_account_suite, \
                                    pop3_account_suite, \
                                    mail_component_suite))
    return jmc_suite

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    
    coverage.erase()
    coverage.start()

    unittest.main()    

    coverage.stop()
    coverage.analysis(jmc.jabber.component)
    coverage.analysis(jmc.lang)
    coverage.analysis(jmc.model.account)

    coverage.report([jmc.jabber.component, \
                     jmc.lang, \
                     jmc.model.account])
