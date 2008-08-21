##
## runner.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Fri May 18 13:43:37 2007 David Rousselie
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
import os

from jcl.tests import JCLTestCase
from jcl.tests.runner import JCLRunner_TestCase

import jcl.model as model
from jcl.model.account import Account, PresenceAccount, User, LegacyJID

import jmc
from jmc.lang import Lang
from jmc.runner import JMCRunner
from jmc.jabber.component import MailComponent
import jmc.model.account as account
from jmc.model.account import MailAccount, IMAPAccount, POP3Account, \
    AbstractSMTPAccount, GlobalSMTPAccount, SMTPAccount

if sys.platform == "win32":
    DB_PATH = "/c|/temp/test.db"
else:
    DB_PATH = "/tmp/test.db"
DB_URL = "sqlite://" + DB_PATH# + "?debug=1&debugThreading=1"

class JMCRunner_TestCase(JCLTestCase):
    def setUp(self):
        JCLTestCase.setUp(self, tables=[Account, PresenceAccount, User,
                                        GlobalSMTPAccount, AbstractSMTPAccount])
        self.runner = JMCRunner("Jabber Mail Component", jmc.version)
        self.smtp_default_login = account.smtp_default_login
        self.smtp_default_password = account.smtp_default_password
        self.smtp_default_host = account.smtp_default_host
        self.smtp_default_port = account.smtp_default_port
        self.smtp_default_tls = account.smtp_default_tls
        self.mail_default_encoding = MailAccount.default_encoding
        self.type_globalsmtp_name = Lang.en.type_globalsmtp_name

    def tearDown(self):
        self.runner = None
        sys.argv = [""]
        account.smtp_default_login = self.smtp_default_login
        account.smtp_default_password = self.smtp_default_password
        account.smtp_default_host = self.smtp_default_host
        account.smtp_default_port = self.smtp_default_port
        account.smtp_default_tls = self.smtp_default_tls
        MailAccount.default_encoding = self.mail_default_encoding
        Lang.en.type_globalsmtp_name = self.type_globalsmtp_name

    def test_configure_default(self):
        self.runner.configure()
        self.assertEquals(self.runner.config_file, "jmc.conf")
        self.assertEquals(self.runner.server, "localhost")
        self.assertEquals(self.runner.port, 5347)
        self.assertEquals(self.runner.secret, "secret")
        self.assertEquals(self.runner.service_jid, "jmc.localhost")
        self.assertEquals(self.runner.language, "en")
        self.assertEquals(self.runner.db_url, "sqlite:///var/spool/jabber/jmc.db")
        self.assertEquals(self.runner.pid_file, "/var/run/jabber/jmc.pid")
        self.assertFalse(self.runner.debug)
        self.assertEquals(self.runner.mail_default_encoding, "iso-8859-1")
        self.assertEquals(self.runner.smtp_default_login, None)
        self.assertEquals(self.runner.smtp_default_password, None)
        self.assertEquals(self.runner.smtp_default_host, None)
        self.assertEquals(self.runner.smtp_default_port, 0)
        self.assertEquals(self.runner.smtp_default_tls, False)
        self.assertEquals(self.runner.enable_smtp_default_account, False)
        self.assertEquals(self.runner.smtp_default_label, None)
        self.runner.setup_smtp_default()
        self.assertEquals(Lang.en.type_globalsmtp_name,
                          "Default SMTP Server")
        _account = GlobalSMTPAccount(user=User(jid="user1@test.com"),
                                     name="account1",
                                     jid="account1@jmc.test.com")
        self.assertEquals(_account.login, '')
        self.assertEquals(_account.password, '')
        self.assertEquals(_account.host, 'localhost')
        self.assertEquals(_account.port, 25)
        self.assertEquals(_account.tls, False)

    def test_configure_configfile(self):
        self.runner.config_file = "src/jmc/tests/jmc.conf"
        self.runner.configure()
        self.assertEquals(self.runner.server, "test_localhost")
        self.assertEquals(self.runner.port, 42)
        self.assertEquals(self.runner.secret, "test_secret")
        self.assertEquals(self.runner.service_jid, "test_jmc.localhost")
        self.assertEquals(self.runner.language, "test_en")
        self.assertEquals(self.runner.db_url, "test_sqlite://root@localhost/var/spool/jabber/test_jmc.db")
        self.assertEquals(self.runner.pid_file, "/var/run/jabber/test_jmc.pid")
        self.assertFalse(self.runner.debug)
        self.assertEquals(self.runner.mail_default_encoding, "test_iso-8859-1")
        self.assertEquals(self.runner.smtp_default_login, "testlogin")
        self.assertEquals(self.runner.smtp_default_password, "testpassword")
        self.assertEquals(self.runner.smtp_default_host, "testhost")
        self.assertEquals(self.runner.smtp_default_port, 2525)
        self.assertEquals(self.runner.smtp_default_tls, True)
        self.assertEquals(self.runner.enable_smtp_default_account, True)
        self.assertEquals(self.runner.smtp_default_label, "SMTP Server")
        self.runner.setup_smtp_default()
        self.assertEquals(Lang.en.type_globalsmtp_name,
                          "SMTP Server")
        _account = GlobalSMTPAccount(user=User(jid="user1@test.com"),
                                     name="account1",
                                     jid="account1@jmc.test.com")
        self.assertEquals(_account.login, 'testlogin')
        self.assertEquals(_account.password, 'testpassword')
        self.assertEquals(_account.host, 'testhost')
        self.assertEquals(_account.port, 2525)
        self.assertEquals(_account.tls, True)

    def test_configure_uncomplete_configfile(self):
        self.runner.config_file = "src/jmc/tests/uncomplete_jmc.conf"
        self.runner.configure()
        self.assertEquals(self.runner.server, "test_localhost")
        self.assertEquals(self.runner.port, 42)
        self.assertEquals(self.runner.secret, "test_secret")
        self.assertEquals(self.runner.service_jid, "test_jmc.localhost")
        self.assertEquals(self.runner.language, "test_en")
        self.assertEquals(self.runner.db_url, "test_sqlite://root@localhost/var/spool/jabber/test_jmc.db")
        self.assertEquals(self.runner.pid_file, "/var/run/jabber/test_jmc.pid")
        self.assertFalse(self.runner.debug)
        self.assertEquals(self.runner.mail_default_encoding, "test_iso-8859-1")
        self.assertEquals(self.runner.smtp_default_login, None)
        self.assertEquals(self.runner.smtp_default_password, None)
        self.assertEquals(self.runner.smtp_default_host, None)
        self.assertEquals(self.runner.smtp_default_port, 0)
        self.assertEquals(self.runner.smtp_default_tls, False)
        self.assertEquals(self.runner.enable_smtp_default_account, False)
        self.assertEquals(self.runner.smtp_default_label, None)
        self.runner.setup_smtp_default()
        self.assertEquals(Lang.en.type_globalsmtp_name,
                          "Default SMTP Server")
        _account = GlobalSMTPAccount(user=User(jid="user1@test.com"),
                                     name="account1",
                                     jid="account1@jmc.test.com")
        self.assertEquals(_account.login, '')
        self.assertEquals(_account.password, '')
        self.assertEquals(_account.host, 'localhost')
        self.assertEquals(_account.port, 25)
        self.assertEquals(_account.tls, False)

    def test_configure_commandline_shortopt(self):
        sys.argv = ["", "-c", "src/jmc/tests/jmc.conf",
                    "-S", "test2_localhost",
                    "-P", "43",
                    "-s", "test2_secret",
                    "-j", "test2_jmc.localhost",
                    "-l", "test2_en",
                    "-u", "sqlite:///tmp/test_jmc.db",
                    "-p", "/tmp/test_jmc.pid",
                    "-e", "test2_iso-8859-1",
                    "-g", "testlogin",
                    "-a", "testpassword",
                    "-t", "testhost",
                    "-r", "2525",
                    "-m", "True",
                    "-n", "True",
                    "-b", "My Global SMTP server"]
        self.runner.configure()
        self.assertEquals(self.runner.server, "test2_localhost")
        self.assertEquals(self.runner.port, 43)
        self.assertEquals(self.runner.secret, "test2_secret")
        self.assertEquals(self.runner.service_jid, "test2_jmc.localhost")
        self.assertEquals(self.runner.language, "test2_en")
        self.assertEquals(self.runner.db_url, "sqlite:///tmp/test_jmc.db")
        self.assertEquals(self.runner.pid_file, "/tmp/test_jmc.pid")
        self.assertFalse(self.runner.debug)
        self.assertEquals(self.runner.mail_default_encoding, "test2_iso-8859-1")
        self.assertEquals(self.runner.smtp_default_login, "testlogin")
        self.assertEquals(self.runner.smtp_default_password, "testpassword")
        self.assertEquals(self.runner.smtp_default_host, "testhost")
        self.assertEquals(self.runner.smtp_default_port, 2525)
        self.assertEquals(self.runner.smtp_default_tls, True)
        self.assertEquals(self.runner.enable_smtp_default_account, True)
        self.assertEquals(self.runner.smtp_default_label, "My Global SMTP server")
        self.runner.setup_smtp_default()
        self.assertEquals(Lang.en.type_globalsmtp_name,
                          "My Global SMTP server")
        _account = GlobalSMTPAccount(user=User(jid="user1@test.com"),
                                     name="account1",
                                     jid="account1@jmc.test.com")
        self.assertEquals(_account.login, 'testlogin')
        self.assertEquals(_account.password, 'testpassword')
        self.assertEquals(_account.host, 'testhost')
        self.assertEquals(_account.port, 2525)
        self.assertEquals(_account.tls, True)

    def test_configure_commandline_longopt(self):
        sys.argv = ["", "--config-file", "src/jmc/tests/jmc.conf",
                    "--server", "test2_localhost",
                    "--port", "43",
                    "--secret", "test2_secret",
                    "--service-jid", "test2_jmc.localhost",
                    "--language", "test2_en",
                    "--db-url", "sqlite:///tmp/test_jmc.db",
                    "--pid-file", "/tmp/test_jmc.pid",
                    "--mail-default-encoding", "test2_iso-8859-1",
                    "--smtp-default-login", "testlogin",
                    "--smtp-default-password", "testpassword",
                    "--smtp-default-host", "testhost",
                    "--smtp-default-port", "2525",
                    "--smtp-default-tls", "True",
                    "--enable-smtp-default-account", "True",
                    "--smtp-default-label", "My Global SMTP server"]
        self.runner.configure()
        self.assertEquals(self.runner.server, "test2_localhost")
        self.assertEquals(self.runner.port, 43)
        self.assertEquals(self.runner.secret, "test2_secret")
        self.assertEquals(self.runner.service_jid, "test2_jmc.localhost")
        self.assertEquals(self.runner.language, "test2_en")
        self.assertEquals(self.runner.db_url, "sqlite:///tmp/test_jmc.db")
        self.assertEquals(self.runner.pid_file, "/tmp/test_jmc.pid")
        self.assertFalse(self.runner.debug)
        self.assertEquals(self.runner.mail_default_encoding, "test2_iso-8859-1")
        self.assertEquals(self.runner.smtp_default_login, "testlogin")
        self.assertEquals(self.runner.smtp_default_password, "testpassword")
        self.assertEquals(self.runner.smtp_default_host, "testhost")
        self.assertEquals(self.runner.smtp_default_port, 2525)
        self.assertEquals(self.runner.smtp_default_tls, True)
        self.assertEquals(self.runner.enable_smtp_default_account, True)
        self.assertEquals(self.runner.smtp_default_label, "My Global SMTP server")
        self.runner.setup_smtp_default()
        self.assertEquals(Lang.en.type_globalsmtp_name,
                          "My Global SMTP server")
        _account = GlobalSMTPAccount(user=User(jid="user1@test.com"),
                                     name="account1",
                                     jid="account1@jmc.test.com")
        self.assertEquals(_account.login, 'testlogin')
        self.assertEquals(_account.password, 'testpassword')
        self.assertEquals(_account.host, 'testhost')
        self.assertEquals(_account.port, 2525)
        self.assertEquals(_account.tls, True)

    def test__run(self):
        self.runner.pid_file = "/tmp/jmc.pid"
        self.runner.db_url = DB_URL
        def do_nothing():
            return (False, 0)
        self.runner._run(do_nothing)
        model.db_connection_str = self.runner.db_url
        model.db_connect()
        # dropTable should succeed because tables should exist
        Account.dropTable()
        PresenceAccount.dropTable()
        User.dropTable()
        LegacyJID.dropTable()
        MailAccount.dropTable()
        IMAPAccount.dropTable()
        POP3Account.dropTable()
        SMTPAccount.dropTable()
        model.db_disconnect()
        os.unlink(DB_PATH)
        self.assertFalse(os.access("/tmp/jmc.pid", os.F_OK))

    def test_run_without_smtp_default_account(self):
        """ """
        def run_func(mail_component_self):
            """ """
            self.assertEquals(mail_component_self.account_manager.account_classes,
                              (IMAPAccount, POP3Account, SMTPAccount))
            return (False, 0)

        self.runner.enable_smtp_default_account = False
        self.runner.pid_file = "/tmp/jmc.pid"
        self.runner.db_url = DB_URL
        self.runner.config = None
        old_run_func = MailComponent.run
        MailComponent.run = run_func
        try:
            self.runner.run()
        finally:
            MailComponent.run = old_run_func
        self.assertFalse(os.access("/tmp/jmc.pid", os.F_OK))

    def test_run_with_smtp_default_account(self):
        """ """
        def run_func(mail_component_self):
            """ """
            self.assertEquals(mail_component_self.account_manager.account_classes,
                              (IMAPAccount, POP3Account, SMTPAccount,
                               GlobalSMTPAccount))
            return (False, 0)

        self.runner.enable_smtp_default_account = True
        self.runner.pid_file = "/tmp/jmc.pid"
        self.runner.db_url = DB_URL
        self.runner.config = None
        old_run_func = MailComponent.run
        MailComponent.run = run_func
        try:
            self.runner.run()
        finally:
            MailComponent.run = old_run_func
        self.assertFalse(os.access("/tmp/jmc.pid", os.F_OK))

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(JMCRunner_TestCase, 'test'))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
