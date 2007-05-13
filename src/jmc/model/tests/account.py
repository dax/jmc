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
import os
import thread
import sys

from sqlobject import *
from sqlobject.dbconnection import TheURIOpener

from jcl.model import account
from jcl.model.account import Account, PresenceAccount
from jmc.model.account import MailAccount, POP3Account, IMAPAccount

from jcl.model.tests.account import PresenceAccount_TestCase
from jmc.model.tests import email_generator, server

if sys.platform == "win32":
   DB_PATH = "/c|/temp/test.db"
else:
   DB_PATH = "/tmp/test.db"
DB_URL = DB_PATH # + "?debug=1&debugThreading=1"

class MailAccount_TestCase(PresenceAccount_TestCase):
    def setUp(self):
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        account.hub.threadConnection = connectionForURI('sqlite://' + DB_URL)
        Account.createTable(ifNotExists = True)
        PresenceAccount.createTable(ifNotExists = True)
        MailAccount.createTable(ifNotExists = True)
        self.account = MailAccount(user_jid = "user1@test.com", \
                                   name = "account1", \
                                   jid = "account1@jmc.test.com")
        del account.hub.threadConnection
        self.account_class = MailAccount

    def tearDown(self):
        account.hub.threadConnection = connectionForURI('sqlite://' + DB_URL)
        MailAccount.dropTable(ifExists = True)
        PresenceAccount.dropTable(ifExists = True)
        Account.dropTable(ifExists = True)
        del TheURIOpener.cachedURIs['sqlite://' + DB_URL]
        account.hub.threadConnection.close()
        del account.hub.threadConnection
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)

    def make_test(email_type, tested_func, expected_res):
        def inner(self):
            encoded, multipart, header = email_type
            email = email_generator.generate(encoded, \
                                             multipart, \
                                             header)
            part = tested_func(self, email)
            self.assertEquals(part, expected_res)
        return inner

    test_get_decoded_part_not_encoded = \
        make_test((False, False, False), \
                  lambda self, email: self.account.get_decoded_part(email, None), \
                  u"Not encoded single part")

    test_get_decoded_part_encoded = \
        make_test((True, False, False), \
                  lambda self, email: self.account.get_decoded_part(email, None), \
                  u"Encoded single part with 'iso-8859-15' charset (éàê)")

    test_format_message_summary_not_encoded = \
        make_test((False, False, True), \
                  lambda self, email: self.account.format_message_summary(email), \
                  (u"From : not encoded from\nSubject : not encoded subject\n\n", \
                   u"not encoded from"))

    test_format_message_summary_encoded = \
        make_test((True, False, True), \
                  lambda self, email: self.account.format_message_summary(email), \
                  (u"From : encoded from (éàê)\nSubject : encoded subject " + \
                   u"(éàê)\n\n", \
                   u"encoded from (éàê)"))

    test_format_message_summary_partial_encoded = \
        make_test((True, False, True), \
                  lambda self, email: \
                  email.replace_header("Subject", \
                                       "\" " + str(email["Subject"]) \
                                       + " \" not encoded part") or \
                  email.replace_header("From", \
                                       "\" " + str(email["From"]) \
                                       + " \" not encoded part") or \
                  self.account.format_message_summary(email), \
                  (u"From : \"encoded from (éàê)\" not encoded part\nSubject " + \
                   u": \"encoded subject (éàê)\" not encoded part\n\n", \
                   u"\"encoded from (éàê)\" not encoded part"))

    test_format_message_single_not_encoded = \
        make_test((False, False, True), \
                  lambda self, email: self.account.format_message(email), \
                  (u"From : not encoded from\nSubject : not encoded subject" + \
                   u"\n\nNot encoded single part\n", \
                   u"not encoded from"))

    test_format_message_single_encoded = \
        make_test((True, False, True), \
                  lambda self, email: self.account.format_message(email), \
                  (u"From : encoded from (éàê)\nSubject : encoded subject " + \
                   u"(éàê)\n\nEncoded single part with 'iso-8859-15' charset" + \
                   u" (éàê)\n", \
                   u"encoded from (éàê)"))

    test_format_message_multi_not_encoded = \
        make_test((False, True, True), \
                  lambda self, email: self.account.format_message(email), \
                  (u"From : not encoded from\nSubject : not encoded subject" + \
                   u"\n\nNot encoded multipart1\nNot encoded multipart2\n", \
                   u"not encoded from"))

    test_format_message_multi_encoded = \
        make_test((True, True, True), \
                  lambda self, email: self.account.format_message(email), \
                  (u"From : encoded from (éàê)\nSubject : encoded subject (éà" + \
                   u"ê)\n\nutf-8 multipart1 with no charset (éàê)" + \
                   u"\nEncoded multipart2 with 'iso-8859-15' charset (éàê)\n" + \
                   u"Encoded multipart3 with no charset (éàê)\n", \
                   u"encoded from (éàê)"))

    def test_get_register_fields(self):
        register_fields = MailAccount.get_register_fields()
        self.assertEquals(len(register_fields), 14)

