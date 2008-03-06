##
## command.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Tue Oct 23 18:53:28 2007 David Rousselie
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
import tempfile
from ConfigParser import ConfigParser
import os
import sys
import logging

from pyxmpp.iq import Iq
from pyxmpp.jabber.dataforms import Field

import jcl.tests
from jcl.tests import JCLTestCase
from jcl.jabber.feeder import Feeder
from jcl.model.account import User, Account, PresenceAccount
from jcl.jabber.tests.command import JCLCommandManagerTestCase
import jcl.jabber.command as command

from jmc.model.account import POP3Account, IMAPAccount, SMTPAccount, \
    MailAccount
from jmc.jabber.component import MailComponent
from jmc.lang import Lang
from jmc.jabber.tests.component import MockIMAPAccount
from jmc.jabber.command import MailCommandManager

class MailCommandManagerTestCase(JCLCommandManagerTestCase):
    def setUp(self, tables=[]):
        tables += [POP3Account, IMAPAccount, SMTPAccount, MailAccount,
                   MockIMAPAccount, User, Account, PresenceAccount]
        JCLTestCase.setUp(self, tables=tables)
        self.config_file = tempfile.mktemp(".conf", "jmctest", jcl.tests.DB_DIR)
        self.config = ConfigParser()
        self.config.read(self.config_file)
        self.comp = MailComponent("jmc.test.com",
                                  "password",
                                  "localhost",
                                  "5347",
                                  self.config,
                                  self.config_file)
        self.comp.set_admins(["admin@test.com"])
        self.command_manager = MailCommandManager(self.comp,
                                                  self.comp.account_manager)
        self.comp.account_manager.account_classes = (POP3Account, IMAPAccount,
                                                     SMTPAccount, MockIMAPAccount)
        self.user1 = User(jid="test1@test.com")
        self.account11 = MockIMAPAccount(user=self.user1,
                                         name="account11",
                                         jid="account11@" + unicode(self.comp.jid))
        self.account12 = MockIMAPAccount(user=self.user1,
                                         name="account12",
                                         jid="account12@" + unicode(self.comp.jid))
        self.user2 = User(jid="test2@test.com")
        self.account21 = MockIMAPAccount(user=self.user2,
                                         name="account21",
                                         jid="account21@" + unicode(self.comp.jid))
        self.account22 = MockIMAPAccount(user=self.user2,
                                         name="account11",
                                         jid="account11@" + unicode(self.comp.jid))
        self.user3 = User(jid="test3@test.com")
        self.account31 = MockIMAPAccount(user=self.user3,
                                         name="account31",
                                         jid="account31@" + unicode(self.comp.jid))
        self.account32 = MockIMAPAccount(user=self.user3,
                                         name="account32",
                                         jid="account32@" + unicode(self.comp.jid))
        self.info_query = Iq(stanza_type="set",
                             from_jid="admin@test.com",
                             to_jid=self.comp.jid)
        self.command_node = self.info_query.set_new_content(command.COMMAND_NS,
                                                            "command")
        class MockFeederHandler(Feeder):
            def __init__(self, component):
                Feeder.__init__(self, component)
                self.checked_accounts = []

            def feed(self, _account):
                self.checked_accounts.append(_account)
                assert(_account.lastcheck == (_account.interval - 1))
                return []

        self.comp.handler.feeder = MockFeederHandler(self.comp)

    def tearDown(self):
        JCLTestCase.tearDown(self)
        if os.path.exists(self.config_file):
            os.unlink(self.config_file)

