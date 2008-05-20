##
## message.py
## Login : <dax@happycoders.org>
## Started on  Tue Nov  6 19:00:22 2007 David Rousselie
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
import re

from pyxmpp.message import Message

from jcl.tests import JCLTestCase
from jcl.model.account import Account, User

from jmc.model.account import GlobalSMTPAccount, AbstractSMTPAccount, \
    SMTPAccount
from jmc.jabber.message import SendMailMessageHandler, \
    RootSendMailMessageHandler
from jmc.lang import Lang

class MockSMTPAccount(object):
    def __init__(self):
        self.email_sent = 0
        self.default_from = "user1@test.com"
        self.email = None

    def send_email(self, email):
        self.email = email
        self.email_sent += 1

    def create_email(self, from_addr, to_addr, subject, body,
                     other_headers=None):
        return (from_addr, to_addr, subject, body, other_headers)

class SendMailMessageHandler_TestCase(unittest.TestCase):
    def setUp(self):
        self.handler = SendMailMessageHandler(None)

    def test_get_email_to_headers_from_message(self):
        to_regexp = re.compile("^\s*(?i)to\s*:\s*(?P<to_email>.*)")
        (message, to_header) = self.handler.get_email_headers_from_message(\
            "To: dest@test.com\ntest body\n", [to_regexp], ["to_email"])
        self.assertEquals(message, "test body\n")
        self.assertEquals(to_header, ["dest@test.com"])

    def test_get_email_headers_from_message(self):
        to_regexp = re.compile("^\s*(?i)to\s*:\s*(?P<to_email>.*)")
        cc_regexp = re.compile("^\s*(?i)cc\s*:\s*(?P<cc_email>.*)")
        bcc_regexp = re.compile("^\s*(?i)bcc\s*:\s*(?P<bcc_email>.*)")
        subject_regexp = re.compile("^\s*(?i)subject\s*:\s*(?P<subject_email>.*)")
        (message, headers) = self.handler.get_email_headers_from_message(\
            "To: dest@test.com\nCc: cc@test.com\n"
            + "Bcc: bcc@test.com\n"
            + "Subject: test subject\ntest body\n",
            [to_regexp, cc_regexp, bcc_regexp, subject_regexp],
            ["to_email", "cc_email", "bcc_email", "subject_email"])
        self.assertEquals(message, "test body\n")
        self.assertEquals(headers, ["dest@test.com",
                                    "cc@test.com",
                                    "bcc@test.com",
                                    "test subject"])

    def test_get_email_headers_from_message_unordered(self):
        to_regexp = re.compile("^\s*(?i)to\s*:\s*(?P<to_email>.*)")
        cc_regexp = re.compile("^\s*(?i)cc\s*:\s*(?P<cc_email>.*)")
        bcc_regexp = re.compile("^\s*(?i)bcc\s*:\s*(?P<bcc_email>.*)")
        subject_regexp = re.compile("^\s*(?i)subject\s*:\s*(?P<subject_email>.*)")
        (message, headers) = self.handler.get_email_headers_from_message(\
            "To: dest@test.com\nCc: cc@test.com\n"
            + "Bcc: bcc@test.com\n"
            + "Subject: test subject\ntest body\n",
            [cc_regexp, to_regexp, subject_regexp, bcc_regexp],
            ["cc_email", "to_email", "subject_email", "bcc_email"])
        self.assertEquals(message, "test body\n")
        self.assertEquals(headers, ["cc@test.com",
                                    "dest@test.com",
                                    "test subject",
                                    "bcc@test.com"])

    def test_handle(self):
        mock_account = MockSMTPAccount()
        message = Message(from_jid="user1@test.com",
                          to_jid="real_dest%test.com@jmc.test.com",
                          subject="real subject",
                          body="To: dest@test.com\nCc: cc@test.com\n" \
                              + "Bcc: bcc@test.com\n" \
                              + "Subject: test subject\ntest body\n")
        result = self.handler.handle(\
            message, Lang.en, [mock_account])
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0].stanza_type, "message")
        self.assertEquals(result[0].get_from(), "real_dest%test.com@jmc.test.com")
        self.assertEquals(result[0].get_to(), "user1@test.com")
        self.assertEquals(result[0].get_subject(),
                          Lang.en.send_mail_ok_subject)
        self.assertEquals(result[0].get_body(),
                          Lang.en.send_mail_ok_body % \
                              ("real_dest@test.com, dest@test.com"))
        self.assertEquals(mock_account.email_sent, 1)
        self.assertEquals(mock_account.email[0], "user1@test.com")
        self.assertEquals(mock_account.email[1], "real_dest@test.com, dest@test.com")
        self.assertEquals(mock_account.email[2], "real subject")
        self.assertEquals(mock_account.email[3], "test body\n")
        self.assertEquals(mock_account.email[4], {u"Bcc": "bcc@test.com",
                                                  u"Cc": "cc@test.com"})

