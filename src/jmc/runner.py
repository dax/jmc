##
## runner.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Thu May 17 21:58:32 2007 David Rousselie
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

from jcl.runner import JCLRunner

from jmc.model.account import MailAccount, IMAPAccount, POP3Account, SMTPAccount
from jmc.jabber.component import MailComponent
from jmc.lang import Lang

class JMCRunner(JCLRunner):
    def __init__(self, component_name, component_version):
        JCLRunner.__init__(self, component_name, component_version)
        # define new options
        self.check_interval = 1
        self.mail_default_encoding = "iso-8859-1"
        self.options += [("i:", "check-interval=", "jmc", \
                          " INTERVAL\t\t\tInterval unit in minute between mail checks", \
                          lambda arg: setattr(self, "check_interval", int(arg))), \
                         ("e:", "mail-default-encoding=", "jmc", \
                          " ENCODING\t\tDefault encoding of the component", \
                          lambda arg: setattr(self, "mail_default_encoding", arg))]
        # override JCL default
        self.service_jid = "jmc.localhost"
        self.db_url = "sqlite:///var/spool/jabber/jmc.db"
        self.pid_file = "/var/run/jabber/jmc.pid"
        
    def setup_db(self):
        JCLRunner.setup_db(self)
        MailAccount.createTable(ifNotExists = True)
        IMAPAccount.createTable(ifNotExists = True)
        POP3Account.createTable(ifNotExists = True)
        SMTPAccount.createTable(ifNotExists = True)

    def run(self):
        def run_func():
            component = MailComponent(jid = self.service_jid, \
                                      secret = self.secret, \
                                      server = self.server, \
                                      port = self.port, \
                                      db_connection_str = self.db_url, \
                                      lang = Lang(self.language))
            MailAccount.default_encoding = self.mail_default_encoding
            component.check_interval = self.check_interval
            component.run()
        self._run(run_func)
