# -*- coding: utf-8 -*-
##
## test_component.py
## Login : <dax@happycoders.org>
## Started on  Wed Feb 14 18:04:49 2007 David Rousselie
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
import sys
import time

from sqlobject import *
from sqlobject.dbconnection import TheURIOpener

from pyxmpp.presence import Presence
from pyxmpp.message import Message
from pyxmpp.iq import Iq

from jcl.tests import JCLTestCase
import jcl.model as model
from jcl.model import account
from jcl.model.account import Account, PresenceAccount, LegacyJID, User
from jcl.jabber.tests.presence import DefaultSubscribeHandler_TestCase, \
    DefaultUnsubscribeHandler_TestCase
from jcl.jabber.tests.feeder import FeederMock, SenderMock

from jmc.model.account import MailAccount, IMAPAccount, POP3Account, \
     SMTPAccount, NoAccountError
from jmc.jabber import MailHandler
from jmc.jabber.message import SendMailMessageHandler
from jmc.jabber.presence import MailSubscribeHandler, \
     MailUnsubscribeHandler, MailPresenceHandler
from jmc.jabber.component import MailComponent, MailFeederHandler, \
     MailSender
from jmc.lang import Lang

if sys.platform == "win32":
   DB_PATH = "/c|/temp/jmc_test.db"
else:
   DB_PATH = "/tmp/jmc_test.db"
DB_URL = DB_PATH# + "?debug=1&debugThreading=1"

class MockStream(object):
    def __init__(self,
                 jid="",
                 secret="",
                 server="",
                 port="",
                 keepalive=True):
        self.sent = []
        self.connection_started = False
        self.connection_stopped = False
        self.eof = False
        self.socket = []

    def send(self, iq):
        self.sent.append(iq)

    def set_iq_set_handler(self, iq_type, ns, handler):
        if not iq_type in ["query"]:
            raise Exception("IQ type unknown: " + iq_type)
        if not ns in ["jabber:iq:version",
                      "jabber:iq:register",
                      "http://jabber.org/protocol/disco#items",
                      "http://jabber.org/protocol/disco#info"]:
            raise Exception("Unknown namespace: " + ns)
        if handler is None:
            raise Exception("Handler must not be None")

    set_iq_get_handler = set_iq_set_handler

    def set_presence_handler(self, status, handler):
        if not status in ["available",
                          "unavailable",
                          "probe",
                          "subscribe",
                          "subscribed",
                          "unsubscribe",
                          "unsubscribed"]:
            raise Exception("Status unknown: " + status)
        if handler is None:
            raise Exception("Handler must not be None")

    def set_message_handler(self, msg_type, handler):
        if not msg_type in ["normal"]:
            raise Exception("Message type unknown: " + msg_type)
        if handler is None:
            raise Exception("Handler must not be None")

    def connect(self):
        self.connection_started = True

    def disconnect(self):
        self.connection_stopped = True

    def loop_iter(self, timeout):
        time.sleep(timeout)

    def close(self):
        pass

class MockMailAccount(object):
    def _init(self):
        self.connected = False
        self.has_connected = False
        self.marked_all_as_read = False
        self._action = PresenceAccount.DO_NOTHING

    def connect(self):
        self.connected = True
        self.has_connected = True

    def mark_all_as_read(self):
        self.marked_all_as_read = True

    def disconnect(self):
        self.connected = False

    def get_action(self):
        return self._action

    action = property(get_action)

class MockIMAPAccount(MockMailAccount, IMAPAccount):
    def _init(self, *args, **kw):
        IMAPAccount._init(self, *args, **kw)
        MockMailAccount._init(self)

    def ls_dir(self, imap_dir):
        if imap_dir == "":
            return ["INBOX"]
        elif imap_dir == "INBOX":
            return ["dir1", "dir2"]
        elif imap_dir == "INBOX/dir1":
            return ["subdir1", "subdir2"]
        return []

    def get_mail_with_attachment_list(self):
       return [("1", "mail 1"),
               ("2", "mail 2")]

    def get_mail_list_summary(self):
       return [("1", "mail 1"),
               ("2", "mail 2")]


class MockPOP3Account(MockMailAccount, POP3Account):
    def _init(self, *args, **kw):
        POP3Account._init(self, *args, **kw)
        MockMailAccount._init(self)

