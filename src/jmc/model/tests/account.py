# -*- coding: utf-8 -*-
##
## test_account.py
## Login : <dax@happycoders.org>
## Started on  Wed Feb 14 08:23:17 2007 David Rousselie
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
import thread

from jcl.tests import JCLTestCase
import jcl.model as model
from jcl.model.account import Account, PresenceAccount, User
from jmc.model.account import MailAccount, POP3Account, IMAPAccount, SMTPAccount
from jmc.lang import Lang

from jcl.model.tests.account import Account_TestCase, \
    PresenceAccount_TestCase, InheritableAccount_TestCase, \
    ExampleAccount
from jmc.model.tests import email_generator, server

class MailAccount_TestCase(PresenceAccount_TestCase):
    def setUp(self):
        PresenceAccount_TestCase.setUp(self, tables=[MailAccount])
        self.account = MailAccount(user=User(jid="user1@test.com"),
                                   name="account1",
                                   jid="account1@jmc.test.com")
        self.account_class = MailAccount

    def make_test(email_type, tested_func, expected_res):
        def inner(self):
            encoded, multipart, header = email_type
            email = email_generator.generate(encoded,
                                             multipart,
                                             header)
            part = tested_func(self, email)
            self.assertEquals(part, expected_res)
        return inner

    test_get_decoded_part_not_encoded = \
        make_test((False, False, False), \
                  lambda self, email: \
                      self.account.get_decoded_part(email, None),
                  u"Not encoded single part")

    test_get_decoded_part_encoded = \
        make_test((True, False, False),
                  lambda self, email: \
                      self.account.get_decoded_part(email, None),
                  u"Encoded single part with 'iso-8859-15' charset (éàê)")

    test_format_message_summary_not_encoded = \
        make_test((False, False, True),
                  lambda self, email: \
                      self.account.format_message_summary(email),
                  (u"From : not encoded from\nSubject : not encoded subject\n\n",
                   u"not encoded from"))

    test_format_message_summary_encoded = \
        make_test((True, False, True),
                  lambda self, email: \
                      self.account.format_message_summary(email),
                  (u"From : encoded from (éàê)\nSubject : encoded subject " + \
                       u"(éàê)\n\n",
                   u"encoded from (éàê)"))

    test_format_message_summary_partial_encoded = \
        make_test((True, False, True),
                  lambda self, email: \
                      email.replace_header("Subject",
                                           "\" " + str(email["Subject"]) \
                                               + " \" not encoded part") or \
                      email.replace_header("From",
                                           "\" " + str(email["From"]) \
                                               + " \" not encoded part") or \
                  self.account.format_message_summary(email),
                  (u"From : \"encoded from (éàê)\" not encoded part\nSubject " + \
                       u": \"encoded subject (éàê)\" not encoded part\n\n",
                   u"\"encoded from (éàê)\" not encoded part"))

    test_format_message_single_not_encoded = \
        make_test((False, False, True),
                  lambda self, email: \
                      self.account.format_message(email),
                  (u"From : not encoded from\nSubject : not encoded subject" + \
                       u"\n\nNot encoded single part\n",
                   u"not encoded from"))

    test_format_message_single_encoded = \
        make_test((True, False, True),
                  lambda self, email: \
                      self.account.format_message(email),
                  (u"From : encoded from (éàê)\nSubject : encoded subject " + \
                       u"(éàê)\n\nEncoded single part with 'iso-8859-15' charset" + \
                       u" (éàê)\n",
                   u"encoded from (éàê)"))

    test_format_message_multi_not_encoded = \
        make_test((False, True, True),
                  lambda self, email: \
                      self.account.format_message(email),
                  (u"From : not encoded from\nSubject : not encoded subject" + \
                       u"\n\nNot encoded multipart1\nNot encoded multipart2\n",
                   u"not encoded from"))

    test_format_message_multi_encoded = \
        make_test((True, True, True),
                  lambda self, email: \
                      self.account.format_message(email),
                  (u"From : encoded from (éàê)\nSubject : encoded subject (éà" + \
                       u"ê)\n\nutf-8 multipart1 with no charset (éàê)" + \
                       u"\nEncoded multipart2 with 'iso-8859-15' charset (éàê)\n" + \
                       u"Encoded multipart3 with no charset (éàê)\n",
                   u"encoded from (éàê)"))

    def test_get_default_status_msg(self):
        """
        Get default status message for MailAccount.
        Should raise NotImplementedError because get_type() method
        is not implemented
        """
        try:
            self.account.get_default_status_msg(Lang.en)
        except NotImplementedError:
            return
        fail("No NotImplementedError raised")

