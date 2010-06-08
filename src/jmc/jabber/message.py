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
from jmc.model.account import AbstractSMTPAccount

class SendMailMessageHandler(MailHandler):
    def __init__(self, component):
        MailHandler.__init__(self, component)
        self.__logger = logging.getLogger(\
            "jmc.jabber.component.SendMailMessageHandler")
        self.to_regexp = re.compile("^\s*(?i)to\s*:\s*(?P<to_email>.*)")
        self.cc_regexp = re.compile("^\s*(?i)cc\s*:\s*(?P<cc_email>.*)")
        self.bcc_regexp = re.compile("^\s*(?i)bcc\s*:\s*(?P<bcc_email>.*)")
        self.subject_regexp = re.compile("^\s*(?i)subject\s*:\s*(?P<subject_email>.*)")

    def send_mail_result(self, message, lang_class, to_email):
        return [Message(from_jid=message.get_to(),
                        to_jid=message.get_from(),
                        subject=lang_class.send_mail_ok_subject,
                        body=lang_class.send_mail_ok_body % (to_email))]

    def get_email_headers_from_message(self, text, regexps, groups):
        """
        This method extract line from message body with given regexps
        and associated matching groups names.
        If a line match a regexp, this line is removed from the returned message
        and matching group is extracted and returned in 'headers'.
        """
        headers = []
        for i in xrange(len(regexps)):
            headers.append(None)
        lines = text.split('\n')
        message_body = []
        regexps_len = len(regexps)
        matched = 0
        while matched < regexps_len \
                and lines:
            line = lines.pop(0)
            has_matched = False
            i = 0
            while i < regexps_len \
                    and not has_matched:
                if regexps[i] is not None:
                    match = regexps[i].match(line)
                    if match:
                        headers[i] = match.group(groups[i])
                        regexps[i] = None
                        has_matched = True
                i += 1
            if has_matched:
                matched += 1
            else:
                message_body.append(line)
        message_body.extend(lines)
        return ("\n".join(message_body), headers)

    def handle(self, stanza, lang_class, data):
        message = stanza
        if message.get_body() is None or message.get_body() == "":
            return []
        accounts = data
        to_node = message.get_to().node
        to_email = to_node.replace('%', '@', 1)
        (message_body,
         (more_to_email,
          subject,
          cc_email,
          bcc_email)) = self.get_email_headers_from_message(\
            message.get_body(),
            [self.to_regexp,
             self.subject_regexp,
             self.cc_regexp,
             self.bcc_regexp],
            ["to_email",
             "subject_email",
             "cc_email",
             "bcc_email"])
        other_headers = {}
        other_headers["Cc"] = cc_email
        other_headers["Bcc"] = bcc_email
        message_subject = message.get_subject()
        if message_subject is not None \
                and len(message_subject) > 0:
            subject = message_subject
        if more_to_email is not None:
            to_email += ", " + more_to_email
        accounts[0].send_email(\
            accounts[0].create_email(accounts[0].default_from,
                                     to_email,
                                     message.get_subject(),
                                     message_body,
                                     other_headers))
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
            account_class=AbstractSMTPAccount,
            filter=(AbstractSMTPAccount.q.default_account == True))
        if accounts.count() != 1:
            self.__logger.error("No default account found for user " +
                                str(bare_from_jid))
        if accounts.count() == 0:
            accounts = account.get_accounts(bare_from_jid,
                                            AbstractSMTPAccount)
        return accounts

    def handle(self, stanza, lang_class, data):
        message = stanza
        if message.get_body() is None or message.get_body() == "":
            return []
        accounts = data
        (message_body,
         (to_email,
          subject,
          cc_email,
          bcc_email)) = self.get_email_headers_from_message(\
            message.get_body(),
            [self.to_regexp,
             self.subject_regexp,
             self.cc_regexp,
             self.bcc_regexp],
            ["to_email",
             "subject_email",
             "cc_email",
             "bcc_email"])
        other_headers = {}
        other_headers["Cc"] = cc_email
        other_headers["Bcc"] = bcc_email
        message_subject = message.get_subject()
        if message_subject is not None \
                and len(message_subject) > 0:
            subject = message_subject
        if to_email is not None:
            accounts[0].send_email(\
                accounts[0].create_email(accounts[0].default_from,
                                         to_email,
                                         subject,
                                         message_body,
                                         other_headers))
            return self.send_mail_result(message, lang_class, to_email)
        else:
            return [Message(from_jid=message.get_to(),
                            to_jid=message.get_from(),
                            stanza_type="error",
                            subject=lang_class.send_mail_error_no_to_header_subject,
                            body=lang_class.send_mail_error_no_to_header_body)]