class MailComponent_TestCase(JCLTestCase):
    def setUp(self):
        JCLTestCase.setUp(self, tables=[Account, PresenceAccount, User,
                                        MailAccount, IMAPAccount, POP3Account,
                                        SMTPAccount, MockIMAPAccount,
                                        MockPOP3Account])
        self.comp = MailComponent("jmc.test.com",
                                  "password",
                                  "localhost",
                                  "5347",
                                  None,
                                  None)
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream

    ###########################################################################
    # 'feed' test methods
    ###########################################################################
    def test_feed_live_email_init_no_password(self):
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertEquals(account11.error, None)
        self.assertFalse(account11.waiting_password_reply)
        account11.live_email_only = True
        account11.password = None
        result = self.comp.handler.feeder.feed(account11)
        self.assertEquals(len(result), 0)
        sent = self.comp.stream.sent
        self.assertEquals(len(sent), 1)
        self.assertEquals(sent[0].get_to(), "test1@test.com")
        self.assertEquals(sent[0].get_from(), "account11@jmc.test.com")
        self.assertTrue(account11.first_check)
        self.assertTrue(account11.waiting_password_reply)
        self.assertEquals(account11.error, None)
        self.assertFalse(account11.connected)
        self.assertFalse(account11.has_connected)
        self.assertFalse(account11.marked_all_as_read)
        model.db_disconnect()

    def test_feed_live_email_init_no_password2(self):
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertEquals(account11.error, None)
        account11.waiting_password_reply = True
        account11.live_email_only = True
        account11.password = None
        result = self.comp.handler.feeder.feed(account11)
        self.assertEquals(result, [])
        self.assertTrue(account11.first_check)
        self.assertTrue(account11.waiting_password_reply)
        self.assertEquals(account11.error, None)
        self.assertFalse(account11.connected)
        self.assertFalse(account11.has_connected)
        self.assertFalse(account11.marked_all_as_read)
        self.assertEquals(len(self.comp.stream.sent), 0)
        model.db_disconnect()

    def test_feed_interval_no_check(self):
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = PresenceAccount.DO_NOTHING
        account11.first_check = False
        self.assertEquals(account11.lastcheck, 0)
        account11.interval = 2
        result = self.comp.handler.feeder.feed(account11)
        self.assertEquals(result, [])
        self.assertEquals(account11.lastcheck, 1)
        model.db_disconnect()

    def test_feed_interval_check(self):
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = PresenceAccount.DO_NOTHING
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        result = self.comp.handler.feeder.feed(account11)
        self.assertEquals(result, [])
        self.assertEquals(account11.lastcheck, 0)
        model.db_disconnect()

    def test_feed_no_password(self):
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = MailAccount.RETRIEVE
        account11.status = account.ONLINE
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        account11.password = None
        self.assertFalse(account11.waiting_password_reply)
        result = self.comp.handler.feeder.feed(account11)
        self.assertEquals(account11.error, None)
        self.assertEquals(len(result), 0)
        sent = self.comp.stream.sent
        self.assertEquals(len(sent), 1)
        self.assertEquals(sent[0].get_to(), "test1@test.com")
        self.assertEquals(sent[0].get_from(), "account11@jmc.test.com")
        self.assertEquals(account11.lastcheck, 0)
        self.assertFalse(account11.connected)
        self.assertFalse(account11.has_connected)
        model.db_disconnect()

    def test_feed_unknown_action(self):
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = 42 # Unknown action
        account11.status = account.ONLINE
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        account11.password = "password"
        account11.get_new_mail_list = lambda: []
        result = self.comp.handler.feeder.feed(account11)
        self.assertNotEquals(account11.error, None)
        self.assertEquals(len(result), 0)
        sent = self.comp.stream.sent
        self.assertEquals(len(sent), 1)
        self.assertEquals(sent[0].get_to(), "test1@test.com")
        self.assertEquals(sent[0].get_from(), "account11@jmc.test.com")
        self.assertEquals(account11.lastcheck, 0)
        self.assertFalse(account11.connected)
        self.assertTrue(account11.has_connected)
        model.db_disconnect()

    def test_feed_retrieve_no_mail(self):
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = MailAccount.RETRIEVE
        account11.status = account.ONLINE
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        account11.password = "password"
        account11.get_new_mail_list = lambda: []
        result = self.comp.handler.feeder.feed(account11)
        self.assertEquals(account11.error, None)
        self.assertEquals(result, [])
        self.assertEquals(account11.lastcheck, 0)
        self.assertFalse(account11.connected)
        self.assertTrue(account11.has_connected)
        self.assertEquals(len(self.comp.stream.sent), 0)
        model.db_disconnect()

    def test_feed_retrieve_mail(self):
        def mock_get_mail(index):
            return [("body1", "from1@test.com"),
                    ("body2", "from2@test.com")][index]
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = MailAccount.RETRIEVE
        account11.status = account.ONLINE
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        account11.password = "password"
        account11.get_new_mail_list = lambda: [0, 1]
        account11.get_mail = mock_get_mail
        result = self.comp.handler.feeder.feed(account11)
        self.assertEquals(account11.error, None)
        self.assertEquals(account11.lastcheck, 0)
        self.assertFalse(account11.connected)
        self.assertTrue(account11.has_connected)
        self.assertEquals(len(self.comp.stream.sent), 0)
        self.assertEquals(len(result), 2)
        self.assertEquals(result[0][0],
                          "from1@test.com")
        self.assertEquals(result[0][1],
                          account11.default_lang_class.new_mail_subject \
                          % ("from1@test.com"))
        self.assertEquals(result[0][2], "body1")
        self.assertEquals(result[1][0],
                          "from2@test.com")
        self.assertEquals(result[1][1], \
                          account11.default_lang_class.new_mail_subject \
                          % ("from2@test.com"))
        self.assertEquals(result[1][2], "body2")
        model.db_disconnect()

    def test_feed_digest_no_mail(self):
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = MailAccount.DIGEST
        account11.status = account.ONLINE
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        account11.password = "password"
        account11.get_new_mail_list = lambda: []
        result = self.comp.handler.feeder.feed(account11)
        self.assertEquals(account11.error, None)
        self.assertEquals(result, [])
        self.assertEquals(account11.lastcheck, 0)
        self.assertFalse(account11.connected)
        self.assertTrue(account11.has_connected)
        self.assertEquals(len(self.comp.stream.sent), 0)
        model.db_disconnect()

    def test_feed_digest_mail(self):
        def mock_get_mail_summary(index):
            return [("body1", "from1@test.com"),
                    ("body2", "from2@test.com")][index]
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = MailAccount.DIGEST
        account11.status = account.ONLINE
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        account11.password = "password"
        account11.get_new_mail_list = lambda: [0, 1]
        account11.get_mail_summary = mock_get_mail_summary
        result = self.comp.handler.feeder.feed(account11)
        self.assertEquals(account11.error, None)
        self.assertEquals(account11.lastcheck, 0)
        self.assertFalse(account11.connected)
        self.assertTrue(account11.has_connected)
        self.assertEquals(len(self.comp.stream.sent), 0)
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0][1],
                          account11.default_lang_class.new_digest_subject \
                          % (2))
        self.assertEquals(result[0][2],
                          "body1\n----------------------------------\nbody2\n----------------------------------\n")
        model.db_disconnect()

    ###########################################################################
    # 'initialize_live_email' test methods
    ###########################################################################
    def test_initialize_live_email(self):
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertEquals(account11.error, None)
        account11.live_email_only = True
        account11.password = "password"
        continue_checking = self.comp.handler.feeder.initialize_live_email(account11)
        self.assertEquals(continue_checking, True)
        self.assertFalse(account11.first_check)
        self.assertFalse(account11.waiting_password_reply)
        self.assertEquals(account11.error, None)
        self.assertFalse(account11.connected)
        self.assertTrue(account11.has_connected)
        self.assertTrue(account11.marked_all_as_read)
        model.db_disconnect()

    def test_initialize_live_email_connection_error(self):
        def raiser():
            raise Exception
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11.connect = raiser
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertEquals(account11.error, None)
        account11.live_email_only = True
        account11.password = "password"
        continue_checking = self.comp.handler.feeder.initialize_live_email(account11)
        self.assertEquals(continue_checking, False)
        sent = self.comp.stream.sent
        self.assertEquals(len(sent), 1)
        self.assertEquals(sent[0].get_to(), "test1@test.com")
        self.assertEquals(sent[0].get_from(), "account11@jmc.test.com")
        self.assertTrue(account11.first_check)
        self.assertFalse(account11.waiting_password_reply)
        self.assertEquals(account11.error, "")
        self.assertFalse(account11.connected)
        self.assertFalse(account11.has_connected)
        self.assertFalse(account11.marked_all_as_read)
        model.db_disconnect()

    def test_initialize_live_email_mark_as_read_error(self):
        def raiser():
            raise Exception
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11.mark_all_as_read = raiser
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertEquals(account11.error, None)
        account11.live_email_only = True
        account11.password = "password"
        continue_checking = self.comp.handler.feeder.initialize_live_email(account11)
        self.assertEquals(continue_checking, False)
        sent = self.comp.stream.sent
        self.assertEquals(len(sent), 1)
        self.assertEquals(sent[0].get_to(), "test1@test.com")
        self.assertEquals(sent[0].get_from(), "account11@jmc.test.com")
        self.assertTrue(account11.first_check)
        self.assertFalse(account11.waiting_password_reply)
        self.assertEquals(account11.error, "")
        self.assertFalse(account11.connected)
        self.assertTrue(account11.has_connected)
        self.assertFalse(account11.marked_all_as_read)
        model.db_disconnect()

    def test_initialize_live_email_disconnection_error(self):
        def raiser():
            raise Exception
        model.db_connect()
        account11 = MockIMAPAccount(user=User(jid="test1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11.disconnect = raiser
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertEquals(account11.error, None)
        account11.live_email_only = True
        account11.password = "password"
        continue_checking = self.comp.handler.feeder.initialize_live_email(account11)
        self.assertFalse(continue_checking)
        sent = self.comp.stream.sent
        self.assertEquals(len(sent), 1)
        self.assertEquals(sent[0].get_to(), "test1@test.com")
        self.assertEquals(sent[0].get_from(), "account11@jmc.test.com")
        self.assertEquals(continue_checking, False)
        self.assertTrue(account11.first_check)
        self.assertFalse(account11.waiting_password_reply)
        self.assertEquals(account11.error, "")
        self.assertFalse(account11.connected)
        self.assertTrue(account11.has_connected)
        self.assertTrue(account11.marked_all_as_read)
        model.db_disconnect()

    def test_disco_get_info_imap_node(self):
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream
        account11 = MockIMAPAccount(user=User(jid="user1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        info_query = Iq(stanza_type="get",
                        from_jid="user1@test.com",
                        to_jid="jcl.test.com/IMAP")
        disco_info = self.comp.disco_get_info("IMAP", info_query)
        self.assertEquals(len(self.comp.stream.sent), 0)
        self.assertTrue(disco_info.has_feature("jabber:iq:register"))
        self.assertTrue(disco_info.has_feature("http://jabber.org/protocol/disco#info"))
        self.assertTrue(disco_info.has_feature("http://jabber.org/protocol/disco#items"))

    def test_disco_get_info_imap_node_no_account(self):
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream
        account11 = MockPOP3Account(user=User(jid="user1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account21 = MockIMAPAccount(user=User(jid="user2@test.com"),
                                    name="account21",
                                    jid="account21@jmc.test.com")
        info_query = Iq(stanza_type="get",
                        from_jid="user1@test.com",
                        to_jid="jcl.test.com/IMAP")
        disco_info = self.comp.disco_get_info("IMAP", info_query)
        self.assertEquals(len(self.comp.stream.sent), 0)
        self.assertTrue(disco_info.has_feature("jabber:iq:register"))
        self.assertFalse(disco_info.has_feature("http://jabber.org/protocol/disco#info"))
        self.assertFalse(disco_info.has_feature("http://jabber.org/protocol/disco#items"))

    def test_disco_get_info_imap_long_node(self):
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream
        account11 = MockIMAPAccount(user=User(jid="user1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        info_query = Iq(stanza_type="get",
                        from_jid="user1@test.com",
                        to_jid="account11@jcl.test.com/IMAP")
        disco_info = self.comp.disco_get_info("IMAP/account11",
                                              info_query)
        self.assertEquals(len(self.comp.stream.sent), 0)
        self.assertTrue(disco_info.has_feature("jabber:iq:register"))
        self.assertTrue(disco_info.has_feature("http://jabber.org/protocol/disco#info"))
        self.assertTrue(disco_info.has_feature("http://jabber.org/protocol/disco#items"))

    def test_disco_get_info_not_imap_long_node(self):
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream
        account11 = MockPOP3Account(user=User(jid="user1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        info_query = Iq(stanza_type="get",
                        from_jid="user1@test.com",
                        to_jid="account11@jcl.test.com/POP3")
        disco_info = self.comp.disco_get_info("POP3/account11",
                                              info_query)
        self.assertEquals(len(self.comp.stream.sent), 0)
        self.assertTrue(disco_info.has_feature("jabber:iq:register"))
        self.assertFalse(disco_info.has_feature("http://jabber.org/protocol/disco#info"))
        self.assertFalse(disco_info.has_feature("http://jabber.org/protocol/disco#items"))

    def test_disco_get_info_imap_dir_node(self):
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream
        account11 = MockIMAPAccount(user=User(jid="user1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11.mailbox = "INBOX/dir1"
        info_query = Iq(stanza_type="get",
                        from_jid="user1@test.com",
                        to_jid="account11@jcl.test.com/IMAP/INBOX")
        disco_info = self.comp.disco_get_info("IMAP/account11/INBOX",
                                              info_query)
        self.assertEquals(len(self.comp.stream.sent), 0)
        self.assertTrue(disco_info.has_feature("jabber:iq:register"))
        self.assertTrue(disco_info.has_feature("http://jabber.org/protocol/disco#info"))
        self.assertTrue(disco_info.has_feature("http://jabber.org/protocol/disco#items"))

    def test_disco_get_info_imap_dir_node_already_registered(self):
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream
        account11 = MockIMAPAccount(user=User(jid="user1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11.mailbox = "INBOX"
        info_query = Iq(stanza_type="get",
                        from_jid="user1@test.com",
                        to_jid="account11@jcl.test.com/IMAP/INBOX")
        disco_info = self.comp.disco_get_info("IMAP/account11/INBOX",
                                              info_query)
        self.assertEquals(len(self.comp.stream.sent), 0)
        self.assertTrue(disco_info.has_feature("jabber:iq:register"))
        self.assertTrue(disco_info.has_feature("http://jabber.org/protocol/disco#info"))
        self.assertTrue(disco_info.has_feature("http://jabber.org/protocol/disco#items"))

    def test_disco_get_info_imap_dir_node_last_subdir(self):
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream
        account11 = MockIMAPAccount(user=User(jid="user1@test.com"),
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11.mailbox = "INBOX/dir1/subdir1"
        info_query = Iq(stanza_type="get",
                        from_jid="user1@test.com",
                        to_jid="account11@jcl.test.com/IMAP/INBOX/dir1/subdir1")
        disco_info = self.comp.disco_get_info("IMAP/account11/INBOX/dir1/subdir1",
                                              info_query)
        self.assertEquals(len(self.comp.stream.sent), 0)
        self.assertTrue(disco_info.has_feature("jabber:iq:register"))
        self.assertTrue(disco_info.has_feature("http://jabber.org/protocol/disco#info"))
        self.assertFalse(disco_info.has_feature("http://jabber.org/protocol/disco#items"))

    def test_disco_get_items_base_imap_account(self):
        account11 = MockIMAPAccount(user=User(jid="user1@test.com"),
                                    name="account11",
                                    jid="account11@jcl.test.com")
        info_query = Iq(stanza_type="get",
                        from_jid="user1@test.com",
                        to_jid="account11@jcl.test.com/IMAP")
        disco_items = self.comp.disco_get_items("IMAP/account11", info_query)
        self.assertEquals(len(disco_items.get_items()), 1)
        disco_item = disco_items.get_items()[0]
        self.assertEquals(unicode(disco_item.get_jid()), unicode(account11.jid)
                          + "/IMAP/INBOX")
        self.assertEquals(disco_item.get_node(), "IMAP/" + account11.name + "/INBOX")
        self.assertEquals(disco_item.get_name(), "INBOX")

    def test_disco_get_items_inbox_imap_account(self):
        account11 = MockIMAPAccount(user=User(jid="user1@test.com"),
                                    name="account11",
                                    jid="account11@jcl.test.com")
        info_query = Iq(stanza_type="get",
                        from_jid="user1@test.com",
                        to_jid="account11@jcl.test.com/IMAP/INBOX")
        disco_items = self.comp.disco_get_items("IMAP/account11/INBOX", info_query)
        self.assertEquals(len(disco_items.get_items()), 2)
        disco_item = disco_items.get_items()[0]
        self.assertEquals(unicode(disco_item.get_jid()), unicode(account11.jid)
                          + "/IMAP/INBOX/dir1")
        self.assertEquals(disco_item.get_node(), "IMAP/" + account11.name + "/INBOX"
                          + "/dir1")
        self.assertEquals(disco_item.get_name(), "dir1")
        disco_item = disco_items.get_items()[1]
        self.assertEquals(unicode(disco_item.get_jid()), unicode(account11.jid)
                          + "/IMAP/INBOX/dir2")
        self.assertEquals(disco_item.get_node(), "IMAP/" + account11.name + "/INBOX"
                          + "/dir2")
        self.assertEquals(disco_item.get_name(), "dir2")

    def test_disco_get_items_subdir_imap_account(self):
        account11 = MockIMAPAccount(user=User(jid="user1@test.com"),
                                    name="account11",
                                    jid="account11@jcl.test.com")
        info_query = Iq(stanza_type="get",
                        from_jid="user1@test.com",
                        to_jid="account11@jcl.test.com/IMAP")
        disco_items = self.comp.disco_get_items("IMAP/account11/INBOX/dir1", info_query)
        self.assertEquals(len(disco_items.get_items()), 2)
        disco_item = disco_items.get_items()[0]
        self.assertEquals(unicode(disco_item.get_jid()), unicode(account11.jid)
                          + "/IMAP/INBOX/dir1/subdir1")
        self.assertEquals(disco_item.get_node(), "IMAP/" + account11.name + "/INBOX"
                          + "/dir1/subdir1")
        self.assertEquals(disco_item.get_name(), "subdir1")
        disco_item = disco_items.get_items()[1]
        self.assertEquals(unicode(disco_item.get_jid()), unicode(account11.jid)
                          + "/IMAP/INBOX/dir1/subdir2")
        self.assertEquals(disco_item.get_node(), "IMAP/" + account11.name + "/INBOX"
                          + "/dir1/subdir2")
        self.assertEquals(disco_item.get_name(), "subdir2")

    def test_account_get_register_imap_dir_already_registered(self):
        model.db_connect()
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream
        user1 = User(jid="user1@test.com")
        account1 = MockIMAPAccount(user=user1,
                                   name="account1",
                                   jid="account1@jcl.test.com")
        account1.mailbox = "INBOX"
        account11 = MockIMAPAccount(user=user1,
                                    name="account11",
                                    jid="account11@jcl.test.com")
        account11.mailbox = "INBOX/dir1"
        account11.password = "pass1"
        account11.port = 993
        account11.host = "host1"
        account11.login = "login1"
        account11.ssl = True
        account11.interval = 1
        account11.store_password = False
        account11.live_email_only = True
        account11.chat_action = PresenceAccount.DO_NOTHING
        account11.online_action = PresenceAccount.DO_NOTHING
        account11.away_action = PresenceAccount.DO_NOTHING
        account11.xa_action = PresenceAccount.DO_NOTHING
        account11.dnd_action = PresenceAccount.DO_NOTHING
        account11.offline_action = PresenceAccount.DO_NOTHING
        account21 = MockIMAPAccount(user=User(jid="user2@test.com"),
                                    name="account21",
                                    jid="account21@jcl.test.com")
        model.db_disconnect()
        self.comp.handle_get_register(Iq(stanza_type="get",
                                         from_jid="user1@test.com",
                                         to_jid="account1@jcl.test.com/IMAP/INBOX/dir1"))
        self.assertEquals(len(self.comp.stream.sent), 1)
        iq_sent = self.comp.stream.sent[0]
        self.assertEquals(iq_sent.get_to(), "user1@test.com")
        titles = iq_sent.xpath_eval("jir:query/jxd:x/jxd:title",
                                    {"jir" : "jabber:iq:register",
                                     "jxd" : "jabber:x:data"})
        self.assertEquals(len(titles), 1)
        self.assertEquals(titles[0].content,
                          Lang.en.register_title)
        instructions = iq_sent.xpath_eval("jir:query/jxd:x/jxd:instructions",
                                          {"jir" : "jabber:iq:register",
                                           "jxd" : "jabber:x:data"})
        self.assertEquals(len(instructions), 1)
        self.assertEquals(instructions[0].content,
                          Lang.en.register_instructions)
        fields = iq_sent.xpath_eval("jir:query/jxd:x/jxd:field",
                                    {"jir" : "jabber:iq:register",
                                     "jxd" : "jabber:x:data"})
        self.assertEquals(len(fields), 16)
        field = fields[0]
        self.assertEquals(field.prop("type"), "hidden")
        self.assertEquals(field.prop("var"), "name")
        self.assertEquals(field.prop("label"), Lang.en.account_name)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "account11")
        self.assertEquals(field.children.next.name, "required")
        field = fields[1]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "chat_action")
        self.assertEquals(field.prop("label"), Lang.en.field_chat_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[2]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "online_action")
        self.assertEquals(field.prop("label"), Lang.en.field_online_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[3]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "away_action")
        self.assertEquals(field.prop("label"), Lang.en.field_away_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[4]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "xa_action")
        self.assertEquals(field.prop("label"), Lang.en.field_xa_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[5]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "dnd_action")
        self.assertEquals(field.prop("label"), Lang.en.field_dnd_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[6]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "offline_action")
        self.assertEquals(field.prop("label"), Lang.en.field_offline_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[7]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "login")
        self.assertEquals(field.prop("label"), Lang.en.field_login)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "login1")
        self.assertEquals(field.children.next.name, "required")
        field = fields[8]
        self.assertEquals(field.prop("type"), "text-private")
        self.assertEquals(field.prop("var"), "password")
        self.assertEquals(field.prop("label"), Lang.en.field_password)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "pass1")
        field = fields[9]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "host")
        self.assertEquals(field.prop("label"), Lang.en.field_host)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "host1")
        self.assertEquals(field.children.next.name, "required")
        field = fields[10]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "port")
        self.assertEquals(field.prop("label"), Lang.en.field_port)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "993")
        field = fields[11]
        self.assertEquals(field.prop("type"), "boolean")
        self.assertEquals(field.prop("var"), "ssl")
        self.assertEquals(field.prop("label"), Lang.en.field_ssl)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "1")
        field = fields[12]
        self.assertEquals(field.prop("type"), "boolean")
        self.assertEquals(field.prop("var"), "store_password")
        self.assertEquals(field.prop("label"), Lang.en.field_store_password)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[13]
        self.assertEquals(field.prop("type"), "boolean")
        self.assertEquals(field.prop("var"), "live_email_only")
        self.assertEquals(field.prop("label"), Lang.en.field_live_email_only)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "1")
        field = fields[14]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "interval")
        self.assertEquals(field.prop("label"), Lang.en.field_interval)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "1")
        field = fields[15]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "mailbox")
        self.assertEquals(field.prop("label"), Lang.en.field_mailbox)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "INBOX/dir1")

    def test_account_get_register_imap_dir_new(self):
        model.db_connect()
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream
        user1 = User(jid="user1@test.com")
        account1 = MockIMAPAccount(user=user1,
                                   name="account1",
                                   jid="account1@jcl.test.com")
        account1.maildir = "INBOX"
        account1.password = "pass1"
        account1.port = 993
        account1.host = "host1"
        account1.login = "login1"
        account1.ssl = True
        account1.interval = 1
        account1.store_password = False
        account1.live_email_only = True
        account1.chat_action = PresenceAccount.DO_NOTHING
        account1.online_action = PresenceAccount.DO_NOTHING
        account1.away_action = PresenceAccount.DO_NOTHING
        account1.xa_action = PresenceAccount.DO_NOTHING
        account1.dnd_action = PresenceAccount.DO_NOTHING
        account1.offline_action = PresenceAccount.DO_NOTHING
        account11 = MockIMAPAccount(user=user1,
                                    name="account11",
                                    jid="account11@jcl.test.com")
        account11.maildir = "INBOX/dir1"
        account11.delimiter = "/"
        account21 = MockIMAPAccount(user=User(jid="user2@test.com"),
                                    name="account21",
                                    jid="account21@jcl.test.com")
        model.db_disconnect()
        self.comp.handle_get_register(Iq(stanza_type="get",
                                         from_jid="user1@test.com",
                                         to_jid="account1@jcl.test.com/IMAP/INBOX/dir1/subdir1"))
        self.assertEquals(len(self.comp.stream.sent), 1)
        iq_sent = self.comp.stream.sent[0]
        self.assertEquals(iq_sent.get_to(), "user1@test.com")
        titles = iq_sent.xpath_eval("jir:query/jxd:x/jxd:title",
                                    {"jir" : "jabber:iq:register",
                                     "jxd" : "jabber:x:data"})
        self.assertEquals(len(titles), 1)
        self.assertEquals(titles[0].content,
                          Lang.en.register_title)
        instructions = iq_sent.xpath_eval("jir:query/jxd:x/jxd:instructions",
                                          {"jir" : "jabber:iq:register",
                                           "jxd" : "jabber:x:data"})
        self.assertEquals(len(instructions), 1)
        self.assertEquals(instructions[0].content,
                          Lang.en.register_instructions)
        fields = iq_sent.xpath_eval("jir:query/jxd:x/jxd:field",
                                    {"jir" : "jabber:iq:register",
                                     "jxd" : "jabber:x:data"})
        self.assertEquals(len(fields), 16)
        field = fields[0]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "name")
        self.assertEquals(field.prop("label"), Lang.en.account_name)
        self.assertEquals(field.children.name, "required")
        self.assertEquals(field.children.next, None)
        field = fields[1]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "chat_action")
        self.assertEquals(field.prop("label"), Lang.en.field_chat_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[2]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "online_action")
        self.assertEquals(field.prop("label"), Lang.en.field_online_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[3]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "away_action")
        self.assertEquals(field.prop("label"), Lang.en.field_away_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[4]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "xa_action")
        self.assertEquals(field.prop("label"), Lang.en.field_xa_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[5]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "dnd_action")
        self.assertEquals(field.prop("label"), Lang.en.field_dnd_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[6]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "offline_action")
        self.assertEquals(field.prop("label"), Lang.en.field_offline_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[7]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "login")
        self.assertEquals(field.prop("label"), Lang.en.field_login)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "login1")
        self.assertEquals(field.children.next.name, "required")
        field = fields[8]
        self.assertEquals(field.prop("type"), "text-private")
        self.assertEquals(field.prop("var"), "password")
        self.assertEquals(field.prop("label"), Lang.en.field_password)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "pass1")
        field = fields[9]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "host")
        self.assertEquals(field.prop("label"), Lang.en.field_host)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "host1")
        self.assertEquals(field.children.next.name, "required")
        field = fields[10]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "port")
        self.assertEquals(field.prop("label"), Lang.en.field_port)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "993")
        field = fields[11]
        self.assertEquals(field.prop("type"), "boolean")
        self.assertEquals(field.prop("var"), "ssl")
        self.assertEquals(field.prop("label"), Lang.en.field_ssl)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "1")
        field = fields[12]
        self.assertEquals(field.prop("type"), "boolean")
        self.assertEquals(field.prop("var"), "store_password")
        self.assertEquals(field.prop("label"), Lang.en.field_store_password)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[13]
        self.assertEquals(field.prop("type"), "boolean")
        self.assertEquals(field.prop("var"), "live_email_only")
        self.assertEquals(field.prop("label"), Lang.en.field_live_email_only)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "1")
        field = fields[14]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "interval")
        self.assertEquals(field.prop("label"), Lang.en.field_interval)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "1")
        field = fields[15]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "mailbox")
        self.assertEquals(field.prop("label"), Lang.en.field_mailbox)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "INBOX/dir1/subdir1")

    def test_account_get_register_imap_dir_new(self):
        model.db_connect()
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream
        user1 = User(jid="user1@test.com")
        account1 = MockIMAPAccount(user=user1,
                                   name="account1",
                                   jid="account1@jcl.test.com")
        account1.maildir = "INBOX"
        account1.password = "pass1"
        account1.port = 993
        account1.host = "host1"
        account1.login = "login1"
        account1.ssl = True
        account1.interval = 1
        account1.store_password = False
        account1.live_email_only = True
        account1.chat_action = PresenceAccount.DO_NOTHING
        account1.online_action = PresenceAccount.DO_NOTHING
        account1.away_action = PresenceAccount.DO_NOTHING
        account1.xa_action = PresenceAccount.DO_NOTHING
        account1.dnd_action = PresenceAccount.DO_NOTHING
        account1.offline_action = PresenceAccount.DO_NOTHING
        account11 = MockIMAPAccount(user=user1,
                                    name="account11",
                                    jid="account11@jcl.test.com")
        account11.maildir = "INBOX/dir1"
        account11.delimiter = "."
        account21 = MockIMAPAccount(user=User(jid="user2@test.com"),
                                    name="account21",
                                    jid="account21@jcl.test.com")
        model.db_disconnect()
        self.comp.handle_get_register(Iq(stanza_type="get",
                                         from_jid="user1@test.com",
                                         to_jid="account1@jcl.test.com/IMAP/INBOX/dir1/subdir1"))
        self.assertEquals(len(self.comp.stream.sent), 1)
        iq_sent = self.comp.stream.sent[0]
        self.assertEquals(iq_sent.get_to(), "user1@test.com")
        titles = iq_sent.xpath_eval("jir:query/jxd:x/jxd:title",
                                    {"jir" : "jabber:iq:register",
                                     "jxd" : "jabber:x:data"})
        self.assertEquals(len(titles), 1)
        self.assertEquals(titles[0].content,
                          Lang.en.register_title)
        instructions = iq_sent.xpath_eval("jir:query/jxd:x/jxd:instructions",
                                          {"jir" : "jabber:iq:register",
                                           "jxd" : "jabber:x:data"})
        self.assertEquals(len(instructions), 1)
        self.assertEquals(instructions[0].content,
                          Lang.en.register_instructions)
        fields = iq_sent.xpath_eval("jir:query/jxd:x/jxd:field",
                                    {"jir" : "jabber:iq:register",
                                     "jxd" : "jabber:x:data"})
        self.assertEquals(len(fields), 16)
        field = fields[0]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "name")
        self.assertEquals(field.prop("label"), Lang.en.account_name)
        self.assertEquals(field.children.name, "required")
        self.assertEquals(field.children.next, None)
        field = fields[1]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "chat_action")
        self.assertEquals(field.prop("label"), Lang.en.field_chat_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[2]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "online_action")
        self.assertEquals(field.prop("label"), Lang.en.field_online_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[3]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "away_action")
        self.assertEquals(field.prop("label"), Lang.en.field_away_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[4]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "xa_action")
        self.assertEquals(field.prop("label"), Lang.en.field_xa_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[5]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "dnd_action")
        self.assertEquals(field.prop("label"), Lang.en.field_dnd_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[6]
        self.assertEquals(field.prop("type"), "list-single")
        self.assertEquals(field.prop("var"), "offline_action")
        self.assertEquals(field.prop("label"), Lang.en.field_offline_action)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[7]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "login")
        self.assertEquals(field.prop("label"), Lang.en.field_login)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "login1")
        self.assertEquals(field.children.next.name, "required")
        field = fields[8]
        self.assertEquals(field.prop("type"), "text-private")
        self.assertEquals(field.prop("var"), "password")
        self.assertEquals(field.prop("label"), Lang.en.field_password)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "pass1")
        field = fields[9]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "host")
        self.assertEquals(field.prop("label"), Lang.en.field_host)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "host1")
        self.assertEquals(field.children.next.name, "required")
        field = fields[10]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "port")
        self.assertEquals(field.prop("label"), Lang.en.field_port)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "993")
        field = fields[11]
        self.assertEquals(field.prop("type"), "boolean")
        self.assertEquals(field.prop("var"), "ssl")
        self.assertEquals(field.prop("label"), Lang.en.field_ssl)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "1")
        field = fields[12]
        self.assertEquals(field.prop("type"), "boolean")
        self.assertEquals(field.prop("var"), "store_password")
        self.assertEquals(field.prop("label"), Lang.en.field_store_password)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "0")
        field = fields[13]
        self.assertEquals(field.prop("type"), "boolean")
        self.assertEquals(field.prop("var"), "live_email_only")
        self.assertEquals(field.prop("label"), Lang.en.field_live_email_only)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "1")
        field = fields[14]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "interval")
        self.assertEquals(field.prop("label"), Lang.en.field_interval)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "1")
        field = fields[15]
        self.assertEquals(field.prop("type"), "text-single")
        self.assertEquals(field.prop("var"), "mailbox")
        self.assertEquals(field.prop("label"), Lang.en.field_mailbox)
        self.assertEquals(field.children.name, "value")
        self.assertEquals(field.children.content, "INBOX.dir1.subdir1")