class POP3Account_TestCase(InheritableAccount_TestCase):
    def setUp(self):
        JCLTestCase.setUp(self, tables=[Account, PresenceAccount, User,
                                        MailAccount, POP3Account])
        self.pop3_account = POP3Account(user=User(jid="user1@test.com"),
                                        name="account1",
                                        jid="account1@jmc.test.com",
                                        login="login")
        self.pop3_account.password = "pass"
        self.pop3_account.host = "localhost"
        self.pop3_account.port = 1110
        self.pop3_account.ssl = False
        model.db_disconnect()
        self.account_class = POP3Account

    def make_test(responses=None, queries=None, core=None):
        def inner(self):
            self.server = server.DummyServer("localhost", 1110)
            thread.start_new_thread(self.server.serve, ())
            self.server.responses = ["+OK connected\r\n",
                                     "+OK name is a valid mailbox\r\n",
                                     "+OK pass\r\n"]
            if responses:
                self.server.responses += responses
            self.server.queries = ["USER login\r\n",
                                   "PASS pass\r\n"]
            if queries:
                self.server.queries += queries
            self.server.queries += ["QUIT\r\n"]
            self.pop3_account.connect()
            self.failUnless(self.pop3_account.connection,
                            "Cannot establish connection")
            if core:
                model.db_connect()
                core(self)
                model.db_disconnect()
            self.pop3_account.disconnect()
            self.failUnless(self.server.verify_queries(),
                            "Sended queries does not match expected queries.")
        return inner

    test_connection = make_test

    test_get_mail_list_summary = \
        make_test(["+OK 2 20\r\n",
                   "+OK 10 octets\r\n" + \
                       "From: user@test.com\r\n" + \
                       "Subject: mail subject 1\r\n.\r\n",
                   "+OK 10 octets\r\n" + \
                       "From: user@test.com\r\n" + \
                       "Subject: mail subject 2\r\n.\r\n",
                   "+OK\r\n"],
                  ["STAT\r\n",
                   "TOP 1 0\r\n",
                   "TOP 2 0\r\n",
                   "RSET\r\n"],
                  lambda self: \
                      self.assertEquals(self.pop3_account.get_mail_list_summary(),
                                        [("1", "mail subject 1"),
                                         ("2", "mail subject 2")]))

    test_get_mail_list_summary_start_index = \
        make_test(["+OK 3 30\r\n",
                   "+OK 10 octets\r\n" + \
                       "From: user@test.com\r\n" + \
                       "Subject: mail subject 2\r\n.\r\n",
                   "+OK 10 octets\r\n" + \
                       "From: user@test.com\r\n" + \
                       "Subject: mail subject 3\r\n.\r\n",
                   "+OK\r\n"],
                  ["STAT\r\n",
                   "TOP 2 0\r\n",
                   "TOP 3 0\r\n",
                   "RSET\r\n"],
                  lambda self: \
                      self.assertEquals(self.pop3_account.get_mail_list_summary(start_index=2),
                                        [("2", "mail subject 2"),
                                         ("3", "mail subject 3")]))

    test_get_mail_list_summary_end_index = \
        make_test(["+OK 3 30\r\n",
                   "+OK 10 octets\r\n" + \
                       "From: user@test.com\r\n" + \
                       "Subject: mail subject 1\r\n.\r\n",
                   "+OK 10 octets\r\n" + \
                       "From: user@test.com\r\n" + \
                       "Subject: mail subject 2\r\n.\r\n",
                   "+OK\r\n"],
                  ["STAT\r\n",
                   "TOP 1 0\r\n",
                   "TOP 2 0\r\n",
                   "RSET\r\n"],
                  lambda self: \
                      self.assertEquals(self.pop3_account.get_mail_list_summary(end_index=2),
                                        [("1", "mail subject 1"),
                                         ("2", "mail subject 2")]))

    test_get_new_mail_list = \
        make_test(["+OK 2 20\r\n"],
                  ["STAT\r\n"],
                  lambda self: \
                      self.assertEquals(self.pop3_account.get_new_mail_list(),
                                        ["1", "2"]))

    test_get_mail_summary = \
        make_test(["+OK 10 octets\r\n" + \
                       "From: user@test.com\r\n" + \
                       "Subject: subject test\r\n\r\n" + \
                       "mymessage\r\n.\r\n",
                   "+OK\r\n"],
                  ["RETR 1\r\n",
                   "RSET\r\n"],
                  lambda self: \
                      self.assertEquals(self.pop3_account.get_mail_summary(1),
                                        (u"From : user@test.com\n" + \
                                             u"Subject : subject test\n\n",
                                         u"user@test.com")))

    test_get_mail = \
        make_test(["+OK 10 octets\r\n" + \
                       "From: user@test.com\r\n" + \
                       "Subject: subject test\r\n\r\n" + \
                       "mymessage\r\n.\r\n",
                   "+OK\r\n"],
                  ["RETR 1\r\n",
                   "RSET\r\n"],
                  lambda self: \
                      self.assertEquals(self.pop3_account.get_mail(1),
                                        (u"From : user@test.com\n" + \
                                             u"Subject : subject test\n\n" + \
                                             u"mymessage\n",
                                         u"user@test.com")))

    test_unsupported_reset_command_get_mail_summary = \
        make_test(["+OK 10 octets\r\n" + \
                       "From: user@test.com\r\n" + \
                       "Subject: subject test\r\n\r\n" + \
                       "mymessage\r\n.\r\n",
                   "-ERR unknown command\r\n"],
                  ["RETR 1\r\n",
                   "RSET\r\n"],
                  lambda self: \
                      self.assertEquals(self.pop3_account.get_mail_summary(1),
                                        (u"From : user@test.com\n" + \
                                             u"Subject : subject test\n\n",
                                         u"user@test.com")))

    test_unsupported_reset_command_get_mail = \
        make_test(["+OK 10 octets\r\n" + \
                       "From: user@test.com\r\n" + \
                       "Subject: subject test\r\n\r\n" + \
                       "mymessage\r\n.\r\n",
                   "-ERR unknown command\r\n"],
                  ["RETR 1\r\n",
                   "RSET\r\n"],
                  lambda self: \
                      self.assertEquals(self.pop3_account.get_mail(1),
                                        (u"From : user@test.com\n" + \
                                             u"Subject : subject test\n\n" + \
                                             u"mymessage\n",
                                         u"user@test.com")))

    def test_get_next_mail_index_empty(self):
        """
        Test get_next_mail_index with empty mail_list parameter.
        """
        mail_list = []
        self.pop3_account.nb_mail = 0
        self.pop3_account.lastmail = 0
        result = []
        for elt in self.pop3_account.get_next_mail_index(mail_list):
            result.append(elt)
        self.assertEquals(result, [])

    def test_get_next_mail_index(self):
        """
        Test get_next_mail_index first check.
        """
        mail_list = [1, 2, 3, 4]
        self.pop3_account.nb_mail = 4
        self.pop3_account.lastmail = 0
        result = []
        for elt in self.pop3_account.get_next_mail_index(mail_list):
            result.append(elt)
        self.assertEquals(result, [1, 2, 3, 4])
        self.assertEquals(self.pop3_account.lastmail, 4)

    def test_get_next_mail_index_second_check(self):
        """
        Test get_next_mail_index second check (no parallel checking).
        """
        mail_list = [1, 2, 3, 4, 5, 6, 7, 8]
        self.pop3_account.nb_mail = 8
        self.pop3_account.lastmail = 4
        result = []
        for elt in self.pop3_account.get_next_mail_index(mail_list):
            result.append(elt)
        self.assertEquals(result, [5, 6, 7, 8])
        self.assertEquals(self.pop3_account.lastmail, 8)

    def test_get_next_mail_index_second_check_parallel_check(self):
        """
        Test get_next_mail_index second check (with parallel checking
        but not more new emails than last index jmc stopped:
        3 new emails after another client checked emails).
        """
        mail_list = [1, 2, 3]
        self.pop3_account.nb_mail = 3
        self.pop3_account.lastmail = 4
        result = []
        for elt in self.pop3_account.get_next_mail_index(mail_list):
            result.append(elt)
        self.assertEquals(result, [1, 2, 3])
        self.assertEquals(self.pop3_account.lastmail, 3)

    def test_get_next_mail_index_second_check_bug_parallel_check(self):
        """
        Test get_next_mail_index second check (with parallel checking
        but with more new emails than last index jmc stopped:
        5 new emails after another client checked emails). Cannot make
        the difference with one new email since last jmc email check!!
        """
        mail_list = [1, 2, 3, 4, 5]
        self.pop3_account.nb_mail = 5
        self.pop3_account.lastmail = 4
        result = []
        for elt in self.pop3_account.get_next_mail_index(mail_list):
            result.append(elt)
        # with no bug it should be:
        # self.assertEquals(result, [1, 2, 3, 4, 5])
        self.assertEquals(result, [5])
        self.assertEquals(self.pop3_account.lastmail, 5)

    def test_get_default_status_msg(self):
        """
        Get default status message for POP3Account.
        """
        status_msg = self.pop3_account.get_default_status_msg(Lang.en)
        self.assertEquals(status_msg, "pop3://login@localhost:1110")

    def test_get_default_status_msg_ssl(self):
        """
        Get default status message for SSL POP3Account.
        """
        self.pop3_account.ssl = True
        status_msg = self.pop3_account.get_default_status_msg(Lang.en)
        self.assertEquals(status_msg, "pop3s://login@localhost:1110")

