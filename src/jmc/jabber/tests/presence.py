# -*- coding: utf-8 -*-
##
## presence.py
## Login : <dax@happycoders.org>
## Started on  Thu Dec  6 08:19:59 2007 David Rousselie
## $Id$
##
## Copyright (C) 2007 David Rousselie
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

import unittest
import time

from pyxmpp.iq import Iq

from jcl.model.account import User, LegacyJID, Account
from jcl.tests import JCLTestCase

from jmc.jabber.component import MailComponent
from jmc.jabber.presence import MailAccountIQLastHandler

class MailAccountIQLastHandler_TestCase(JCLTestCase):
    def setUp(self):
        JCLTestCase.setUp(self, tables=[User, LegacyJID, Account])
        self.comp = MailComponent("jmc.test.com",
                                  "password",
                                  "localhost",
                                  "5347",
                                  None, None)
        self.handler = MailAccountIQLastHandler(self.comp)

    def test_handle(self):
        user1 = User(jid="user1@test.com")
        account11 = Account(user=user1,
                            name="account11",
                            jid="account11@jcl.test.com")
        account12 = Account(user=user1,
                            name="account12",
                            jid="account12@jcl.test.com")
        info_query = Iq(from_jid="user1@test.com",
                        to_jid="account11@jcl.test.com",
                        stanza_type="get")
        account11.lastcheck = int(time.time())
        time.sleep(1)
        result = self.handler.handle(info_query, None, account11)
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0].get_to(), "user1@test.com")
        self.assertEquals(result[0].get_from(), "account11@jcl.test.com")
        self.assertEquals(result[0].get_type(), "result")
        self.assertNotEquals(result[0].xmlnode.children, None)
        self.assertEquals(result[0].xmlnode.children.name, "query")
        self.assertEquals(int(result[0].xmlnode.children.prop("seconds")), 1)

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(MailAccountIQLastHandler_TestCase, 'test'))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