class POP3Account_TestCase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        account.hub.threadConnection = connectionForURI('sqlite://' + DB_URL)
        Account.createTable(ifNotExists = True)
        PresenceAccount.createTable(ifNotExists = True)
        MailAccount.createTable(ifNotExists = True)
        POP3Account.createTable(ifNotExists = True)
        self.pop3_account = POP3Account(user_jid = "user1@test.com", \
                                       name = "account1", \
                                       jid = "account1@jmc.test.com", \
                                       login = "login")
        self.pop3_account.password = "pass"
        self.pop3_account.host = "localhost"
        self.pop3_account.port = 1110
        self.pop3_account.ssl = False
        del account.hub.threadConnection
        
    def tearDown(self):
        account.hub.threadConnection = connectionForURI('sqlite://' + DB_URL)
        POP3Account.dropTable(ifExists = True)
        MailAccount.dropTable(ifExists = True)
        PresenceAccount.dropTable(ifExists = True)
        Account.dropTable(ifExists = True)
        del TheURIOpener.cachedURIs['sqlite://' + DB_URL]
        account.hub.threadConnection.close()
        del account.hub.threadConnection
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        self.server = None
        self.pop3_account = None

    def make_test(responses = None, queries = None, core = None):
        def inner(self):
            self.server = server.DummyServer("localhost", 1110)
            thread.start_new_thread(self.server.serve, ())
            self.server.responses = ["+OK connected\r\n", \
                                     "+OK name is a valid mailbox\r\n", \
                                     "+OK pass\r\n"]
            if responses:
                self.server.responses += responses
            self.server.queries = ["USER login\r\n", \
                                   "PASS pass\r\n"]
            if queries:
                self.server.queries += queries
            self.server.queries += ["QUIT\r\n"]
            self.pop3_account.connect()
            self.failUnless(self.pop3_account.connection, \
                            "Cannot establish connection")
            if core:
                account.hub.threadConnection = connectionForURI('sqlite://' + DB_URL)
                core(self)
                del account.hub.threadConnection
            self.pop3_account.disconnect()
            self.failUnless(self.server.verify_queries(), \
                            "Sended queries does not match expected queries.")
        return inner

    test_connection = make_test()
    
    test_get_mail_list = \
        make_test(["+OK 2 20\r\n"], \
                  ["STAT\r\n"], \
                  lambda self: \
                  self.assertEquals(self.pop3_account.get_mail_list(), \
                                    ["1", "2"]))

    test_get_mail_summary = \
        make_test(["+OK 10 octets\r\n" + \
                   "From: user@test.com\r\n" + \
                   "Subject: subject test\r\n\r\n" + \
                   "mymessage\r\n.\r\n",
                   "+OK\r\n"], \
                  ["RETR 1\r\n",
                   "RSET\r\n"], \
                  lambda self: \
                  self.assertEquals(self.pop3_account.get_mail_summary(1), \
                                    (u"From : user@test.com\n" + \
                                     u"Subject : subject test\n\n", \
                                     u"user@test.com")))

    test_get_mail = \
        make_test(["+OK 10 octets\r\n" + \
                   "From: user@test.com\r\n" + \
                   "Subject: subject test\r\n\r\n" + \
                   "mymessage\r\n.\r\n",
                   "+OK\r\n"], \
                  ["RETR 1\r\n",
                   "RSET\r\n"], \
                  lambda self: \
                  self.assertEquals(self.pop3_account.get_mail(1), \
                                    (u"From : user@test.com\n" + \
                                     u"Subject : subject test\n\n" + \
                                     u"mymessage\n", \
                                     u"user@test.com")))

    test_unsupported_reset_command_get_mail_summary = \
        make_test(["+OK 10 octets\r\n" + \
                   "From: user@test.com\r\n" + \
                   "Subject: subject test\r\n\r\n" + \
                   "mymessage\r\n.\r\n",
                   "-ERR unknown command\r\n"], \
                  ["RETR 1\r\n",
                   "RSET\r\n"], \
                  lambda self: \
                  self.assertEquals(self.pop3_account.get_mail_summary(1), \
                                    (u"From : user@test.com\n" + \
                                     u"Subject : subject test\n\n", \
                                     u"user@test.com")))

    test_unsupported_reset_command_get_mail = \
        make_test(["+OK 10 octets\r\n" + \
                   "From: user@test.com\r\n" + \
                   "Subject: subject test\r\n\r\n" + \
                   "mymessage\r\n.\r\n",
                   "-ERR unknown command\r\n"], \
                  ["RETR 1\r\n",
                   "RSET\r\n"], \
                  lambda self: \
                  self.assertEquals(self.pop3_account.get_mail(1), \
                                    (u"From : user@test.com\n" + \
                                     u"Subject : subject test\n\n" + \
                                     u"mymessage\n", \
                                     u"user@test.com")))

    def test_get_register_fields(self):
        register_fields = POP3Account.get_register_fields()
        self.assertEquals(len(register_fields), 14)

