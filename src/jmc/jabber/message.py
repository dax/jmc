##
## message.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Wed Jun 27 22:08:23 2007 David Rousselie
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

import logging
import re

from pyxmpp.message import Message

from jcl.model import account
from jmc.jabber import MailHandler
from jmc.model.account import SMTPAccount

class SendMailMessageHandler(MailHandler):
    def __init__(self, component):
        MailHandler.__init__(self, component)
        self.__logger = logging.getLogger(\
            "jmc.jabber.component.SendMailMessageHandler")

    def send_mail_result(self, message, lang_class, to_email):
        return [Message(from_jid=message.get_to(),
                        to_jid=message.get_from(),
                        subject=lang_class.send_mail_ok_subject,
                        body=lang_class.send_mail_ok_body % (to_email))]

    def handle(self, stanza, lang_class, data):
        message = stanza
        accounts = data
        to_node = message.get_to().node
        to_email = to_node.replace('%', '@', 1)
        accounts[0].send_email(\
            accounts[0].create_email(accounts[0].default_from,
                                     to_email,
                                     message.get_subject(),
                                     message.get_body()))
        return self.send_mail_result(message, lang_class, to_email)

class RootSendMailMessageHandler(SendMailMessageHandler):
    """Handle message sent to root JID"""

    def __init__(self, component):
        SendMailMessageHandler.__init__(self, component)
        self.to_regexp = re.compile("^\s*(to|TO|To)\s*:\s*(?P<to_email>.*)")
        self.__logger = logging.getLogger(\
            "jmc.jabber.component.RootSendMailMessageHandler")

    def filter(self, stanza, lang_class):
        bare_from_jid = unicode(stanza.get_from().bare())
        accounts = account.get_accounts(\
            bare_from_jid,
            account_class=SMTPAccount,
            filter=(SMTPAccount.q.default_account == True))
        if accounts.count() != 1:
            self.__logger.error("No default account found for user " +
                                str(bare_from_jid))
        if accounts.count() == 0:
            accounts = account.get_accounts(bare_from_jid,
                                            SMTPAccount)
        return accounts

    def handle(self, stanza, lang_class, data):
        message = stanza
        accounts = data
        to_email = None
        lines = message.get_body().split('\n')
        message_body = []
        while to_email is None \
                and lines:
            line = lines.pop(0)
            match = self.to_regexp.match(line)
            if match:
                to_email = match.group("to_email")
            else:
                message_body.append(line)
        message_body.extend(lines)
        if to_email is not None:
            accounts[0].send_email(\
                accounts[0].create_email(accounts[0].default_from,
                                         to_email,
                                         message.get_subject(),
                                         "\n".join(message_body)))
            return self.send_mail_result(message, lang_class, to_email)
        else:
            return [Message(from_jid=message.get_to(),
                            to_jid=message.get_from(),
                            stanza_type="error",
                            subject=lang_class.send_mail_error_no_to_header_subject,
                            body=lang_class.send_mail_error_no_to_header_body)]

