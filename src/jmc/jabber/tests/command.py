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

from pyxmpp.iq import Iq
from pyxmpp.jabber.dataforms import Form

import jcl.tests
from jcl.jabber.tests.command import JCLCommandManager_TestCase
from jcl.jabber.feeder import Feeder
from jcl.model.account import Account, PresenceAccount, LegacyJID, \
    User
import jcl.jabber.command as command

from jmc.model.account import POP3Account, IMAPAccount, SMTPAccount, \
    MailAccount
from jmc.jabber.component import MailComponent
from jmc.jabber.command import MailCommandManager

from jmc.jabber.tests.component import MockIMAPAccount

class MailCommandManager_TestCase(JCLCommandManager_TestCase):
    def setUp(self):
        JCLCommandManager_TestCase.setUp(self, tables=[POP3Account, IMAPAccount,
                                                       SMTPAccount, MailAccount,
                                                       MockIMAPAccount])
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
        self.command_manager = command.command_manager

    def tearDown(self):
        JCLCommandManager_TestCase.tearDown(self)
        if os.path.exists(self.config_file):
            os.unlink(self.config_file)

#     def test_execute_retrieve_attachment(self):
#         self.comp.account_manager.account_classes = (POP3Account, IMAPAccount,
#                                                      SMTPAccount, MockIMAPAccount)
#         account1 = MockIMAPAccount(user=User(jid="test1@test.com"),
#                                    name="account1",
#                                    jid="account1@" + unicode(self.comp.jid))
#         info_query = Iq(stanza_type="set",
#                         from_jid="test1@test.com",
#                         to_jid="account1@" + unicode(self.comp.jid))
#         command_node = info_query.set_new_content(command.COMMAND_NS, "command")
#         command_node.setProp("node", "jmc#retrieve-attachment")
#         result = self.command_manager.apply_command_action(info_query,
#                                                            "jmc#retrieve-attachment",
#                                                            "execute")
#         self.assertNotEquals(result, None)
#         self.assertEquals(len(result), 1)
#         print str(result[0].xmlnode)
#         xml_command = result[0].xpath_eval("c:command",
#                                            {"c": "http://jabber.org/protocol/commands"})[0]
#         self.assertEquals(xml_command.prop("status"), "executing")
#         self.assertNotEquals(xml_command.prop("sessionid"), None)
#         self._check_actions(result[0], ["next"])
#         print str(result[0].xmlnode)
#         x_data = result[0].xpath_eval("c:command/data:x",
#                                       {"c": "http://jabber.org/protocol/commands",
#                                        "data": "jabber:x:data"})
#         self.assertEquals(len(x_data), 1)
#         self.assertEquals(x_data[0].prop("type"), "form")
#         options = result[0].xpath_eval("c:command/data:x/data:field[1]/data:option",
#                                        {"c": "http://jabber.org/protocol/commands",
#                                         "data": "jabber:x:data"})
#         self.assertEquals(len(options), 3)
#         self.assertEquals(options[0].prop("label"), "Next")
#         self.assertEquals(options[0].children.name, "value")
#         self.assertEquals(options[0].children.content, "-1")
#         self.assertEquals(options[1].prop("label"), "mail 1")
#         self.assertEquals(options[1].children.name, "value")
#         self.assertEquals(options[1].children.content, "1")
#         self.assertEquals(options[2].prop("label"), "mail 2")
#         self.assertEquals(options[2].children.name, "value")
#         self.assertEquals(options[2].children.content, "2")