class IMAPAccount_TestCase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        account.hub.threadConnection = connectionForURI('sqlite://' + DB_URL)
        Account.createTable(ifNotExists = True)
        PresenceAccount.createTable(ifNotExists = True)
        MailAccount.createTable(ifNotExists = True)
        IMAPAccount.createTable(ifNotExists = True)
        self.imap_account = IMAPAccount(user_jid = "user1@test.com", \
                                       name = "account1", \
                                       jid = "account1@jmc.test.com", \
                                       login = "login")
        self.imap_account.password = "pass"
        self.imap_account.host = "localhost"
        self.imap_account.port = 1143
        self.imap_account.ssl = False
        del account.hub.threadConnection

    def tearDown(self):
        account.hub.threadConnection = connectionForURI('sqlite://' + DB_URL)
        IMAPAccount.dropTable(ifExists = True)
        MailAccount.dropTable(ifExists = True)
        PresenceAccount.dropTable(ifExists = True)
        Account.dropTable(ifExists = True)
        del TheURIOpener.cachedURIs['sqlite://' + DB_URL]
        account.hub.threadConnection.close()
        del account.hub.threadConnection
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        self.server = None
        self.imap_account = None

    def make_test(responses = None, queries = None, core = None):
        def inner(self):
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
            self.imap_account.connect()
            self.failUnless(self.imap_account.connection, \
                            "Cannot establish connection")
            if core:
                account.hub.threadConnection = connectionForURI('sqlite://' + DB_URL)
                core(self)
                del account.hub.threadConnection
            self.imap_account.disconnect()
            self.failUnless(self.server.verify_queries())
        return inner
            
    test_connection = make_test()

    test_get_mail_list = make_test([lambda data: "* 42 EXISTS\n* 1 RECENT\n* OK" +\
                                    " [UNSEEN 9]\n* FLAGS (\Deleted \Seen\*)\n*" +\
                                    " OK [PERMANENTFLAGS (\Deleted \Seen\*)\n" + \
                                    data.split()[0] + \
                                    " OK [READ-WRITE] SELECT completed\n", \
                                    lambda data: "* SEARCH 9 10 \n" + \
                                    data.split()[0] + " OK SEARCH completed\n"], \
                                   ["^[^ ]* SELECT INBOX", \
                                    "^[^ ]* SEARCH RECENT"], \
                                   lambda self: \
                                   self.assertEquals(self.imap_account.get_mail_list(), ['9', '10']))

    test_get_mail_summary = make_test([lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" +\
                                       " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" +\
                                       " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                                       data.split()[0] + \
                                       " OK [READ-WRITE] SELECT completed\r\n", \
                                       lambda data: "* 1 FETCH ((RFC822) {12}\r\nbody" + \
                                       " text\r\n)\r\n" + \
                                       data.split()[0] + " OK FETCH completed\r\n"], \
                                      ["^[^ ]* EXAMINE INBOX", \
                                       "^[^ ]* FETCH 1 \(RFC822\)"], \
                                      lambda self: self.assertEquals(self.imap_account.get_mail_summary(1), \
                                                                     (u"From : None\nSubject : None\n\n", \
                                                                      u"None")))

    test_get_mail = make_test([lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" +\
                               " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" +\
                               " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                               data.split()[0] + \
                               " OK [READ-WRITE] SELECT completed\r\n", \
                               lambda data: "* 1 FETCH ((RFC822) {11}\r\nbody" + \
                               " text\r\n)\r\n" + \
                               data.split()[0] + " OK FETCH completed\r\n"], \
                              ["^[^ ]* EXAMINE INBOX", \
                               "^[^ ]* FETCH 1 \(RFC822\)",], \
                              lambda self: self.assertEquals(self.imap_account.get_mail(1), \
                                                             (u"From : None\nSubject : None\n\nbody text\r\n\n", \
                                                              u"None")))
        
    def test_get_register_fields(self):
        register_fields = IMAPAccount.get_register_fields()
        self.assertEquals(len(register_fields), 15)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MailAccount_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(POP3Account_TestCase, 'test'))
    suite.addTest(unittest.makeSuite(IMAPAccount_TestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