class MailCommandManagerForceCheckCommand_TestCase(MailCommandManagerTestCase):
    """
    Test 'force-check' ad-hoc command
    """

    def setUp(self, tables=[]):
        """
        Prepare data
        """
        MailCommandManagerTestCase.setUp(self, tables)
        self.command_node.setProp("node", "jmc#force-check")

    def test_execute_force_check(self):
        self.info_query.set_from("test1@test.com")
        self.info_query.set_to("account11@" + unicode(self.comp.jid))
        result = self.command_manager.apply_command_action(\
            self.info_query,
            "jmc#force-check",
            "execute")
        result_iq = result[0].xmlnode
        result_iq.setNs(None)
        self.assertTrue(jcl.tests.is_xml_equal(\
                u"<iq from='account11@" + unicode(self.comp.jid)
                + "' to='test1@test.com' type='result'>"
                + "<command xmlns='http://jabber.org/protocol/commands' "
                + "status='completed'>"
                + "</command></iq>",
                result_iq, True, test_sibling=False))
        feeder = self.comp.handler.feeder
        self.assertEquals(len(feeder.checked_accounts), 1)
        self.assertEquals(feeder.checked_accounts[0], self.account11)

    def test_execute_force_check_root_node(self):
        self.info_query.set_from("test1@test.com")
        result = self.command_manager.apply_command_action(\
            self.info_query,
            "jmc#force-check",
            "execute")
        result_iq = result[0].xmlnode
        result_iq.setNs(None)
        self.assertTrue(jcl.tests.is_xml_equal(\
                u"<iq from='jmc.test.com' to='test1@test.com' type='result'>"
                + "<command xmlns='http://jabber.org/protocol/commands'"
                + "status='executing'>"
                + "<actions execute='complete'><complete/></actions>"
                + "<x xmlns='jabber:x:data' type='form'>"
                + "<title>" + Lang.en.command_force_check + "</title>"
                + "<instructions>" + Lang.en.command_force_check_1_description
                + "</instructions>"
                + "<field var='account_names' type='list-multi' label='"
                + Lang.en.field_accounts + "'>"
                + "<option label=\"account11 (IMAP)\">"
                + "<value>account11/test1@test.com</value></option>"
                + "<option label=\"account12 (IMAP)\">"
                + "<value>account12/test1@test.com</value></option>"
                + "<option label=\"account11 (MockIMAP)\">"
                + "<value>account11/test1@test.com</value></option>"
                + "<option label=\"account12 (MockIMAP)\">"
                + "<value>account12/test1@test.com</value></option>"
                + "</field></x></command></iq>",
                result_iq, True))
        session_id = result_iq.children.prop("sessionid")
        self.assertNotEquals(session_id, None)
        context_session = self.command_manager.sessions[session_id][1]
        self.assertEquals(context_session["user_jids"],
                          ["test1@test.com"])

        # Second step
        info_query = self.prepare_submit(\
            node="jmc#force-check",
            session_id=session_id,
            from_jid="test1@test.com",
            to_jid=unicode(self.comp.jid),
            fields=[Field(field_type="list-multi",
                          name="account_names",
                          values=["account11/test1@test.com",
                                  "account12/test1@test.com"])],
            action="complete")
        result = self.command_manager.apply_command_action(\
            info_query,
            "jmc#force-check",
            "execute")
        result_iq = result[0].xmlnode
        result_iq.setNs(None)
        self.assertTrue(jcl.tests.is_xml_equal(\
                u"<iq from='" + unicode(self.comp.jid)
                + "' to='test1@test.com' type='result'>"
                + "<command xmlns='http://jabber.org/protocol/commands' "
                + "status='completed'>"
                + "</command></iq>",
                result_iq, True, test_sibling=False))
        self.assertEquals(context_session["account_names"],
                          ["account11/test1@test.com",
                           "account12/test1@test.com"])
        feeder = self.comp.handler.feeder
        self.assertEquals(len(feeder.checked_accounts), 2)
        self.assertEquals(feeder.checked_accounts[0], self.account11)
        self.assertEquals(feeder.checked_accounts[1], self.account12)