#         # Delayed to JMC 0.3.1
#         return
#         # Second step: TODO
#         info_query = Iq(stanza_type="set",
#                         from_jid="admin@test.com",
#                         to_jid=self.comp.jid)
#         command_node = info_query.set_new_content(command.COMMAND_NS, "command")
#         command_node.setProp("node", "http://jabber.org/protocol/admin#add-user")
#         session_id = xml_command.prop("sessionid")
#         command_node.setProp("sessionid", session_id)
#         command_node.setProp("action", "next")
#         submit_form = Form(xmlnode_or_type="submit")
#         submit_form.add_field(field_type="list-single",
#                               name="account_type",
#                               value="Example")
#         submit_form.add_field(field_type="jid-single",
#                               name="user_jid",
#                               value="user2@test.com")
#         submit_form.as_xml(command_node)
#         result = self.command_manager.apply_command_action(info_query,
#                                                            "http://jabber.org/protocol/admin#add-user",
#                                                            "next")
#         self.assertNotEquals(result, None)
#         self.assertEquals(len(result), 1)
#         xml_command = result[0].xpath_eval("c:command",
#                                            {"c": "http://jabber.org/protocol/commands"})[0]
#         self.assertEquals(xml_command.prop("status"), "executing")
#         self.assertEquals(xml_command.prop("sessionid"), session_id)
#         self._check_actions(result[0], ["prev", "complete"], 1)
#         x_data = result[0].xpath_eval("c:command/data:x",
#                                       {"c": "http://jabber.org/protocol/commands",
#                                        "data": "jabber:x:data"})
#         self.assertEquals(len(x_data), 1)
#         self.assertEquals(x_data[0].prop("type"), "form")
#         fields = result[0].xpath_eval("c:command/data:x/data:field",
#                                       {"c": "http://jabber.org/protocol/commands",
#                                        "data": "jabber:x:data"})
#         self.assertEquals(len(fields), 6)
#         context_session = self.command_manager.sessions[session_id][1]
#         self.assertEquals(context_session["account_type"], ["Example"])
#         self.assertEquals(context_session["user_jid"], ["user2@test.com"])

#         # Third step
#         info_query = Iq(stanza_type="set",
#                         from_jid="admin@test.com",
#                         to_jid=self.comp.jid)
#         command_node = info_query.set_new_content(command.COMMAND_NS, "command")
#         command_node.setProp("node", "http://jabber.org/protocol/admin#add-user")
#         command_node.setProp("sessionid", session_id)
#         command_node.setProp("action", "complete")
#         submit_form = Form(xmlnode_or_type="submit")
#         submit_form.add_field(field_type="text-single",
#                               name="name",
#                               value="account1")
#         submit_form.add_field(field_type="text-single",
#                               name="login",
#                               value="login1")
#         submit_form.add_field(field_type="text-private",
#                               name="password",
#                               value="pass1")
#         submit_form.add_field(field_type="boolean",
#                               name="store_password",
#                               value="1")
#         submit_form.add_field(field_type="list-single",
#                               name="test_enum",
#                               value="choice2")
#         submit_form.add_field(field_type="text-single",
#                               name="test_int",
#                               value="42")
#         submit_form.as_xml(command_node)

#         result = self.command_manager.apply_command_action(info_query,
#                                                            "http://jabber.org/protocol/admin#add-user",
#                                                            "execute")
#         xml_command = result[0].xpath_eval("c:command",
#                                            {"c": "http://jabber.org/protocol/commands"})[0]
#         self.assertEquals(xml_command.prop("status"), "completed")
#         self.assertEquals(xml_command.prop("sessionid"), session_id)
#         self._check_actions(result[0])

#         self.assertEquals(context_session["name"], ["account1"])
#         self.assertEquals(context_session["login"], ["login1"])
#         self.assertEquals(context_session["password"], ["pass1"])
#         self.assertEquals(context_session["store_password"], ["1"])
#         self.assertEquals(context_session["test_enum"], ["choice2"])
#         self.assertEquals(context_session["test_int"], ["42"])

#         model.db_connect()
#         _account = account.get_account("user2@test.com",
#                                        "account1")
#         self.assertNotEquals(_account, None)
#         self.assertEquals(_account.user.jid, "user2@test.com")
#         self.assertEquals(_account.name, "account1")
#         self.assertEquals(_account.jid, "account1@" + unicode(self.comp.jid))
#         model.db_disconnect()