class IMAPAccount_TestCase(InheritableAccount_TestCase):
    def setUp(self):
        JCLTestCase.setUp(self, tables=[Account, PresenceAccount, User,
                                        MailAccount, IMAPAccount])
        self.imap_account = IMAPAccount(user=User(jid="user1@test.com"),
                                        name="account1",
                                        jid="account1@jmc.test.com",
                                        login="login")
        self.imap_account.password = "pass"
        self.imap_account.host = "localhost"
        self.imap_account.port = 1143
        self.imap_account.ssl = False
        self.account_class = IMAPAccount

    def make_test(self, responses=None, queries=None, core=None):
        def inner():
            self.server = server.DummyServer("localhost", 1143)
            thread.start_new_thread(self.server.serve, ())
            self.server.responses = ["* OK [CAPABILITY IMAP4 LOGIN-REFERRALS " + \
                                     "AUTH=PLAIN]\n", \
                                     lambda data: "* CAPABILITY IMAP4 " + \
                                     "LOGIN-REFERRALS AUTH=PLAIN\n" + \
                                     data.split()[0] + \
                                     " OK CAPABILITY completed\n", \
                                     lambda data: data.split()[0] + \
                                     " OK LOGIN completed\n"]
            if responses:
                self.server.responses += responses
            self.server.queries = ["^[^ ]* CAPABILITY", \
                                   "^[^ ]* LOGIN login \"pass\""]
            if queries:
                self.server.queries += queries
            self.server.queries += ["^[^ ]* LOGOUT"]
            if not self.imap_account.connected:
                self.imap_account.connect()
            self.failUnless(self.imap_account.connection, \
                            "Cannot establish connection")
            if core:
                model.db_connect()
                core(self)
                model.db_disconnect()
            if self.imap_account.connected:
                self.imap_account.disconnect()
            self.failUnless(self.server.verify_queries())
        return inner

    def test_connection(self):
        test_func = self.make_test()
        test_func()

    def test_get_mail_list_summary(self):
        test_func = self.make_test(\
            [lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" +\
                 " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" +\
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                 data.split()[0] + \
                 " OK [READ-WRITE] SELECT completed\r\n",
             lambda data: "* 1 FETCH ((RFC822.header) {38}\r\n" + \
                 "Subject: mail subject 1\r\n\r\nbody text\r\n)\r\n" + \
                 "* 2 FETCH ((RFC822.header) {38}\r\n" + \
                 "Subject: mail subject 2\r\n\r\nbody text\r\n)\r\n" + \
                 data.split()[0] + " OK FETCH completed\r\n"],
            ["^[^ ]* EXAMINE INBOX",
             "^[^ ]* FETCH 1:20 RFC822.header"],
            lambda self: \
                self.assertEquals(self.imap_account.get_mail_list_summary(),
                                  [('1', 'mail subject 1'),
                                   ('2', 'mail subject 2')]))
        test_func()

    def test_get_mail_list_summary_inbox_does_not_exist(self):
        self.__test_select_inbox_does_not_exist(\
            lambda: self.imap_account.get_mail_list_summary(), readonly=True)

    def test_get_mail_list_summary_start_index(self):
        test_func = self.make_test(\
            [lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" +\
                 " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" +\
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                 data.split()[0] + \
                 " OK [READ-WRITE] SELECT completed\r\n",
             lambda data: "* 2 FETCH ((RFC822.header) {38}\r\n" + \
                 "Subject: mail subject 2\r\n\r\nbody text\r\n)\r\n" + \
                 "* 3 FETCH ((RFC822.header) {38}\r\n" + \
                 "Subject: mail subject 3\r\n\r\nbody text\r\n)\r\n" + \
                 data.split()[0] + " OK FETCH completed\r\n"],
            ["^[^ ]* EXAMINE INBOX",
             "^[^ ]* FETCH 2:20 RFC822.header"],
            lambda self: \
                self.assertEquals(self.imap_account.get_mail_list_summary(start_index=2),
                                  [('2', 'mail subject 2'),
                                   ('3', 'mail subject 3')]))
        test_func()

    def test_get_mail_list_summary_end_index(self):
        test_func = self.make_test(\
            [lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" +\
                 " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" +\
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                 data.split()[0] + \
                 " OK [READ-WRITE] SELECT completed\r\n",
             lambda data: "* 1 FETCH ((RFC822.header) {38}\r\n" + \
                 "Subject: mail subject 1\r\n\r\nbody text\r\n)\r\n" + \
                 "* 2 FETCH ((RFC822.header) {38}\r\n" + \
                 "Subject: mail subject 2\r\n\r\nbody text\r\n)\r\n" + \
                 data.split()[0] + " OK FETCH completed\r\n"],
            ["^[^ ]* EXAMINE INBOX",
             "^[^ ]* FETCH 1:2 RFC822.header"],
            lambda self: \
                self.assertEquals(self.imap_account.get_mail_list_summary(end_index=2),
                                  [('1', 'mail subject 1'),
                                   ('2', 'mail subject 2')]))
        test_func()

    def test_get_new_mail_list(self):
        test_func = self.make_test(\
            [lambda data: "* 42 EXISTS\n* 1 RECENT\n* OK" + \
                 " [UNSEEN 9]\n* FLAGS (\Deleted \Seen\*)\n*" + \
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\n" + \
                 data.split()[0] + \
                 " OK [READ-WRITE] SELECT completed\n",
             lambda data: "* SEARCH 9 10 \n" + \
                 data.split()[0] + " OK SEARCH completed\n"],
            ["^[^ ]* SELECT INBOX",
             "^[^ ]* SEARCH RECENT"],
            lambda self: \
                self.assertEquals(self.imap_account.get_new_mail_list(),
                                  ['9', '10']))
        test_func()

    def __test_select_inbox_does_not_exist(self, tested_func,
                                           exception_message="Mailbox does not exist",
                                           readonly=False):
        def check_func(self):
            try:
                tested_func()
            except Exception, e:
                self.assertEquals(e.message, exception_message)
                return
            self.fail("No exception raised when selecting non existing mailbox")
        test_func = self.make_test(\
            [lambda data: "* 42 EXISTS\n* 1 RECENT\n* OK" + \
                 " [UNSEEN 9]\n* FLAGS (\Deleted \Seen\*)\n*" + \
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\n" + \
                 data.split()[0] + \
                 " NO Mailbox does not exist \n"],
            ["^[^ ]* " + (readonly and "EXAMINE" or "SELECT") + " INBOX"],
            check_func)
        test_func()

    def test_get_new_mail_list_inbox_does_not_exist(self):
        self.__test_select_inbox_does_not_exist(\
            lambda: self.imap_account_get_new_mail_list())

    def test_get_new_mail_list_delimiter1(self):
        self.imap_account.mailbox = "INBOX/dir1/subdir2"
        self.imap_account.delimiter = "."
        test_func = self.make_test( \
            [lambda data: "* 42 EXISTS\n* 1 RECENT\n* OK" + \
                 " [UNSEEN 9]\n* FLAGS (\Deleted \Seen\*)\n*" + \
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\n" + \
                 data.split()[0] + \
                 " OK [READ-WRITE] SELECT completed\n",
             lambda data: "* SEARCH 9 10 \n" + \
                 data.split()[0] + " OK SEARCH completed\n"],
            ["^[^ ]* SELECT \"?INBOX\.dir1\.subdir2\"?",
             "^[^ ]* SEARCH RECENT"],
            lambda self: \
                self.assertEquals(self.imap_account.get_new_mail_list(),
                                  ['9', '10']))
        test_func()

    def test_get_new_mail_list_delimiter2(self):
        self.imap_account.mailbox = "INBOX/dir1/subdir2"
        self.imap_account.delimiter = "/"
        test_func = self.make_test( \
            [lambda data: "* 42 EXISTS\n* 1 RECENT\n* OK" + \
                 " [UNSEEN 9]\n* FLAGS (\Deleted \Seen\*)\n*" + \
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\n" + \
                 data.split()[0] + \
                 " OK [READ-WRITE] SELECT completed\n",
             lambda data: "* SEARCH 9 10 \n" + \
                 data.split()[0] + " OK SEARCH completed\n"],
            ["^[^ ]* SELECT \"?INBOX/dir1/subdir2\"?",
             "^[^ ]* SEARCH RECENT"],
            lambda self: \
                self.assertEquals(self.imap_account.get_new_mail_list(),
                                  ['9', '10']))
        test_func()

    def test_get_mail_summary(self):
        test_func = self.make_test(\
            [lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" +\
                 " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" +\
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                 data.split()[0] + \
                 " OK [READ-WRITE] SELECT completed\r\n",
             lambda data: "* 1 FETCH ((RFC822) {12}\r\nbody" + \
                 " text\r\n)\r\n" + \
                 data.split()[0] + " OK FETCH completed\r\n"],
            ["^[^ ]* EXAMINE INBOX",
             "^[^ ]* FETCH 1 \(RFC822.header\)"],
            lambda self: \
                self.assertEquals(self.imap_account.get_mail_summary(1),
                                  (u"From : None\nSubject : None\n\n",
                                   u"None")))
        test_func()

    def test_get_mail_summary_inbox_does_not_exist(self):
        self.__test_select_inbox_does_not_exist(\
            lambda: self.imap_account.get_mail_summary(1),
            "Mailbox does not exist (email 1)", True)

    def test_get_new_mail_list_inbox_does_not_exist(self):
        def check_func(self):
            try:
                self.imap_account.get_new_mail_list()
            except Exception, e:
                self.assertEquals(e.message, "Mailbox does not exist")
                return
            self.fail("No exception raised when selecting non existing mailbox")
        test_func = self.make_test(\
            [lambda data: "* 42 EXISTS\n* 1 RECENT\n* OK" + \
                 " [UNSEEN 9]\n* FLAGS (\Deleted \Seen\*)\n*" + \
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\n" + \
                 data.split()[0] + \
                 " NO Mailbox does not exist \n"],
            ["^[^ ]* SELECT INBOX"],
            check_func)
        test_func()

    def test_get_mail_summary_delimiter(self):
        self.imap_account.mailbox = "INBOX/dir1/subdir2"
        self.imap_account.delimiter = "."
        test_func = self.make_test(\
            [lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" +\
                 " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" +\
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                 data.split()[0] + \
                 " OK [READ-WRITE] SELECT completed\r\n",
             lambda data: "* 1 FETCH ((RFC822) {12}\r\nbody" + \
                 " text\r\n)\r\n" + \
                 data.split()[0] + " OK FETCH completed\r\n"],
            ["^[^ ]* EXAMINE \"?INBOX\.dir1\.subdir2\"?",
             "^[^ ]* FETCH 1 \(RFC822.header\)"],
            lambda self: \
                self.assertEquals(self.imap_account.get_mail_summary(1),
                                  (u"From : None\nSubject : None\n\n",
                                   u"None")))
        test_func()

    def test_get_mail(self):
        test_func = self.make_test(\
            [lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" + \
                 " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" + \
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                 data.split()[0] + \
                 " OK [READ-WRITE] SELECT completed\r\n",
             lambda data: "* 1 FETCH ((RFC822) {11}\r\nbody" + \
                 " text\r\n)\r\n" + \
                 data.split()[0] + " OK FETCH completed\r\n"],
            ["^[^ ]* EXAMINE INBOX",
             "^[^ ]* FETCH 1 \(RFC822\)"],
            lambda self: \
                self.assertEquals(self.imap_account.get_mail(1),
                                  (u"From : None\nSubject : None\n\nbody text\r\n\n",
                                   u"None")))
        test_func()

    def test_get_mail_inbox_does_not_exist(self):
        self.__test_select_inbox_does_not_exist(\
            lambda: self.imap_account.get_mail(1),
            "Mailbox does not exist (email 1)", True)

    def test_get_mail_delimiter(self):
        self.imap_account.mailbox = "INBOX/dir1/subdir2"
        self.imap_account.delimiter = "."
        test_func = self.make_test(\
            [lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" + \
                 " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" + \
                 " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                 data.split()[0] + \
                 " OK [READ-WRITE] SELECT completed\r\n",
             lambda data: "* 1 FETCH ((RFC822) {11}\r\nbody" + \
                 " text\r\n)\r\n" + \
                 data.split()[0] + " OK FETCH completed\r\n"],
            ["^[^ ]* EXAMINE \"?INBOX\.dir1\.subdir2\"?",
             "^[^ ]* FETCH 1 \(RFC822\)"],
            lambda self: \
                self.assertEquals(self.imap_account.get_mail(1),
                                  (u"From : None\nSubject : None\n\nbody text\r\n\n",
                                   u"None")))
        test_func()

    def test_build_folder_cache(self):
        test_func = self.make_test(\
        [lambda data: '* LIST () "." "INBOX"\r\n' + \
         '* LIST () "." "INBOX.dir1"\r\n' + \
         '* LIST () "." "INBOX.dir1.subdir1"\r\n' + \
         '* LIST () "." "INBOX.dir1.subdir2"\r\n' + \
         '* LIST () "." "INBOX.dir2"\r\n' + \
         data.split()[0] + ' OK LIST completed\r\n'],
        ["^[^ ]* LIST \"\" \*"],
        lambda self: self.assertEquals(self.imap_account._build_folder_cache(),
                                       {"INBOX":
                                        {"dir1":
                                         {"subdir1": {},
                                          "subdir2": {}},
                                         "dir2": {}}}))
        test_func()

    def test_ls_dir_base(self):
        self.test_build_folder_cache()
        self.assertEquals(self.imap_account.ls_dir(""),
                          ["INBOX"])

    def test_ls_dir_subdir(self):
        self.test_build_folder_cache()
        result = self.imap_account.ls_dir("INBOX")
        result.sort()
        self.assertEquals(result,
                          ["dir1", "dir2"])

    def test_ls_dir_subsubdir_delim1(self):
        self.test_build_folder_cache()
        self.imap_account.default_delimiter = "."
        result = self.imap_account.ls_dir("INBOX/dir1")
        result.sort()
        self.assertEquals(result,
                          ["subdir1", "subdir2"])

    def test_ls_dir_subsubdir_delim2(self):
        self.test_build_folder_cache()
        result = self.imap_account.ls_dir("INBOX/dir1")
        result.sort()
        self.assertEquals(result,
                          ["subdir1", "subdir2"])

    def test_populate_handler(self):
        self.assertEquals(".", self.imap_account.delimiter)
        self.imap_account.mailbox = "INBOX.dir1.subdir2"
        def call_func(self):
            self.imap_account.populate_handler()
            self.assertEquals("INBOX/dir1/subdir2", self.imap_account.mailbox)
        test_func = self.make_test(\
            [lambda data: '* LIST () "." "INBOX.dir1.subdir2"\r\n' + \
                 data.split()[0] + ' OK LIST completed\r\n'],
            ["^[^ ]* LIST \"?INBOX.dir1.subdir2\"? \*"],
            call_func)
        test_func()

    def test_populate_handler_wrong_mailbox(self):
        self.assertEquals(".", self.imap_account.delimiter)
        self.imap_account.mailbox = "INBOX.dir1.subdir2"
        def call_func(self):
            try:
                self.imap_account.populate_handler()
            except Exception, e:
                return
            self.fail("Exception should have been raised")
        test_func = self.make_test(\
            [lambda data: data.split()[0] + ' ERR LIST completed\r\n'],
            ["^[^ ]* LIST \"?INBOX.dir1.subdir2\"? \*"],
            call_func)
        test_func()

    def check_get_next_mail_index(self, mail_list):
        """
        Common tests for get_next_mail_index method.
        """
        result = []
        original_mail_list = [elt for elt in mail_list]
        for elt in self.imap_account.get_next_mail_index(mail_list):
            result.append(elt)
        self.assertEquals(mail_list, [])
        self.assertEquals(result, original_mail_list)

    def test_get_next_mail_index_empty(self):
        """
        Test get_next_mail_index with empty mail_list parameter.
        """
        mail_list = []
        self.check_get_next_mail_index(mail_list)

    def test_get_next_mail_index(self):
        """
        Test get_next_mail_index.
        """
        mail_list = [1, 2, 3, 4]
        self.check_get_next_mail_index(mail_list)

    def test_get_default_status_msg(self):
        """
        Get default status message for IMAPAccount.
        """
        status_msg = self.imap_account.get_default_status_msg(Lang.en)
        self.assertEquals(status_msg, "imap://login@localhost:1143")

    def test_get_default_status_msg_ssl(self):
        """
        Get default status message for SSL IMAPAccount.
        """
        self.imap_account.ssl = True
        status_msg = self.imap_account.get_default_status_msg(Lang.en)
        self.assertEquals(status_msg, "imaps://login@localhost:1143")

class SMTPAccount_TestCase(Account_TestCase):
    def setUp(self):
        JCLTestCase.setUp(self, tables=[Account, ExampleAccount, User,
                                        SMTPAccount])
        self.account_class = SMTPAccount

    def test_default_account_post_func_no_default_true(self):
        model.db_connect()
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jmc.test.com")
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jmc.test.com")
        (name, field_type, field_options, post_func, default_func) = \
            SMTPAccount.get_register_fields()[7]
        value = post_func("True", None, "user1@test.com")
        self.assertTrue(value)
        model.db_disconnect()

    def test_default_account_post_func_no_default_false(self):
        model.db_connect()
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jmc.test.com")
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jmc.test.com")
        (name, field_type, field_options, post_func, default_func) = \
            SMTPAccount.get_register_fields()[7]
        value = post_func("False", None, "user1@test.com")
        self.assertTrue(value)
        model.db_disconnect()

    def test_default_account_post_func_true(self):
        model.db_connect()
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jmc.test.com")
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jmc.test.com")
        account12.default_account = True
        (name, field_type, field_options, post_func, default_func) = \
            SMTPAccount.get_register_fields()[7]
        value = post_func("True", None, "user1@test.com")
        self.assertTrue(value)
        self.assertFalse(account12.default_account)
        model.db_disconnect()

    def test_default_account_post_func_false(self):
        model.db_connect()
        user1 = User(jid="user1@test.com")
        account11 = SMTPAccount(user=user1,
                                name="account11",
                                jid="account11@jmc.test.com")
        account12 = SMTPAccount(user=user1,
                                name="account12",
                                jid="account12@jmc.test.com")
        account12.default_account = True
        (name, field_type, field_options, post_func, default_func) = \
            SMTPAccount.get_register_fields()[7]
        value = post_func("False", None, "user1@test.com")
        self.assertFalse(value)
        self.assertTrue(account12.default_account)
        model.db_disconnect()

    def test_create_email(self):
        model.db_connect()
        account11 = SMTPAccount(user=User(jid="user1@test.com"),
                                name="account11",
                                jid="account11@jmc.test.com")
        model.db_disconnect()
        email = account11.create_email("from@test.com",
                                       "to@test.com",
                                       "subject",
                                       "body")
        self.assertEqual(email['From'], "from@test.com")
        self.assertEqual(email['To'], "to@test.com")
        self.assertEqual(email['Subject'], "subject")
        self.assertEqual(email.get_payload(), "body")

    def test_create_email_other_headers(self):
        model.db_connect()
        account11 = SMTPAccount(user=User(jid="user1@test.com"),
                                name="account11",
                                jid="account11@jmc.test.com")
        model.db_disconnect()
        email = account11.create_email("from@test.com",
                                       "to@test.com",
                                       "subject",
                                       "body",
                                       {"Bcc": "bcc@test.com",
                                        "Cc": "cc@test.com"})
        self.assertEqual(email['From'], "from@test.com")
        self.assertEqual(email['To'], "to@test.com")
        self.assertEqual(email['Subject'], "subject")
        self.assertEqual(email['Bcc'], "bcc@test.com")
        self.assertEqual(email['Cc'], "cc@test.com")
        self.assertEqual(email.get_payload(), "body")

    def make_test(self, responses=None, queries=None, core=None):
        def inner():
            self.server = server.DummyServer("localhost", 1025)
            thread.start_new_thread(self.server.serve, ())
            self.server.responses = []
            if responses:
                self.server.responses += responses
            self.server.responses += ["221 localhost closing connection\r\n"]
            self.server.queries = []
            if queries:
                self.server.queries += queries
            self.server.queries += ["quit\r\n"]
            if core:
                model.db_connect()
                core(self)
                model.db_disconnect()
            self.failUnless(self.server.verify_queries())
        return inner

    def test_send_email_esmtp_no_auth(self):
        model.db_connect()
        smtp_account = SMTPAccount(user=User(jid="user1@test.com"),
                                   name="account11",
                                   jid="account11@jmc.test.com")
        smtp_account.host = "localhost"
        smtp_account.port = 1025
        model.db_disconnect()
        email = smtp_account.create_email("from@test.com",
                                          "to@test.com",
                                          "subject",
                                          "body")
        test_func = self.make_test(["220 localhost ESMTP\r\n",
                                    "250-localhost Hello 127.0.0.1\r\n"
                                    + "250-SIZE 52428800\r\n"
                                    + "250-PIPELINING\r\n"
                                    + "250 HELP\r\n",
                                    "250 OK\r\n",
                                    "250 Accepted\r\n",
                                    "354 Enter message\r\n",
                                    None, None, None, None,
                                    None, None, None, None,
                                    "250 OK\r\n"],
                                   ["ehlo \[127.0...1\]\r\n",
                                    "mail FROM:<" + str(email['From']) + ">.*",
                                    "rcpt TO:<" + str(email['To']) + ">\r\n",
                                    "data\r\n"] +
                                   email.as_string().split("\n") + [".\r\n"],
                                   lambda self: \
                                       smtp_account.send_email(email))
        test_func()

    def test_send_email_no_auth(self):
        model.db_connect()
        smtp_account = SMTPAccount(user=User(jid="user1@test.com"),
                                   name="account11",
                                   jid="account11@jmc.test.com")
        smtp_account.host = "localhost"
        smtp_account.port = 1025
        model.db_disconnect()
        email = smtp_account.create_email("from@test.com",
                                          "to@test.com",
                                          "subject",
                                          "body")
        test_func = self.make_test(["220 localhost SMTP\r\n",
                                    "504 ESMTP not supported\r\n",
                                    "250-localhost Hello 127.0.0.1\r\n"
                                    + "250-SIZE 52428800\r\n"
                                    + "250-PIPELINING\r\n"
                                    + "250 HELP\r\n",
                                    "250 OK\r\n",
                                    "250 Accepted\r\n",
                                    "354 Enter message\r\n",
                                    None, None, None, None,
                                    None, None, None, None,
                                    "250 OK\r\n"],
                                   ["ehlo \[127.0...1\]\r\n",
                                    "helo \[127.0...1\]\r\n",
                                    "mail FROM:<" + str(email['From']) + ">.*",
                                    "rcpt TO:<" + str(email['To']) + ">\r\n",
                                    "data\r\n"] +
                                   email.as_string().split("\n") + [".\r\n"],
                                   lambda self: \
                                       smtp_account.send_email(email))
        test_func()

    def test_send_email_esmtp_auth(self):
        model.db_connect()
        smtp_account = SMTPAccount(user=User(jid="user1@test.com"),
                                   name="account11",
                                   jid="account11@jmc.test.com")
        smtp_account.host = "localhost"
        smtp_account.port = 1025
        smtp_account.login = "user"
        smtp_account.password = "pass"
        model.db_disconnect()
        email = smtp_account.create_email("from@test.com",
                                          "to@test.com",
                                          "subject",
                                          "body")
        test_func = self.make_test(["220 localhost ESMTP\r\n",
                                    "250-localhost Hello 127.0.0.1\r\n"
                                    + "250-SIZE 52428800\r\n"
                                    + "250-AUTH PLAIN LOGIN CRAM-MD5\r\n"
                                    + "250-PIPELINING\r\n"
                                    + "250 HELP\r\n",
                                    "334 ZGF4IDNmNDM2NzY0YzBhNjgyMTQ1MzhhZGNiMjE2YTYxZjRm\r\n",
                                    "235 Authentication succeeded\r\n",
                                    "250 OK\r\n",
                                    "250 Accepted\r\n",
                                    "354 Enter message\r\n",
                                    None, None, None, None,
                                    None, None, None, None,
                                    "250 OK\r\n"],
                                   ["ehlo \[127.0...1\]\r\n",
                                    "AUTH CRAM-MD5\r\n",
                                    ".*\r\n",
                                    "mail FROM:<" + str(email['From']) + ">.*",
                                    "rcpt TO:<" + str(email['To']) + ">\r\n",
                                    "data\r\n"] +
                                   email.as_string().split("\n") + [".\r\n"],
                                   lambda self: \
                                       smtp_account.send_email(email))
        test_func()

    def test_send_email_esmtp_auth_method2(self):
        model.db_connect()
        smtp_account = SMTPAccount(user=User(jid="user1@test.com"),
                                   name="account11",
                                   jid="account11@jmc.test.com")
        smtp_account.host = "localhost"
        smtp_account.port = 1025
        smtp_account.login = "user"
        smtp_account.password = "pass"
        model.db_disconnect()
        email = smtp_account.create_email("from@test.com",
                                          "to@test.com",
                                          "subject",
                                          "body")
        test_func = self.make_test(["220 localhost ESMTP\r\n",
                                    "250-localhost Hello 127.0.0.1\r\n"
                                    + "250-SIZE 52428800\r\n"
                                    + "250-AUTH PLAIN LOGIN CRAM-MD5\r\n"
                                    + "250-PIPELINING\r\n"
                                    + "250 HELP\r\n",
                                    "334 ZGF4IDNmNDM2NzY0YzBhNjgyMTQ1MzhhZGNiMjE2YTYxZjRm\r\n",
                                    "535 Incorrect Authentication data\r\n",
                                    "334 asd235r4\r\n",
                                    "235 Authentication succeeded\r\n",
                                    "250 OK\r\n",
                                    "250 Accepted\r\n",
                                    "354 Enter message\r\n",
                                    None, None, None, None,
                                    None, None, None, None,
                                    "250 OK\r\n"],
                                   ["ehlo \[127.0...1\]\r\n",
                                    "AUTH CRAM-MD5\r\n",
                                    ".*\r\n",
                                    "AUTH LOGIN .*\r\n",
                                    ".*\r\n",
                                    "mail FROM:<" + str(email['From']) + ">.*",
                                    "rcpt TO:<" + str(email['To']) + ">\r\n",
                                    "data\r\n"] +
                                   email.as_string().split("\n") + [".\r\n"],
                                   lambda self: \
                                       smtp_account.send_email(email))
        test_func()

    def test_get_default_status_msg(self):
        """
        Get default status message for IMAPAccount.
        """
        smtp_account = SMTPAccount(user=User(jid="user1@test.com"),
                                   name="account11",
                                   jid="account11@jmc.test.com")
        smtp_account.host = "localhost"
        smtp_account.port = 1025
        smtp_account.login = "user"
        smtp_account.password = "pass"
        status_msg = smtp_account.get_default_status_msg(Lang.en)
        self.assertEquals(status_msg, "smtp://user@localhost:1025")

    def test_get_default_status_msg_ssl(self):
        """
        Get default status message for SSL IMAPAccount.
        """
        smtp_account = SMTPAccount(user=User(jid="user1@test.com"),
                                   name="account11",
                                   jid="account11@jmc.test.com")
        smtp_account.host = "localhost"
        smtp_account.port = 1025
        smtp_account.login = "user"
        smtp_account.password = "pass"
        smtp_account.tls = True
        status_msg = smtp_account.get_default_status_msg(Lang.en)
        self.assertEquals(status_msg, "smtps://user@localhost:1025")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MailAccount_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(POP3Account_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(IMAPAccount_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(SMTPAccount_TestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
