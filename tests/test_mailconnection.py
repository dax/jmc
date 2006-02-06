# -*- coding: utf-8 -*-
##
## mailconnection_test.py
## Login : David Rousselie <david.rousselie@happycoders.org>
## Started on  Fri May 13 11:32:51 2005 David Rousselie
## $Id: test_mailconnection.py,v 1.2 2005/09/18 20:24:07 David Rousselie Exp $
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

import unittest
from jabber.mailconnection import IMAPConnection, \
     POP3Connection, \
     MailConnection
import dummy_server
import email_generator
import thread
import re
import sys
import string

class MailConnection_TestCase(unittest.TestCase):
    def setUp(self):
        self.connection = MailConnection()
            
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
                  lambda self, email: self.connection.get_decoded_part(email, None), \
                  u"Not encoded single part")

    test_get_decoded_part_encoded = \
        make_test((True, False, False), \
                  lambda self, email: self.connection.get_decoded_part(email, None), \
                  u"Encoded single part with 'iso-8859-15' charset (éàê)")

    test_format_message_summary_not_encoded = \
        make_test((False, False, True), \
                  lambda self, email: self.connection.format_message_summary(email), \
                  (u"From : not encoded from\nSubject : not encoded subject\n\n", \
                   u"not encoded from"))

    test_format_message_summary_encoded = \
        make_test((True, False, True), \
                  lambda self, email: self.connection.format_message_summary(email), \
                  (u"From : encoded from (éàê)\nSubject : encoded subject " + \
                   u"(éàê)\n\n", \
                   u"encoded from (éàê)"))

    test_format_message_summary_partial_encoded = \
        make_test((True, False, True), \
                  lambda self, email: \
                  email.replace_header("Subject", \
                                       "\"" + str(email["Subject"]) \
                                       + "\" not encoded part") or \
                  email.replace_header("From", \
                                       "\"" + str(email["From"]) \
                                       + "\" not encoded part") or \
                  self.connection.format_message_summary(email), \
                  (u"From : \"encoded from (éàê)\" not encoded part\nSubject " + \
                   u": \"encoded subject (éàê)\" not encoded part\n\n", \
                   u"\"encoded from (éàê)\" not encoded part"))

    test_format_message_single_not_encoded = \
        make_test((False, False, True), \
                  lambda self, email: self.connection.format_message(email), \
                  (u"From : not encoded from\nSubject : not encoded subject" + \
                   u"\n\nNot encoded single part\n", \
                   u"not encoded from"))

    test_format_message_single_encoded = \
        make_test((True, False, True), \
                  lambda self, email: self.connection.format_message(email), \
                  (u"From : encoded from (éàê)\nSubject : encoded subject " + \
                   u"(éàê)\n\nEncoded single part with 'iso-8859-15' charset" + \
                   u" (éàê)\n", \
                   u"encoded from (éàê)"))

    test_format_message_multi_not_encoded = \
        make_test((False, True, True), \
                  lambda self, email: self.connection.format_message(email), \
                  (u"From : not encoded from\nSubject : not encoded subject" + \
                   u"\n\nNot encoded multipart1\nNot encoded multipart2\n", \
                   u"not encoded from"))

    test_format_message_multi_encoded = \
        make_test((True, True, True), \
                  lambda self, email: self.connection.format_message(email), \
                  (u"From : encoded from (éàê)\nSubject : encoded subject (éà" + \
                   u"ê)\n\nutf-8 multipart1 with no charset (éàê)" + \
                   u"\nEncoded multipart2 with 'iso-8859-15' charset (éàê)\n" + \
                   u"Encoded multipart3 with no charset (éàê)\n", \
                   u"encoded from (éàê)"))