#         stanza_sent = result
#         self.assertEquals(len(stanza_sent), 4)
#         iq_result = stanza_sent[0]
#         self.assertTrue(isinstance(iq_result, Iq))
#         self.assertEquals(iq_result.get_node().prop("type"), "result")
#         self.assertEquals(iq_result.get_from(), self.comp.jid)
#         self.assertEquals(iq_result.get_to(), "admin@test.com")
#         presence_component = stanza_sent[1]
#         self.assertTrue(isinstance(presence_component, Presence))
#         self.assertEquals(presence_component.get_from(), self.comp.jid)
#         self.assertEquals(presence_component.get_to(), "user2@test.com")
#         self.assertEquals(presence_component.get_node().prop("type"),
#                           "subscribe")
#         message = stanza_sent[2]
#         self.assertTrue(isinstance(message, Message))
#         self.assertEquals(message.get_from(), self.comp.jid)
#         self.assertEquals(message.get_to(), "user2@test.com")
#         self.assertEquals(message.get_subject(),
#                           _account.get_new_message_subject(Lang.en))
#         self.assertEquals(message.get_body(),
#                           _account.get_new_message_body(Lang.en))
#         presence_account = stanza_sent[3]
#         self.assertTrue(isinstance(presence_account, Presence))
#         self.assertEquals(presence_account.get_from(), "account1@" + unicode(self.comp.jid))
#         self.assertEquals(presence_account.get_to(), "user2@test.com")
#         self.assertEquals(presence_account.get_node().prop("type"),
#                           "subscribe")

    def test_execute_force_check(self):
        self.comp.account_manager.account_classes = (POP3Account, IMAPAccount,
                                                     SMTPAccount, MockIMAPAccount)
        class MockFeederHandler(Feeder):
            def __init__(self, component):
                Feeder.__init__(self, component)
                self.checked_accounts = []

            def feed(self, _account):
                self.checked_accounts.append(_account)
                assert(_account.lastcheck == (_account.interval - 1))
                return []

        self.comp.handler.feeder = MockFeederHandler(self.comp)
        user1 = User(jid="test1@test.com")
        user2 = User(jid="test2@test.com")
        account11 = MockIMAPAccount(user=user1,
                                    name="account11",
                                    jid="account11@" + unicode(self.comp.jid))
        account12 = MockIMAPAccount(user=user1,
                                    name="account12",
                                    jid="account12@" + unicode(self.comp.jid))
        account21 = MockIMAPAccount(user=user2,
                                    name="account21",
                                    jid="account21@" + unicode(self.comp.jid))
        account22 = MockIMAPAccount(user=user2,
                                    name="account11",
                                    jid="account11@" + unicode(self.comp.jid))
        info_query = Iq(stanza_type="set",
                        from_jid="test1@test.com",
                        to_jid=self.comp.jid)
        command_node = info_query.set_new_content(command.COMMAND_NS, "command")
        command_node.setProp("node", "jmc#force-check")
        result = self.command_manager.apply_command_action(info_query,
                                                           "jmc#force-check",
                                                           "execute")
        self.assertNotEquals(result, None)
        self.assertEquals(len(result), 1)
        xml_command = result[0].xpath_eval("c:command",
                                           {"c": "http://jabber.org/protocol/commands"})[0]
        self.assertEquals(xml_command.prop("status"), "executing")
        self.assertNotEquals(xml_command.prop("sessionid"), None)
        self._check_actions(result[0], ["complete"])
        session_id = xml_command.prop("sessionid")
        context_session = self.command_manager.sessions[session_id][1]
        self.assertEquals(context_session["user_jids"],
                          ["test1@test.com"])

        # Second step
        info_query = Iq(stanza_type="set",
                        from_jid="admin@test.com",
                        to_jid=self.comp.jid)
        command_node = info_query.set_new_content(command.COMMAND_NS, "command")
        command_node.setProp("node", "jmc#force-check")
        command_node.setProp("sessionid", session_id)
        command_node.setProp("action", "complete")
        submit_form = Form(xmlnode_or_type="submit")
        submit_form.add_field(field_type="list-multi",
                              name="account_names",
                              values=["account11/test1@test.com",
                                      "account12/test1@test.com"])
        submit_form.as_xml(command_node)
        result = self.command_manager.apply_command_action(info_query,
                                                           "jmc#force-check",
                                                           "execute")
        xml_command = result[0].xpath_eval("c:command",
                                           {"c": "http://jabber.org/protocol/commands"})[0]
        self.assertEquals(xml_command.prop("status"), "completed")
        self.assertEquals(xml_command.prop("sessionid"), session_id)
        self._check_actions(result[0])
        self.assertEquals(context_session["account_names"],
                          ["account11/test1@test.com",
                           "account12/test1@test.com"])
        feeder = self.comp.handler.feeder
        self.assertEquals(len(feeder.checked_accounts), 2)
        self.assertEquals(feeder.checked_accounts[0], account11)
        self.assertEquals(feeder.checked_accounts[1], account12)

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(MailCommandManager_TestCase, 'test'))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
