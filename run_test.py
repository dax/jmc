##
## run_test.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Wed May 18 13:33:03 2005 David Rousselie
## $Id: run_test.py,v 1.2 2005/09/18 20:24:07 David Rousselie Exp $
## 
## Copyright (C) 2005 David Rousselie
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
sys.path.append("src")
reload(sys)
sys.setdefaultencoding('utf8')
del sys.setdefaultencoding

import tests
from tests.test_mailconnection import *
from tests.test_mailconnection_factory import *
from tests.test_component import *
from tests.test_storage import *
from tests.test_lang import *
from test import test_support
import logging
import jmc


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
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
    sqlitestorage_suite = unittest.makeSuite(SQLiteStorage_TestCase, \
                                             "test")
    lang_suite = unittest.makeSuite(Lang_TestCase, \
                                    "test")

    jmc_suite = unittest.TestSuite((mail_connection_suite, \
                                    pop3_connection_suite, \
                                    imap_connection_suite, \
                                    mc_factory_suite, \
 #                                   component_suite, \
 #                                   component2_suite, \
                                    storage_suite, \
                                    dbmstorage_suite, \
                                    sqlitestorage_suite, \
                                    lang_suite))
    #test_support.run_suite(mail_connection_suite)
    #test_support.run_suite(pop3_connection_suite)
    #test_support.run_suite(imap_connection_suite)
    #test_support.run_suite(mc_factory_suite)
    #test_support.run_suite(component_suite)
    #test_support.run_suite(component2_suite)
    #test_support.run_suite(storage_suite)
    #test_support.run_suite(sqlitestorage_suite)
    #test_support.run_suite(dbmstorage_suite)
    test_support.run_suite(jmc_suite)

coverage.stop()
coverage.analysis(jmc.email.mailconnection_factory)
coverage.analysis(jmc.email.mailconnection)
coverage.analysis(jmc.jabber.component)
coverage.analysis(jmc.jabber.x)
coverage.analysis(jmc.utils.lang)
coverage.report([jmc.email.mailconnection_factory, jmc.email.mailconnection, \
                 jmc.jabber.component, jmc.jabber.x, jmc.utils.lang])
