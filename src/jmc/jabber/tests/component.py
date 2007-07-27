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
import os
import sys
import time

from sqlobject import *
from sqlobject.dbconnection import TheURIOpener

from pyxmpp.presence import Presence
from pyxmpp.message import Message

import jcl.model as model
from jcl.model import account
from jcl.model.account import Account, PresenceAccount, LegacyJID
from jcl.jabber.tests.presence import DefaultSubscribeHandler_TestCase, \
    DefaultUnsubscribeHandler_TestCase
from jcl.jabber.tests.feeder import FeederMock, SenderMock

from jmc.model.account import MailAccount, IMAPAccount, POP3Account, \
     SMTPAccount, NoAccountError
from jmc.jabber import MailHandler
from jmc.jabber.message import SendMailMessageHandler, \
     RootSendMailMessageHandler
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

class MockPOP3Account(MockMailAccount, POP3Account):
    def _init(self, *args, **kw):
        IMAPAccount._init(self, *args, **kw)
        MockMailAccount._init(self)

class MockSMTPAccount(object):
    def __init__(self):
        self.default_from = "user1@test.com"

    def create_email(self, from_email, to_email, subject, body):
        return (from_email, to_email, subject, body)

    def send_email(self, email):
        self.email = email

class MailComponent_TestCase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        self.comp = MailComponent("jmc.test.com",
                                 "password",
                                 "localhost",
                                 "5347")
        self.comp.stream = MockStream()
        self.comp.stream_class = MockStream
        model.db_connection_str = 'sqlite://' + DB_URL
        model.db_connect()
        Account.createTable(ifNotExists=True)
        PresenceAccount.createTable(ifNotExists=True)
        MailAccount.createTable(ifNotExists=True)
        IMAPAccount.createTable(ifNotExists=True)
        POP3Account.createTable(ifNotExists=True)
        SMTPAccount.createTable(ifNotExists=True)
        MockIMAPAccount.createTable(ifNotExists=True)
        MockPOP3Account.createTable(ifNotExists=True)
        model.db_disconnect()

    def tearDown(self):
        model.db_connect()
        MockPOP3Account.dropTable(ifExists=True)
        MockIMAPAccount.dropTable(ifExists=True)
        SMTPAccount.dropTable(ifExists=True)
        POP3Account.dropTable(ifExists=True)
        IMAPAccount.dropTable(ifExists=True)
        MailAccount.dropTable(ifExists=True)
        PresenceAccount.dropTable(ifExists=True)
        Account.dropTable(ifExists=True)
        del TheURIOpener.cachedURIs['sqlite://' + DB_URL]
        model.hub.threadConnection.close()
        model.db_disconnect()
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)

    ###########################################################################
    # 'feed' test methods
    ###########################################################################
    def test_feed_live_email_init_no_password(self):
        model.db_connect()
        account11 = MockIMAPAccount(user_jid="test1@test.com",
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertFalse(account11.in_error)
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
        self.assertFalse(account11.in_error)
        self.assertFalse(account11.connected)
        self.assertFalse(account11.has_connected)
        self.assertFalse(account11.marked_all_as_read)
        model.db_disconnect()

    def test_feed_live_email_init_no_password2(self):
        model.db_connect()
        account11 = MockIMAPAccount(user_jid="test1@test.com",
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertFalse(account11.in_error)
        account11.waiting_password_reply = True
        account11.live_email_only = True
        account11.password = None
        result = self.comp.handler.feeder.feed(account11)
        self.assertEquals(result, [])
        self.assertTrue(account11.first_check)
        self.assertTrue(account11.waiting_password_reply)
        self.assertFalse(account11.in_error)
        self.assertFalse(account11.connected)
        self.assertFalse(account11.has_connected)
        self.assertFalse(account11.marked_all_as_read)
        self.assertEquals(len(self.comp.stream.sent), 0)
        model.db_disconnect()

    def test_feed_interval_no_check(self):
        model.db_connect()
        account11 = MockIMAPAccount(user_jid="test1@test.com",
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
        account11 = MockIMAPAccount(user_jid="test1@test.com",
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
        account11 = MockIMAPAccount(user_jid="test1@test.com",
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
        self.assertFalse(account11.in_error)
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
        account11 = MockIMAPAccount(user_jid="test1@test.com",
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = 42 # Unknown action
        account11.status = account.ONLINE
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        account11.password = "password"
        account11.get_mail_list = lambda: []
        result = self.comp.handler.feeder.feed(account11)
        self.assertTrue(account11.in_error)
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
        account11 = MockIMAPAccount(user_jid="test1@test.com",
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = MailAccount.RETRIEVE
        account11.status = account.ONLINE
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        account11.password = "password"
        account11.get_mail_list = lambda: []
        result = self.comp.handler.feeder.feed(account11)
        self.assertFalse(account11.in_error)
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
        account11 = MockIMAPAccount(user_jid="test1@test.com",
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = MailAccount.RETRIEVE
        account11.status = account.ONLINE
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        account11.password = "password"
        account11.get_mail_list = lambda: [0, 1]
        account11.get_mail = mock_get_mail
        result = self.comp.handler.feeder.feed(account11)
        self.assertFalse(account11.in_error)
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
        account11 = MockIMAPAccount(user_jid="test1@test.com",
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = MailAccount.DIGEST
        account11.status = account.ONLINE
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        account11.password = "password"
        account11.get_mail_list = lambda: []
        result = self.comp.handler.feeder.feed(account11)
        self.assertFalse(account11.in_error)
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
        account11 = MockIMAPAccount(user_jid="test1@test.com",
                                    name="account11",
                                    jid="account11@jmc.test.com")
        account11._action = MailAccount.DIGEST
        account11.status = account.ONLINE
        account11.first_check = False
        account11.lastcheck = 1
        account11.interval = 2
        account11.password = "password"
        account11.get_mail_list = lambda: [0, 1]
        account11.get_mail_summary = mock_get_mail_summary
        result = self.comp.handler.feeder.feed(account11)
        self.assertFalse(account11.in_error)
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
        account11 = MockIMAPAccount(user_jid = "test1@test.com", \
                                    name = "account11", \
                                    jid = "account11@jmc.test.com")
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertFalse(account11.in_error)
        account11.live_email_only = True
        account11.password = "password"
        continue_checking = self.comp.handler.feeder.initialize_live_email(account11)
        self.assertEquals(continue_checking, True)
        self.assertFalse(account11.first_check)
        self.assertFalse(account11.waiting_password_reply)
        self.assertFalse(account11.in_error)
        self.assertFalse(account11.connected)
        self.assertTrue(account11.has_connected)
        self.assertTrue(account11.marked_all_as_read)
        model.db_disconnect()

    def test_initialize_live_email_connection_error(self):
        def raiser():
            raise Exception
        model.db_connect()
        account11 = MockIMAPAccount(user_jid = "test1@test.com", \
                                    name = "account11", \
                                    jid = "account11@jmc.test.com")
        account11.connect = raiser
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertFalse(account11.in_error)
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
        self.assertTrue(account11.in_error)
        self.assertFalse(account11.connected)
        self.assertFalse(account11.has_connected)
        self.assertFalse(account11.marked_all_as_read)
        model.db_disconnect()

    def test_initialize_live_email_mark_as_read_error(self):
        def raiser():
            raise Exception
        model.db_connect()
        account11 = MockIMAPAccount(user_jid = "test1@test.com", \
                                    name = "account11", \
                                    jid = "account11@jmc.test.com")
        account11.mark_all_as_read = raiser
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertFalse(account11.in_error)
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
        self.assertTrue(account11.in_error)
        self.assertFalse(account11.connected)
        self.assertTrue(account11.has_connected)
        self.assertFalse(account11.marked_all_as_read)
        model.db_disconnect()

    def test_initialize_live_email_disconnection_error(self):
        def raiser():
            raise Exception
        model.db_connect()
        account11 = MockIMAPAccount(user_jid = "test1@test.com", \
                                    name = "account11", \
                                    jid = "account11@jmc.test.com")
        account11.disconnect = raiser
        account11.status = account.ONLINE
        self.assertTrue(account11.first_check)
        self.assertFalse(account11.in_error)
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
        self.assertTrue(account11.in_error)
        self.assertFalse(account11.connected)
        self.assertTrue(account11.has_connected)
        self.assertTrue(account11.marked_all_as_read)
        model.db_disconnect()

class SendMailMessageHandler_TestCase(unittest.TestCase):
    def setUp(self):
        self.handler = SendMailMessageHandler(None)

    def test_handle(self):
        message = Message(from_jid="user1@test.com",
                          to_jid="user%test.com@jcl.test.com",
                          subject="message subject",
                          body="message body")
        accounts = [MockSMTPAccount()]
        result = self.handler.handle(message, Lang.en, accounts)
        self.assertEquals(accounts[0].email[1], "user@test.com")
        self.assertEquals(accounts[0].email[2], "message subject")
        self.assertEquals(accounts[0].email[3], "message body")
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0].stanza_type, "message")
        self.assertEquals(result[0].get_from(), "user%test.com@jcl.test.com")
        self.assertEquals(result[0].get_to(), "user1@test.com")
        self.assertEquals(result[0].get_subject(),
                          Lang.en.send_mail_ok_subject)
        self.assertEquals(result[0].get_body(),
                          Lang.en.send_mail_ok_body % ("user@test.com"))

class RootSendMailMessageHandler_TestCase(unittest.TestCase):
    def setUp(self):
        self.handler = RootSendMailMessageHandler(None)
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        model.db_connection_str = 'sqlite://' + DB_URL
        model.db_connect()
        Account.createTable(ifNotExists=True)
        SMTPAccount.createTable(ifNotExists=True)
        model.db_disconnect()

    def tearDown(self):
        model.db_connect()
        SMTPAccount.dropTable(ifExists=True)
        Account.dropTable(ifExists=True)
        del TheURIOpener.cachedURIs['sqlite://' + DB_URL]
        model.hub.threadConnection.close()
        model.db_disconnect()
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)

    def test_filter(self):
        model.db_connect()
        account11 = SMTPAccount(user_jid="user1@test.com",
                                name="account11",
                                jid="account11@jcl.test.com")
        account11.default_account = True
        account12 = SMTPAccount(user_jid="user1@test.com",
                                name="account12",
                                jid="account12@jcl.test.com")
        message = Message(from_jid="user1@test.com",
                          to_jid="account11@jcl.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertEquals(accounts.count(), 1)
        model.db_disconnect()

    def test_filter_no_default_account(self):
        model.db_connect()
        account11 = SMTPAccount(user_jid="user1@test.com",
                                name="account11",
                                jid="account11@jcl.test.com")
        account12 = SMTPAccount(user_jid="user1@test.com",
                                name="account12",
                                jid="account12@jcl.test.com")
        message = Message(from_jid="user1@test.com",
                          to_jid="account11@jcl.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertEquals(accounts.count(), 2)
        self.assertEquals(accounts[0].name, "account11")
        model.db_disconnect()

    def test_filter_wrong_dest(self):
        model.db_connect()
        account11 = SMTPAccount(user_jid="user1@test.com",
                                name="account11",
                                jid="account11@jcl.test.com")
        account12 = SMTPAccount(user_jid="user1@test.com",
                                name="account12",
                                jid="account12@jcl.test.com")
        message = Message(from_jid="user1@test.com",
                          to_jid="user2%test.com@jcl.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertEquals(accounts.count(), 2)
        model.db_disconnect()

    def test_filter_wrong_user(self):
        model.db_connect()
        account11 = SMTPAccount(user_jid="user1@test.com",
                                name="account11",
                                jid="account11@jcl.test.com")
        account12 = SMTPAccount(user_jid="user1@test.com",
                                name="account12",
                                jid="account12@jcl.test.com")
        message = Message(from_jid="user2@test.com",
                          to_jid="account11@jcl.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertEquals(accounts.count(), 0)
        model.db_disconnect()

    def test_handle_email_found_in_header(self):
        message = Message(from_jid="user1@test.com",
                          to_jid="jcl.test.com",
                          subject="message subject",
                          body="to: user@test.com\n" \
                             "message body\nother line")
        accounts = [MockSMTPAccount()]
        result = self.handler.handle(message, Lang.en, accounts)
        self.assertEquals(accounts[0].email[1], "user@test.com")
        self.assertEquals(accounts[0].email[2], "message subject")
        self.assertEquals(accounts[0].email[3],
                          "message body\nother line")
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0].get_type(), None)
        self.assertEquals(result[0].get_from(), "jcl.test.com")
        self.assertEquals(result[0].get_to(), "user1@test.com")
        self.assertEquals(result[0].get_subject(),
                          Lang.en.send_mail_ok_subject)
        self.assertEquals(result[0].get_body(),
                          Lang.en.send_mail_ok_body % ("user@test.com"))

    def test_handle_email_not_found_in_header(self):
        message = Message(from_jid="user1@test.com",
                          to_jid="jcl.test.com",
                          subject="message subject",
                          body="message body")
        accounts = [MockSMTPAccount()]
        result = self.handler.handle(message, Lang.en, accounts)
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0].get_type(), "error")
        self.assertEquals(result[0].get_from(), "jcl.test.com")
        self.assertEquals(result[0].get_to(), "user1@test.com")
        self.assertEquals(result[0].get_subject(),
                          Lang.en.send_mail_error_no_to_header_subject)
        self.assertEquals(result[0].get_body(),
                          Lang.en.send_mail_error_no_to_header_body)

class MailSender_TestCase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        model.db_connection_str = 'sqlite://' + DB_URL
        model.db_connect()
        Account.createTable(ifNotExists=True)
        PresenceAccount.createTable(ifNotExists=True)
        MailAccount.createTable(ifNotExists=True)
        IMAPAccount.createTable(ifNotExists=True)
        POP3Account.createTable(ifNotExists=True)
        model.db_disconnect()

    def tearDown(self):
        model.db_connect()
        POP3Account.dropTable(ifExists=True)
        IMAPAccount.dropTable(ifExists=True)
        MailAccount.dropTable(ifExists=True)
        PresenceAccount.dropTable(ifExists=True)
        Account.dropTable(ifExists=True)
        del TheURIOpener.cachedURIs['sqlite://' + DB_URL]
        model.hub.threadConnection.close()
        model.db_disconnect()
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)

    def test_create_message(self):
        mail_sender = MailSender()
        model.db_connect()
        account11 = IMAPAccount(user_jid="test1@test.com",
                                name="account11",
                                jid="account11@jmc.test.com")
        account11.online_action = MailAccount.RETRIEVE
        account11.status = account.ONLINE
        message = mail_sender.create_message(account11, ("from@test.com",
                                                         "subject",
                                                         "message body"))
        self.assertEquals(message.get_to(), account11.user_jid)
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
        account11 = IMAPAccount(user_jid="test1@test.com",
                                name="account11",
                                jid="account11@jmc.test.com")
        account11.online_action = MailAccount.DIGEST
        account11.status = account.ONLINE
        message = mail_sender.create_message(account11, ("from@test.com",
                                                         "subject",
                                                         "message body"))
        self.assertEquals(message.get_to(), account11.user_jid)
        model.db_disconnect()
        self.assertEquals(message.get_subject(), "subject")
        self.assertEquals(message.get_body(), "message body")
        self.assertEquals(message.get_type(), "headline")

class MailHandler_TestCase(unittest.TestCase):
    def setUp(self):
        self.handler = MailHandler(None)
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        model.db_connection_str = 'sqlite://' + DB_URL
        model.db_connect()
        Account.createTable(ifNotExists=True)
        SMTPAccount.createTable(ifNotExists=True)
        model.db_disconnect()

    def tearDown(self):
        model.db_connect()
        SMTPAccount.dropTable(ifExists=True)
        Account.dropTable(ifExists=True)
        del TheURIOpener.cachedURIs['sqlite://' + DB_URL]
        model.hub.threadConnection.close()
        model.db_disconnect()
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)

    def test_filter(self):
        model.db_connect()
        account11 = SMTPAccount(user_jid="user1@test.com",
                                name="account11",
                                jid="account11@jcl.test.com")
        account11.default_account = True
        account12 = SMTPAccount(user_jid="user1@test.com",
                                name="account12",
                                jid="account12@jcl.test.com")
        message = Message(from_jid="user1@test.com",
                          to_jid="user2%test.com@jcl.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertNotEquals(accounts, None)
        self.assertEquals(accounts.count(), 1)
        self.assertEquals(accounts[0].name, "account11")
        model.db_disconnect()

    def test_filter_root(self):
        model.db_connect()
        account11 = SMTPAccount(user_jid="user1@test.com",
                                name="account11",
                                jid="account11@jcl.test.com")
        account11.default_account = True
        account12 = SMTPAccount(user_jid="user1@test.com",
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
        account11 = SMTPAccount(user_jid = "user1@test.com", \
                                   name = "account11", \
                                   jid = "account11@jcl.test.com")
        account12 = SMTPAccount(user_jid = "user1@test.com", \
                                   name = "account12", \
                                   jid = "account12@jcl.test.com")
        message = Message(from_jid = "user1@test.com", \
                             to_jid = "user2%test.com@jcl.test.com", \
                             body = "message")
        accounts = self.handler.filter(message, None)
        self.assertNotEquals(accounts, None)
        self.assertEquals(accounts.count(), 2)
        self.assertEquals(accounts[0].name, "account11")
        model.db_disconnect()

    def test_filter_wrong_dest(self):
        model.db_connect()
        account11 = SMTPAccount(user_jid = "user1@test.com", \
                                   name = "account11", \
                                   jid = "account11@jcl.test.com")
        account12 = SMTPAccount(user_jid = "user1@test.com", \
                                   name = "account12", \
                                   jid = "account12@jcl.test.com")
        message = Message(from_jid = "user1@test.com", \
                             to_jid = "user2test.com@jcl.test.com", \
                             body = "message")
        accounts = self.handler.filter(message, None)
        self.assertEquals(accounts, None)
        model.db_disconnect()

    def test_filter_wrong_account(self):
        model.db_connect()
        account11 = SMTPAccount(user_jid="user1@test.com",
                                name="account11",
                                jid="account11@jcl.test.com")
        account12 = SMTPAccount(user_jid="user1@test.com",
                                name="account12",
                                jid="account12@jcl.test.com")
        message = Message(from_jid="user3@test.com",
                          to_jid="user2%test.com@jcl.test.com",
                          body="message")
        try:
            accounts = self.handler.filter(message, None)
            model.db_disconnect()
        except NoAccountError, e:
           self.assertNotEquals(e, None)
           return
        finally:
           model.db_disconnect()
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
        MailHandler_TestCase.setUp(self)
        self.handler = MailSubscribeHandler(None)
        model.db_connect()
        LegacyJID.createTable(ifNotExists=True)
        model.db_disconnect()

    def test_handle(self):
        model.db_connect()
        account11 = SMTPAccount(user_jid="user1@test.com",
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
        MailHandler_TestCase.setUp(self)
        self.handler = MailUnsubscribeHandler(None)
        model.db_connect()
        LegacyJID.createTable(ifNotExists=True)
        model.db_disconnect()

    def test_handle(self):
        model.db_connect()
        account11 = SMTPAccount(user_jid="user1@test.com",
                                name="account11",
                                jid="account11@jcl.test.com")
        account12 = SMTPAccount(user_jid="user1@test.com",
                                name="account12",
                                jid="account12@jcl.test.com")
        account2 = SMTPAccount(user_jid="user2@test.com",
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

class MailFeederHandler_TestCase(unittest.TestCase):
    def setUp(self):
        self.handler = MailFeederHandler(FeederMock(), SenderMock())
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        model.db_connection_str = 'sqlite://' + DB_URL
        model.db_connect()
        Account.createTable(ifNotExists=True)
        PresenceAccount.createTable(ifNotExists=True)
        MailAccount.createTable(ifNotExists=True)
        IMAPAccount.createTable(ifNotExists=True)
        POP3Account.createTable(ifNotExists=True)
        SMTPAccount.createTable(ifNotExists=True)
        model.db_disconnect()

    def tearDown(self):
        self.handler = None
        model.db_connect()
        SMTPAccount.dropTable(ifExists=True)
        IMAPAccount.dropTable(ifExists=True)
        POP3Account.dropTable(ifExists=True)
        MailAccount.dropTable(ifExists=True)
        PresenceAccount.dropTable(ifExists=True)
        Account.dropTable(ifExists=True)
        del TheURIOpener.cachedURIs['sqlite://' + DB_URL]
        model.hub.threadConnection.close()
        model.db_disconnect()
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)

    def test_filter(self):
        model.db_connect()
        account11 = SMTPAccount(user_jid="user1@test.com",
                                name="account11",
                                jid="account11@jcl.test.com")
        account13 = IMAPAccount(user_jid="user3@test.com",
                                name="account13",
                                jid="account13@jcl.test.com")
        account12 = POP3Account(user_jid="user2@test.com",
                                name="account12",
                                jid="account12@jcl.test.com")
        accounts = self.handler.filter(None, None)
        # SQLObject > 0.8 is needed
        self.assertEquals(accounts.count(), 2)
        self.assertEquals(accounts[0].name, "account12")
        self.assertEquals(accounts[1].name, "account13")
        model.db_disconnect()

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MailComponent_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(SendMailMessageHandler_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(RootSendMailMessageHandler_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(MailSender_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(MailHandler_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(MailUnsubscribeHandler_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(MailSubscribeHandler_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(MailPresenceHandler_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(MailFeederHandler_TestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
