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

import socket

from jcl.runner import JCLRunner

import jmc.model.account as account
from jmc.model.account import MailAccount, IMAPAccount, POP3Account, \
    AbstractSMTPAccount, GlobalSMTPAccount, SMTPAccount
from jmc.jabber.component import MailComponent
from jmc.lang import Lang

from sqlobject import *

class JMCRunner(JCLRunner):

    def __init__(self, component_name, component_version):
        JCLRunner.__init__(self, component_name, component_version)
        self.component_short_name = "JMC"
        # define new options
        self.mail_default_encoding = "iso-8859-1"
        self.smtp_default_login = None
        self.smtp_default_password = None
        self.smtp_default_host = None
        self.smtp_default_port = 0
        self.smtp_default_tls = False
        self.smtp_default_label = None
        self.enable_smtp_default_account = False
        self.options += [("e:", "mail-default-encoding=", "jmc",
                          " ENCODING\t\tDefault encoding of the component",
                          lambda arg: self.set_attr("mail_default_encoding",
                                                    arg)),
                         ("g:", "smtp-default-login=", "smtp",
                          " LOGIN\t\t\tDefault SMTP login",
                          lambda arg: self.set_attr("smtp_default_login", arg)),
                         ("a:", "smtp-default-password=", "smtp",
                          " PASSWORD\t\tDefault SMTP password",
                          lambda arg: self.set_attr("smtp_default_password",
                                                    arg)),
                         ("t:", "smtp-default-host=", "smtp",
                          " HOST\t\t\tDefault SMTP host",
                          lambda arg: self.set_attr("smtp_default_host", arg)),
                         ("r:", "smtp-default-port=", "smtp",
                          " PORT\t\t\tDefault SMTP port",
                          lambda arg: self.set_attr("smtp_default_port",
                                                    int(arg))),
                         ("m:", "smtp-default-tls=", "smtp",
                          " True/False\t\tDefault SMTP TLS connexion",
                          lambda arg: self.set_attr("smtp_default_tls",
                                                    arg.lower() == "true" \
                                                        or arg == "1")),
                         ("n:", "enable-smtp-default-account=", "smtp",
                          " True/False\t\tEnable default SMTP connexion",
                          lambda arg: self.set_attr("enable_smtp_default_account",
                                                    arg.lower() == "true" \
                                                        or arg == "1")),
                         ("b:", "smtp-default-label=", "smtp",
                          "\t\t\tDefault SMTP account label",
                          lambda arg: self.set_attr("smtp_default_label",
                                                    arg))]
        # override JCL default
        self.service_jid = "jmc.localhost"
        self.db_url = "sqlite:///var/spool/jabber/jmc.db"
        self.pid_file = "/var/run/jabber/jmc.pid"
        self.config_file = "jmc.conf"
        # set socket connection timeout (for IMAP and POP connections)
        socket.setdefaulttimeout(10)

    def setup_db(self):
        JCLRunner.setup_db(self)
        MailAccount.createTable(ifNotExists=True)
        IMAPAccount.createTable(ifNotExists=True)
        POP3Account.createTable(ifNotExists=True)
        AbstractSMTPAccount.createTable(ifNotExists=True)
        GlobalSMTPAccount.createTable(ifNotExists=True)
        SMTPAccount.createTable(ifNotExists=True)

    def setup_smtp_default(self):
        """Replace default values for GlobalSMTPAccount"""
        if self.smtp_default_login:
            account.smtp_default_login = self.smtp_default_login
        if self.smtp_default_password:
            account.smtp_default_password = self.smtp_default_password
        if self.smtp_default_host:
            account.smtp_default_host = self.smtp_default_host
        if self.smtp_default_port:
            account.smtp_default_port = self.smtp_default_port
        if self.smtp_default_tls:
            account.smtp_default_tls = self.smtp_default_tls
        if self.smtp_default_label:
            Lang().get_default_lang_class().type_globalsmtp_name = \
                self.smtp_default_label

    def run(self):
        def run_func():
            component = MailComponent(jid=self.service_jid,
                                      secret=self.secret,
                                      server=self.server,
                                      port=self.port,
                                      lang=Lang(self.language),
                                      config=self.config,
                                      config_file=self.config_file)
            component.version = self.component_version
            if self.enable_smtp_default_account:
                component.account_manager.account_classes += (GlobalSMTPAccount,)
            MailAccount.default_encoding = self.mail_default_encoding
            component.disco_identity.set_category("gateway")
            component.disco_identity.set_type("smtp")
            return component.run()
        self.setup_smtp_default()
        self._run(run_func)

def main():
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    del sys.setdefaultencoding
    import jmc
    from jmc.lang import Lang
    runner = JMCRunner(Lang().get_default_lang_class().component_name,
                       jmc.version)
    runner.configure()
    runner.run()

if __name__ == "__main__":
    main()