class POP3Connection_TestCase(unittest.TestCase):
    def setUp(self):
        self.server = dummy_server.DummyServer("localhost", 1110)
        thread.start_new_thread(self.server.serve, ())
        self.pop3connection = POP3Connection("login", \
                                             "pass", \
                                             "localhost", \
                                             1110, \
                                             ssl = False)

    def tearDown(self):
        self.server = None
        self.pop3connection = None

    def make_test(responses = None, queries = None, core = None):
        def inner(self):
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
            self.pop3connection.connect()
            self.failUnless(self.pop3connection.connection, \
                            "Cannot establish connection")
            if core:
                core(self)
            self.pop3connection.disconnect()
            self.failUnless(self.server.verify_queries(), \
                            "Sended queries does not match expected queries.")
        return inner

    test_connection = make_test()
    
    test_get_mail_list = \
        make_test(["+OK 2 20\r\n"], \
                  ["STAT\r\n"], \
                  lambda self: \
                  self.assertEquals(self.pop3connection.get_mail_list(), \
                                    ["1", "2"]))

    test_get_mail_summary = \
        make_test(["+OK 10 octets\r\n" + \
                   "From: user@test.com\r\n" + \
                   "Subject: subject test\r\n\r\n" + \
                   "mymessage\r\n.\r\n"], \
                  ["RETR 1\r\n"], \
                  lambda self: \
                  self.assertEquals(self.pop3connection.get_mail_summary(1), \
                                    (u"From : user@test.com\n" + \
                                     u"Subject : subject test\n\n", \
                                     u"user@test.com")))

    test_get_mail = \
        make_test(["+OK 10 octets\r\n" + \
                   "From: user@test.com\r\n" + \
                   "Subject: subject test\r\n\r\n" + \
                   "mymessage\r\n.\r\n"], \
                  ["RETR 1\r\n"], \
                  lambda self: \
                  self.assertEquals(self.pop3connection.get_mail(1), \
                                    (u"From : user@test.com\n" + \
                                     u"Subject : subject test\n\n" + \
                                     u"mymessage\n", \
                                     u"user@test.com")))


class IMAPConnection_TestCase(unittest.TestCase):
    def setUp(self):
        self.server = dummy_server.DummyServer("localhost", 1143)
        thread.start_new_thread(self.server.serve, ())
        self.imap_connection = IMAPConnection("login", \
                                              "pass", \
                                              "localhost", \
                                              1143, \
                                              ssl = False)

    def tearDown(self):
        self.server = None
        self.imap_connection = None

    def make_test(responses = None, queries = None, core = None):
        def inner(self):
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
            self.imap_connection.connect()
            self.failUnless(self.imap_connection.connection, \
                            "Cannot establish connection")
            if core:
                core(self)
            self.imap_connection.disconnect()
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
                                    "^[^ ]* SEARCH UNSEEN"], \
                                   lambda self: \
                                   self.assertEquals(self.imap_connection.get_mail_list(), ['9', '10']))

    test_get_mail_summary = make_test([lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" +\
                                       " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" +\
                                       " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                                       data.split()[0] + \
                                       " OK [READ-WRITE] SELECT completed\r\n", \
                                       lambda data: "* 1 FETCH ((RFC822) {12}\r\nbody" + \
                                       " text\r\n)\r\n" + \
                                       data.split()[0] + " OK FETCH completed\r\n", \
                                       lambda data: "* 1 FETCH (FLAGS (\UNSEEN))\r\n" + \
                                       data.split()[0] + " OK STORE completed\r\n"], \
                                      ["^[^ ]* SELECT INBOX", \
                                       "^[^ ]* FETCH 1 \(RFC822\)", \
                                       "^[^ ]* STORE 1 FLAGS \(UNSEEN\)"], \
                                      lambda self: self.assertEquals(self.imap_connection.get_mail_summary(1), \
                                                                     (u"From : None\nSubject : None\n\n", \
                                                                      u"None")))

    test_get_mail = make_test([lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" +\
                               " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" +\
                               " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                               data.split()[0] + \
                               " OK [READ-WRITE] SELECT completed\r\n", \
                               lambda data: "* 1 FETCH ((RFC822) {11}\r\nbody" + \
                               " text\r\n)\r\n" + \
                               data.split()[0] + " OK FETCH completed\r\n", \
                               lambda data: "* 1 FETCH (FLAGS (\UNSEEN))\r\n" + \
                               data.split()[0] + " OK STORE completed\r\n"], \
                              ["^[^ ]* SELECT INBOX", \
                               "^[^ ]* FETCH 1 \(RFC822\)", \
                               "^[^ ]* STORE 1 FLAGS \(UNSEEN\)"], \
                              lambda self: self.assertEquals(self.imap_connection.get_mail(1), \
                                                             (u"From : None\nSubject : None\n\nbody text\r\n\n", \
                                                              u"None")))
        
