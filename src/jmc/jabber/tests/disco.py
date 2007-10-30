##
## disco.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Sun Jul  8 20:59:32 2007 David Rousselie
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

from jmc.jabber.disco import MailRootDiscoGetInfoHandler, \
    IMAPAccountDiscoGetInfoHandler
from jmc.lang import Lang

class MockDiscoIndentity(object):
    def __init__(self):
        self.category = ""
        self.type = ""

class MockAccountManager(object):
    def __init__(self):
        self.has_multiple_account_type = False

class MockComponent(object):
    def __init__(self):
        self.name = ""
        self.disco_identity = MockDiscoIndentity()
        self.account_manager = MockAccountManager()

class MailRootDiscoGetInfoHandler_TestCase(unittest.TestCase):
    def test_root_disco_get_info(self):
        component = MockComponent()
        component.name = "Mock component"
        component.disco_identity.category = "gateway"
        component.disco_identity.type = "smtp"
        component.account_manager.has_multiple_account_type = True
        handler = MailRootDiscoGetInfoHandler(component)
        # stanza, lang_class, node, disco_obj, data
        disco_infos = handler.handle(None, None, None, None, None)
        self.assertTrue(disco_infos[0].has_feature("jabber:iq:gateway"))
        self.assertTrue(disco_infos[0].has_feature("http://jabber.org/protocol/disco#info"))
        self.assertTrue(disco_infos[0].has_feature("http://jabber.org/protocol/disco#items"))
        self.assertTrue(disco_infos[0].has_feature("http://jabber.org/protocol/commands"))
        self.assertEquals(len(disco_infos[0].get_identities()), 2)
        self.assertTrue(disco_infos[0].identity_is("gateway", "smtp"))
        self.assertTrue(disco_infos[0].identity_is("headline", "newmail"))

class IMAPAccountDiscoGetInfoHandler_TestCase(unittest.TestCase):
    def test_handle_not_imap(self):
        component = MockComponent()
        component.name = "Mock component"
        component.disco_identity.category = "gateway"
        component.disco_identity.type = "smtp"
        component.account_manager.has_multiple_account_type = True
        handler = IMAPAccountDiscoGetInfoHandler(component)
        # stanza, lang_class, node, disco_obj, data
        disco_infos = handler.handle(None, Lang.en, "account@jmc.test.com/POP3",
                                     None, None)
        self.assertTrue(disco_infos[0].has_feature("jabber:iq:register"))
        self.assertTrue(disco_infos[0].has_feature("http://jabber.org/protocol/commands"))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MailRootDiscoGetInfoHandler_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(IMAPAccountDiscoGetInfoHandler_TestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