class MailSender_TestCase(JCLTestCase):
    def setUp(self):
        JCLTestCase.setUp(self, tables=[Account, PresenceAccount, MailAccount,
                                        IMAPAccount, POP3Account, User])

    def test_create_message(self):
        mail_sender = MailSender()
        model.db_connect()
        user1 = User(jid="test1@test.com")
        account11 = IMAPAccount(user=user1,
                                name="account11",
                                jid="account11@jmc.test.com")
        account11.online_action = MailAccount.RETRIEVE
        account11.status = account.ONLINE
        message = mail_sender.create_message(account11, ("from@test.com",
                                                         "subject",
                                                         "message body"))
        self.assertEquals(message.get_to(), user1.jid)
        model.db_disconnect()
        self.assertEquals(message.get_subject(), "subject")
        self.assertEquals(message.get_body(), "message body")
        addresses = message.xpath_eval("add:addresses/add:address",
                                       {"add": "http://jabber.org/protocol/address"})
        self.assertEquals(len(addresses), 1)
        self.assertEquals(addresses[0].prop("type"),
                          "replyto")
        self.assertEquals(addresses[0].prop("jid"),
                          "from%test.com@jmc.test.com")

    def test_create_message_digest(self):
        mail_sender = MailSender()
        model.db_connect()
        user1 = User(jid="test1@test.com")
        account11 = IMAPAccount(user=user1,
                                name="account11",
                                jid="account11@jmc.test.com")
        account11.online_action = MailAccount.DIGEST
        account11.status = account.ONLINE
        message = mail_sender.create_message(account11, ("from@test.com",
                                                         "subject",
                                                         "message body"))
        self.assertEquals(message.get_to(), user1.jid)
        model.db_disconnect()
        self.assertEquals(message.get_subject(), "subject")
        self.assertEquals(message.get_body(), "message body")
        self.assertEquals(message.get_type(), "headline")

