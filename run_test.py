##
## test.py
## Login : <adro8400@claralinux>
## Started on  Wed May 18 13:33:03 2005 adro8400
## $Id: run_test.py,v 1.2 2005/09/18 20:24:07 dax Exp $
## 
## Copyright (C) 2005 adro8400
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
import unittest
import sys
import tests
from tests.test_mailconnection import *
from tests.test_mailconnection_factory import *
from tests.test_component import *
from tests.test_storage import *
from test import test_support
import jabber

if __name__ == '__main__':
    mail_connection_suite = unittest.makeSuite(MailConnection_TestCase, \
                                               "test")
    pop3_connection_suite = unittest.makeSuite(POP3Connection_TestCase, \
                                               "test")
    imap_connection_suite = unittest.makeSuite(IMAPConnection_TestCase, \
                                               "test")
    mc_factory_suite = unittest.makeSuite(MailConnectionFactory_TestCase, \
                                          "test")
    component_suite = unittest.makeSuite(MailComponent_TestCase_Basic, \
                                          "test")
    component2_suite = unittest.makeSuite(MailComponent_TestCase_NoReg, \
                                          "test")
    storage_suite = unittest.makeSuite(Storage_TestCase, \
                                          "test")
    dbmstorage_suite = unittest.makeSuite(DBMStorage_TestCase, \
                                          "test")

    jmc_suite = unittest.TestSuite((mail_connection_suite, \
                                    pop3_connection_suite, \
                                    imap_connection_suite, \
                                    mc_factory_suite, \
                                    component_suite, \
                                    component2_suite, \
                                    storage_suite, \
                                    dbmstorage_suite))
    test_support.run_suite(component_suite)

# coverage.stop()
# coverage.analysis(jabber.mailconnection_factory)
# coverage.analysis(jabber.mailconnection)
# coverage.analysis(jabber.component)
# coverage.analysis(jabber.x)
# coverage.report([jabber.mailconnection_factory, jabber.mailconnection, \
#                  jabber.component, jabber.x])
