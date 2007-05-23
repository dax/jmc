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

from sqlobject import *

from jcl.tests.runner import JCLRunner_TestCase

from jcl.model import account
from jcl.model.account import Account, PresenceAccount

import jmc
from jmc.runner import JMCRunner
from jmc.model.account import MailAccount, IMAPAccount, POP3Account, SMTPAccount

if sys.platform == "win32":
   DB_PATH = "/c|/temp/test.db"
else:
   DB_PATH = "/tmp/test.db"
DB_URL = "sqlite://" + DB_PATH# + "?debug=1&debugThreading=1"

class JMCRunner_TestCase(JCLRunner_TestCase):
    def setUp(self):
        self.runner = JMCRunner("Jabber Mail Component", jmc.version)

    def tearDown(self):
        self.runner = None
        sys.argv = [""]
        
    def test_configure_default(self):
        self.runner.configure()
        self.assertEquals(self.runner.config_file, None)
        self.assertEquals(self.runner.server, "localhost")
        self.assertEquals(self.runner.port, 5347)
        self.assertEquals(self.runner.secret, "secret")
        self.assertEquals(self.runner.service_jid, "jmc.localhost")
        self.assertEquals(self.runner.language, "en")
        self.assertEquals(self.runner.db_url, "sqlite:///var/spool/jabber/jmc.db")
        self.assertEquals(self.runner.pid_file, "/var/run/jabber/jmc.pid")
        self.assertFalse(self.runner.debug)
        self.assertEquals(self.runner.mail_default_encoding, "iso-8859-1")
        self.assertEquals(self.runner.check_interval, 1)

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
        self.assertEquals(self.runner.check_interval, 2)

    def test_configure_commandline_shortopt(self):
        sys.argv = ["", "-c", "src/jmc/tests/jmc.conf", \
                    "-S", "test2_localhost", \
                    "-P", "43", \
                    "-s", "test2_secret", \
                    "-j", "test2_jmc.localhost", \
                    "-l", "test2_en", \
                    "-u", "sqlite:///tmp/test_jmc.db", \
                    "-p", "/tmp/test_jmc.pid", \
                    "-e", "test2_iso-8859-1", \
                    "-i", "3"]
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
        self.assertEquals(self.runner.check_interval, 3)

    def test_configure_commandline_longopt(self):
        sys.argv = ["", "--config-file", "src/jmc/tests/jmc.conf", \
                    "--server", "test2_localhost", \
                    "--port", "43", \
                    "--secret", "test2_secret", \
                    "--service-jid", "test2_jmc.localhost", \
                    "--language", "test2_en", \
                    "--db-url", "sqlite:///tmp/test_jmc.db", \
                    "--pid-file", "/tmp/test_jmc.pid", \
                    "--mail-default-encoding", "test2_iso-8859-1", \
                    "--check-interval", "4"]
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
        self.assertEquals(self.runner.check_interval, 4)
        
    def test__run(self):
        self.runner.pid_file = "/tmp/jmc.pid"
        self.runner.db_url = DB_URL
        def do_nothing():
            pass
        self.runner._run(do_nothing)
        account.hub.threadConnection = connectionForURI(self.runner.db_url)
        # dropTable should succeed because tables should exist
        Account.dropTable()
        PresenceAccount.dropTable()
        MailAccount.dropTable()
        IMAPAccount.dropTable()
        POP3Account.dropTable()
        SMTPAccount.dropTable()
        del account.hub.threadConnection
        os.unlink(DB_PATH)
        self.assertFalse(os.access("/tmp/jmc.pid", os.F_OK))
        
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(JMCRunner_TestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