class MailCommandManagerGetEmailCommand_TestCase(MailCommandManagerTestCase):
    """
    Test 'get-email' ad-hoc command
    """

    def setUp(self, tables=[]):
        """
        Prepare data
        """
        MailCommandManagerTestCase.setUp(self, tables)
        self.command_node.setProp("node", "jmc#get-email")
        def get_email(email_index):
            """
            Mock method for IMAPAccount.get_email
            """
            return ("mail body " + str(email_index),
                    "from" + str(email_index) + "@test.com")
        self.account11.__dict__["get_mail"] = get_email

    def check_step_1 (self, result):
        """
        Check first step result of get-email ad-hoc command
        """
        result_iq = result[0].xmlnode
        result_iq.setNs(None)
        self.assertTrue(jcl.tests.is_xml_equal(\
                u"<iq from='account11@" + unicode(self.comp.jid) 
                + "' to='test1@test.com' type='result'>"
                + "<command xmlns='http://jabber.org/protocol/commands'"
                + "status='executing'>"
                + "<actions execute='complete'><complete/></actions>"
                + "<x xmlns='jabber:x:data' type='form'>"
                + "<title>" + Lang.en.command_get_email + "</title>"
                + "<instructions>" + Lang.en.command_get_email_1_description
                + "</instructions>"
                + "<field var='emails' type='list-multi' label='"
                + Lang.en.field_email_subject + "'>"
                + "<option label=\"mail 1\">"
                + "<value>1</value></option>"
                + "<option label=\"mail 2\">"
                + "<value>2</value></option>"
                + "</field><field var='fetch_more' type='boolean' label='"
                + Lang.en.field_select_more_emails + "'>"
                + "</field></x></command></iq>",
                result_iq, True))
        session_id = result_iq.children.prop("sessionid")
        self.assertNotEquals(session_id, None)
        return session_id

    def test_execute_get_email(self):
        """
        Test single email retrieval
        """
        self.info_query.set_from("test1@test.com")
        self.info_query.set_to("account11@" + unicode(self.comp.jid))
        result = self.command_manager.apply_command_action(\
            self.info_query,
            "jmc#get-email",
            "execute")
        session_id = self.check_step_1(result)

        # Second step
        info_query = self.prepare_submit(\
            node="jmc#get-email",
            session_id=session_id,
            from_jid="test1@test.com",
            to_jid="account11@jmc.test.com",
            fields=[Field(field_type="list-multi",
                          name="emails",
                          values=["1"]),
                    Field(field_type="boolean",
                          name="fetch_more",
                          value=False)],
            action="complete")
        result = self.command_manager.apply_command_action(\
            info_query,
            "jmc#get-email",
            "execute")
        self.assertEquals(len(result), 2)
        result_iq = result[0].xmlnode
        result_iq.setNs(None)
        self.assertTrue(jcl.tests.is_xml_equal(\
                u"<iq from='account11@" + unicode(self.comp.jid)
                + "' to='test1@test.com' type='result'>"
                + "<command xmlns='http://jabber.org/protocol/commands' "
                + "status='completed'>"
                + "<x xmlns='jabber:x:data' type='form'>"
                + "<title>" + Lang.en.command_get_email + "</title>"
                + "<instructions>" + Lang.en.command_get_email_2_description
                % (1) + "</instructions>"
                + "</x></command></iq>",
                result_iq, True, test_sibling=False))
        result_iq = result[1].xmlnode
        self.assertTrue(jcl.tests.is_xml_equal(\
                u"<message from='account11@" + unicode(self.comp.jid)
                + "' to='test1@test.com' "
                + "xmlns='http://pyxmpp.jabberstudio.org/xmlns/common'>"
                + "<subject>" + Lang.en.mail_subject % ("from1@test.com")
                + "</subject>"
                + "<body>mail body 1</body>"
                + "<addresses xmlns='http://jabber.org/protocol/address'>"
                + "<address type='replyto' jid='from1%test.com@jmc.test.com'/>"
                + "</addresses>"
                + "</message>",
                result_iq, True, test_sibling=False))

    def test_execute_get_emails(self):
        """
        Test multiple emails retrieval
        """
        self.info_query.set_from("test1@test.com")
        self.info_query.set_to("account11@" + unicode(self.comp.jid))
        result = self.command_manager.apply_command_action(\
            self.info_query,
            "jmc#get-email",
            "execute")
        session_id = self.check_step_1(result)

        # Second step
        info_query = self.prepare_submit(\
            node="jmc#get-email",
            session_id=session_id,
            from_jid="test1@test.com",
            to_jid="account11@jmc.test.com",
            fields=[Field(field_type="list-multi",
                          name="emails",
                          values=["1", "2"]),
                    Field(field_type="boolean",
                          name="fetch_more",
                          value=False)],
            action="complete")
        result = self.command_manager.apply_command_action(\
            info_query,
            "jmc#get-email",
            "execute")
        self.assertEquals(len(result), 3)
        result_iq = result[0].xmlnode
        result_iq.setNs(None)
        self.assertTrue(jcl.tests.is_xml_equal(\
                u"<iq from='account11@" + unicode(self.comp.jid)
                + "' to='test1@test.com' type='result'>"
                + "<command xmlns='http://jabber.org/protocol/commands' "
                + "status='completed'>"
                + "<x xmlns='jabber:x:data' type='form'>"
                + "<title>" + Lang.en.command_get_email + "</title>"
                + "<instructions>" + Lang.en.command_get_email_2_description
                % (2) + "</instructions>"
                + "</x></command></iq>",
                result_iq, True, test_sibling=False))
        result_iq = result[1].xmlnode
        self.assertTrue(jcl.tests.is_xml_equal(\
                u"<message from='account11@" + unicode(self.comp.jid)
                + "' to='test1@test.com' "
                + "xmlns='http://pyxmpp.jabberstudio.org/xmlns/common'>"
                + "<subject>" + Lang.en.mail_subject % ("from1@test.com")
                + "</subject>"
                + "<body>mail body 1</body>"
                + "<addresses xmlns='http://jabber.org/protocol/address'>"
                + "<address type='replyto' jid='from1%test.com@jmc.test.com'/>"
                + "</addresses>"
                + "</message>",
                result_iq, True, test_sibling=False))
        result_iq = result[2].xmlnode
        self.assertTrue(jcl.tests.is_xml_equal(\
                u"<message from='account11@" + unicode(self.comp.jid)
                + "' to='test1@test.com' "
                + "xmlns='http://pyxmpp.jabberstudio.org/xmlns/common'>"
                + "<subject>" + Lang.en.mail_subject % ("from2@test.com")
                + "</subject>"
                + "<body>mail body 2</body>"
                + "<addresses xmlns='http://jabber.org/protocol/address'>"
                + "<address type='replyto' jid='from2%test.com@jmc.test.com'/>"
                + "</addresses>"
                + "</message>",
                result_iq, True, test_sibling=False))

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(MailCommandManagerForceCheckCommand_TestCase, 'test'))
    test_suite.addTest(unittest.makeSuite(MailCommandManagerGetEmailCommand_TestCase, 'test'))
    return test_suite

if __name__ == '__main__':
    if '-v' in sys.argv:
        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)
    unittest.main(defaultTest='suite')