class RootSendMailMessageHandler_TestCase(JCLTestCase):
    def setUp(self):
        JCLTestCase.setUp(self, tables=[Account, GlobalSMTPAccount,
                                        AbstractSMTPAccount,
                                        SMTPAccount, User])
        self.handler = RootSendMailMessageHandler(None)

    def test_filter(self):
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jmc.test.com")
        account11.default_account = True
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jmc.test.com")
        message = Message(from_jid="user1@test.com",
                          to_jid="account11@jmc.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertEquals(accounts.count(), 1)

    def test_filter_no_default_account(self):
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jmc.test.com")
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jmc.test.com")
        message = Message(from_jid="user1@test.com",
                          to_jid="account11@jmc.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertEquals(accounts.count(), 2)
        self.assertEquals(accounts[0].name, "account11")

    def test_filter_wrong_dest(self):
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jmc.test.com")
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jmc.test.com")
        message = Message(from_jid="user1@test.com",
                          to_jid="user2%test.com@jmc.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertEquals(accounts.count(), 2)

    def test_filter_wrong_user(self):
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jmc.test.com")
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jmc.test.com")
        message = Message(from_jid="user2@test.com",
                          to_jid="account11@jmc.test.com",
                          body="message")
        accounts = self.handler.filter(message, None)
        self.assertEquals(accounts.count(), 0)

    def test_handle(self):
        mock_account = MockSMTPAccount()
        message = Message(from_jid="user1@test.com",
                          to_jid="jmc.test.com",
                          subject="real subject",
                          body="To: dest@test.com\nCc: cc@test.com\n" \
                              + "Bcc: bcc@test.com\n" \
                              + "Subject: test subject\ntest body\n")
        result = self.handler.handle(\
            message, Lang.en, [mock_account])
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0].get_type(), None)
        self.assertEquals(result[0].get_from(), "jmc.test.com")
        self.assertEquals(result[0].get_to(), "user1@test.com")
        self.assertEquals(result[0].get_subject(),
                          Lang.en.send_mail_ok_subject)
        self.assertEquals(result[0].get_body(),
                          Lang.en.send_mail_ok_body % ("dest@test.com"))
        self.assertEquals(mock_account.email_sent, 1)
        self.assertEquals(mock_account.email[0], "user1@test.com")
        self.assertEquals(mock_account.email[1], "dest@test.com")
        self.assertEquals(mock_account.email[2], "real subject")
        self.assertEquals(mock_account.email[3], "test body\n")
        self.assertEquals(mock_account.email[4], {u"Bcc": "bcc@test.com",
                                                  u"Cc": "cc@test.com"})

    def test_handle_email_not_found_in_header(self):
        message = Message(from_jid="user1@test.com",
                          to_jid="jmc.test.com",
                          subject="message subject",
                          body="message body")
        accounts = [MockSMTPAccount()]
        result = self.handler.handle(message, Lang.en, accounts)
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0].get_type(), "error")
        self.assertEquals(result[0].get_from(), "jmc.test.com")
        self.assertEquals(result[0].get_to(), "user1@test.com")
        self.assertEquals(result[0].get_subject(),
                          Lang.en.send_mail_error_no_to_header_subject)
        self.assertEquals(result[0].get_body(),
                          Lang.en.send_mail_error_no_to_header_body)

    def test_handle_no_jabber_subject(self):
        mock_account = MockSMTPAccount()
        message = Message(from_jid="user1@test.com",
                          to_jid="jmc.test.com",
                          subject="",
                          body="To: dest@test.com\nCc: cc@test.com\n" \
                              + "Bcc: bcc@test.com\n" \
                              + "Subject: test subject\ntest body\n")
        message_to_send = self.handler.handle(\
            message, Lang.en, [mock_account])
        self.assertNotEquals(message_to_send, None)
        self.assertEquals(mock_account.email_sent, 1)
        self.assertEquals(mock_account.email[0], "user1@test.com")
        self.assertEquals(mock_account.email[1], "dest@test.com")
        self.assertEquals(mock_account.email[2], "test subject")
        self.assertEquals(mock_account.email[3], "test body\n")
        self.assertEquals(mock_account.email[4], {u"Bcc": "bcc@test.com",
                                                  u"Cc": "cc@test.com"})

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(SendMailMessageHandler_TestCase, 'test'))
    test_suite.addTest(unittest.makeSuite(RootSendMailMessageHandler_TestCase, 'test'))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
