# -*- coding: utf-8 -*-
##
## feeder.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Wed Mar  5 19:15:04:42 2008 David Rousselie
## $Id$
## 
## Copyright (C) 2006 David Rousselie
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

"""
FeederComponent with JMC Feeder and Sender implementation
"""

__revision__ = "$Id: feeder.py,v 1.1 2008/03/05 20:24:07 dax Exp $"

import logging

from pyxmpp.jid import JID

from jcl.model.account import PresenceAccount
from jcl.jabber.feeder import Feeder, MessageSender, \
    HeadlineSender, FeederHandler
from jcl.model import account

from jmc.model.account import MailAccount

class MailFeeder(Feeder):
    """Email check"""

    def __init__(self, component):
        """MailFeeder constructor"""
        Feeder.__init__(self, component)
        self.__logger = logging.getLogger("jmc.jabber.component.MailFeeder")

    def initialize_live_email(self, _account):
        """For live email checking account, mark emails received while
        offline as read.
        Return a boolean to continue mail checking or not
        (if waiting for password).
        """
        if _account.password is None:
            if not _account.waiting_password_reply:
                account_manager = self.component.account_manager
                self.component.send_stanzas(\
                    account_manager.ask_password(_account,
                                                 _account.default_lang_class))
            return False
        try:
            _account.connect()
            _account.mark_all_as_read()
            _account.disconnect()
            _account.first_check = False
            _account.error = None
            return True
        except Exception, e:
            if _account.connected:
                try:
                    _account.disconnect()
                except:
                    # We have done everything we could
                    _account.connected = False
            self.component.send_error(_account, e)
            return False

    def feed(self, _account):
        """Check for new emails for given MailAccount and return a list of
        those emails or a summary.
        """
        self.__logger.debug("MailFeeder.feed")
        result = []
        if _account.first_check and _account.live_email_only:
            continue_checking = self.initialize_live_email(_account)
            if not continue_checking:
                return result
        _account.lastcheck += 1
        if _account.lastcheck == _account.interval:
            _account.lastcheck = 0
            action = _account.action
            if action != PresenceAccount.DO_NOTHING:
                try:
                    if _account.password is None:
                        account_manager = self.component.account_manager
                        self.component.send_stanzas(\
                            account_manager.ask_password(_account,
                                                         _account.default_lang_class))
                        return result
                    self.__logger.debug("Checking " + _account.name)
                    self.__logger.debug("\t" + _account.login \
                                            + "@" + _account.host)
                    _account.connect()
                    mail_list = _account.get_new_mail_list()
                    default_lang_class = _account.default_lang_class
                    if action == MailAccount.RETRIEVE:
                        for mail_index in _account.get_next_mail_index(mail_list):
                            (body, email_from) = _account.get_mail(mail_index)
                            result.append((email_from,
                                           default_lang_class.new_mail_subject\
                                               % (email_from),
                                           body))
                    elif action == MailAccount.DIGEST:
                        body = ""
                        new_mail_count = 0
                        for mail_index in _account.get_next_mail_index(mail_list):
                            (tmp_body, from_email) = \
                                       _account.get_mail_summary(mail_index)
                            body += tmp_body
                            body += "\n----------------------------------\n"
                            new_mail_count += 1
                        if body != "":
                            result.append((None,
                                           default_lang_class.new_digest_subject\
                                               % (new_mail_count),
                                           body))
                    else:
                        raise Exception("Unkown action: " + str(action) \
                                            + "\nPlease reconfigure account.")
                    _account.disconnect()
                    _account.error = None
                    self.__logger.debug("\nCHECK_MAIL ends " + _account.jid)
                except Exception, e:
                    if _account.connected:
                        try:
                            _account.disconnect()
                        except:
                            # We have done everything we could
                            _account.connected = False
                    self.component.send_error(_account, e)
        return result

class MailSender(HeadlineSender):
    """Send emails messages to jabber users"""

    def create_full_email_message(self, email_from, email_subject,
                                  email_body, to_account):
        """
        Create a jabber message with email data and XEP-0033 addresses
        """
        message = MessageSender.create_message(self, to_account,
                                               (email_subject, email_body))
        msg_node = message.get_node()
        addresses_node = msg_node.newChild(None, "addresses", None)
        address_ns = addresses_node.newNs("http://jabber.org/protocol/address",
                                          None)
        addresses_node.setNs(address_ns)
        replyto_address_node = addresses_node.newChild(address_ns, "address",
                                                       None)
        replyto_address_node.setProp("type", "replyto")
        replyto_jid = email_from.replace('@', '%', 1) + "@" \
            + unicode(JID(to_account.jid).domain)
        replyto_address_node.setProp("jid", replyto_jid)
        return message
        
    def create_message(self, to_account, data):
        """Send given emails (in data) as Jabber messages"""
        email_from, subject, body = data
        if to_account.action == MailAccount.RETRIEVE:
            message = self.create_full_email_message(email_from, subject, body,
                                                     to_account)
        elif to_account.action == MailAccount.DIGEST:
            message = HeadlineSender.create_message(self, to_account,
                                                    (subject, body))
        else:
            message = None
        return message

class MailFeederHandler(FeederHandler):
    def filter(self, stanza, lang_class):
        """
        Return only email account type to check mail from
        """
        accounts = account.get_all_accounts(account_class=MailAccount)
        return accounts