class MailHandler_TestCase(JCLTestCase):
    def setUp(self, tables=[]):
        self.handler = MailHandler(None)
        JCLTestCase.setUp(self, tables=[Account, SMTPAccount, User] + tables)

    def test_filter(self):
        model.db_connect()
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jcl.test.com")
        account11.default_account = True
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jcl.test.com")
        message = Message(from_jid="user1@test.com",
                          to_jid="user2%test.com@jcl.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertNotEquals(accounts, None)
        i = 0
        for _account in accounts:
            i += 1
            if i == 1:
                self.assertEquals(_account.name, "account11")
        self.assertEquals(i, 1)
        model.db_disconnect()

    def test_filter_root(self):
        model.db_connect()
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jcl.test.com")
        account11.default_account = True
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jcl.test.com")
        message = Message(from_jid="user1@test.com",
                          to_jid="jcl.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertEquals(accounts, None)
        model.db_disconnect()

    def test_filter_no_default(self):
        model.db_connect()
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jcl.test.com")
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jcl.test.com")
        message = Message(from_jid="user1@test.com",
                          to_jid="user2%test.com@jcl.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertNotEquals(accounts, None)
        i = 0
        for _account in accounts:
            i += 1
            if i == 1:
                self.assertEquals(_account.name, "account11")
            else:
                self.assertEquals(_account.name, "account12")
        self.assertEquals(i, 2)
        model.db_disconnect()

    def test_filter_wrong_dest(self):
        model.db_connect()
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jcl.test.com")
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jcl.test.com")
        message = Message(from_jid="user1@test.com",
                          to_jid="user2test.com@jcl.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertEquals(accounts, None)
        model.db_disconnect()

    def test_filter_wrong_account(self):
        model.db_connect()
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jcl.test.com")
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jcl.test.com")
        message = Message(from_jid="user3@test.com",
                          to_jid="user2%test.com@jcl.test.com",
                          body="message")
        try:
            accounts = self.handler.filter(message, None)
            model.db_disconnect()
        except NoAccountError, e:
            model.db_disconnect()
            self.assertNotEquals(e, None)
        else:
            self.fail("No exception 'NoAccountError' catched")

class MailPresenceHandler_TestCase(unittest.TestCase):
    def setUp(self):
        self.handler = MailPresenceHandler(None)

    def test_filter(self):
        message = Message(from_jid="user1@test.com",
                          to_jid="user11%test.com@jcl.test.com",
                          body="message")
        result = self.handler.filter(message, None)
        self.assertNotEquals(result, None)

    def test_filter_wrong_dest(self):
        message = Message(from_jid="user1@test.com",
                          to_jid="user11@jcl.test.com",
                          body="message")
        result = self.handler.filter(message, None)
        self.assertEquals(result, None)

    def test_filter_wrong_dest2(self):
        message = Message(from_jid="user1@test.com",
                          to_jid="jcl.test.com",
                          body="message")
        result = self.handler.filter(message, None)
        self.assertEquals(result, None)

class MailSubscribeHandler_TestCase(DefaultSubscribeHandler_TestCase, MailHandler_TestCase):
    def setUp(self):
        MailHandler_TestCase.setUp(self, tables=[LegacyJID])
        self.handler = MailSubscribeHandler(None)

    def test_handle(self):
        model.db_connect()
        account11 = SMTPAccount(user=User(jid="user1@test.com"),
                                name="account11",
                                jid="account11@jcl.test.com")
        presence = Presence(from_jid="user1@test.com",
                            to_jid="user1%test.com@jcl.test.com",
                            stanza_type="subscribe")
        result = self.handler.handle(presence, Lang.en, [account11])
        legacy_jids = LegacyJID.select()
        self.assertEquals(legacy_jids.count(), 1)
        model.db_disconnect()

class MailUnsubscribeHandler_TestCase(DefaultUnsubscribeHandler_TestCase, MailHandler_TestCase):
    def setUp(self):
        MailHandler_TestCase.setUp(self, tables=[LegacyJID])
        self.handler = MailUnsubscribeHandler(None)

    def test_handle(self):
        model.db_connect()
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jcl.test.com")
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jcl.test.com")
        account2 = SMTPAccount(user=User(jid="user2@test.com"),
                               name="account2",
                               jid="account2@jcl.test.com")
        presence = Presence(from_jid="user1@test.com",
                            to_jid="u111%test.com@jcl.test.com",
                            stanza_type="unsubscribe")
        legacy_jid111 = LegacyJID(legacy_address="u111@test.com",
                                  jid="u111%test.com@jcl.test.com",
                                  account=account11)
        legacy_jid112 = LegacyJID(legacy_address="u112@test.com",
                                  jid="u112%test.com@jcl.test.com",
                                  account=account11)
        legacy_jid121 = LegacyJID(legacy_address="u121@test.com",
                                  jid="u121%test.com@jcl.test.com",
                                  account=account12)
        legacy_jid122 = LegacyJID(legacy_address="u122@test.com",
                                  jid="u122%test.com@jcl.test.com",
                                  account=account12)
        legacy_jid21 = LegacyJID(legacy_address="u21@test.com",
                                 jid="u21%test.com@jcl.test.com",
                                 account=account2)
        result = self.handler.handle(presence, Lang.en, [account11])
        legacy_jids = LegacyJID.select()
        self.assertEquals(legacy_jids.count(), 4)
        removed_legacy_jid = LegacyJID.select(\
           LegacyJID.q.jid == "u111%test.com@jcl.test.com")
        self.assertEquals(removed_legacy_jid.count(), 0)
        model.db_disconnect()

class MailFeederHandler_TestCase(JCLTestCase):
    def setUp(self):
        self.handler = MailFeederHandler(FeederMock(), SenderMock())
        JCLTestCase.setUp(self, tables=[Account, PresenceAccount, MailAccount,
                                        IMAPAccount, POP3Account, SMTPAccount,
                                        User])

    def test_filter(self):
        model.db_connect()
        account11 = SMTPAccount(user=User(jid="user1@test.com"),
                                name="account11",
                                jid="account11@jcl.test.com")
        account13 = IMAPAccount(user=User(jid="user3@test.com"),
                                name="account13",
                                jid="account13@jcl.test.com")
        account12 = POP3Account(user=User(jid="user2@test.com"),
                                name="account12",
                                jid="account12@jcl.test.com")
        accounts = self.handler.filter(None, None)
        i = 0
        # SQLObject > 0.8 is needed
        for _account in accounts:
            i += 1
            if i == 1:
                self.assertEquals(_account.name, "account13")
            else:
                self.assertEquals(_account.name, "account12")
        self.assertEquals(i, 2)
        model.db_disconnect()

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(MailComponent_TestCase, 'test'))
    test_suite.addTest(unittest.makeSuite(MailSender_TestCase, 'test'))
    test_suite.addTest(unittest.makeSuite(MailHandler_TestCase, 'test'))
    test_suite.addTest(unittest.makeSuite(MailUnsubscribeHandler_TestCase, 'test'))
    test_suite.addTest(unittest.makeSuite(MailSubscribeHandler_TestCase, 'test'))
    test_suite.addTest(unittest.makeSuite(MailPresenceHandler_TestCase, 'test'))
    test_suite.addTest(unittest.makeSuite(MailFeederHandler_TestCase, 'test'))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
