# -*- coding: utf-8 -*-
##
## component.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Fri Jan  7 11:06:42 2005
## $Id: component.py,v 1.12 2005/09/18 20:24:07 dax Exp $
##
## Copyright (C) 2005
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
import sys

from sqlobject import *

from pyxmpp.message import Message

from jcl.model.account import Account, PresenceAccount
from jcl.jabber.component import Handler, DefaultSubscribeHandler, \
    DefaultUnsubscribeHandler, DefaultPresenceHandler
from jcl.jabber.feeder import FeederComponent, Feeder, MessageSender, \
    HeadlineSender, FeederHandler

from jmc.model.account import MailAccount, IMAPAccount, POP3Account, \
    SMTPAccount
from jmc.lang import Lang

class NoAccountError(Exception):
    """Error raised when no corresponding account is found."""
    pass

class MailComponent(FeederComponent):
    """Jabber Mail Component main implementation"""

    def __init__(self,
                 jid,
                 secret,
                 server,
                 port,
                 db_connection_str,
                 lang = Lang()):
        """Use FeederComponent behavior and setup feeder and sender
        attributes.
        """
        FeederComponent.__init__(self,
                                 jid,
                                 secret,
                                 server,
                                 port,
                                 db_connection_str,
                                 lang=lang)
        self.handler = MailFeederHandler(MailFeeder(self), MailSender(self))
        self.account_manager.account_classes = (IMAPAccount,
                                                POP3Account,
                                                SMTPAccount)
        self.msg_handlers += [SendMailMessageHandler(),
                              RootSendMailMessageHandler()]
        self.subscribe_handlers += [MailSubscribeHandler()]
        self.unsubscribe_handlers += [MailUnsubscribeHandler()]
        self.available_handlers += [DefaultPresenceHandler()]
        self.unavailable_handlers += [DefaultPresenceHandler()]

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
            _account.in_error = False
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
                    mail_list = _account.get_mail_list()
                    default_lang_class = _account.default_lang_class
                    if action == MailAccount.RETRIEVE:
                        # TODO : use generator (yield)
                        mail_index = _account.get_next_mail_index(mail_list)
                        while mail_index is not None:
                            (body, email_from) = _account.get_mail(mail_index)
                            result.append((default_lang_class.new_mail_subject\
                                               % (email_from),
                                           body))
                            mail_index = _account.get_next_mail_index(mail_list)
                    elif action == MailAccount.DIGEST:
                        body = ""
                        new_mail_count = 0
                        mail_index = _account.get_next_mail_index(mail_list)
                        while mail_index is not None:
                            (tmp_body, from_email) = \
                                       _account.get_mail_summary(mail_index)
                            body += tmp_body
                            body += "\n----------------------------------\n"
                            mail_index = _account.get_next_mail_index(mail_list)
                            new_mail_count += 1
                        if body != "":
                            result.append((default_lang_class.new_digest_subject\
                                               % (new_mail_count),
                                           body))
                    else:
                        raise Exception("Unkown action: " + str(action) \
                                            + "\nPlease reconfigure account.")
                    _account.disconnect()
                    _account.in_error = False
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

class MailSender(MessageSender, HeadlineSender):
    """Send emails messages to jabber users"""

    def send(self, to_account, subject, body):
        """Send given emails (in data) as Jabber messages"""
        if to_account.action == MailAccount.RETRIEVE:
            MessageSender.send(self, to_account, subject, body)
        elif to_account.action == MailAccount.DIGEST:
            HeadlineSender.send(self, to_account, subject, body)

class MailHandler(Handler):
    """Define filter for email address in JID"""

    def __init__(self):
        Handler.__init__(self)
        self.dest_jid_regexp = re.compile(".*%.*")

    def filter(self, stanza, lang_class):
        """Return empty array if JID match '.*%.*@componentJID'"""
        if self.dest_jid_regexp.match(stanza.get_to().node):
            bare_from_jid = unicode(stanza.get_from().bare())
            accounts = Account.select(Account.q.user_jid == bare_from_jid)
            if accounts.count() == 0:
                raise NoAccountError()
            else:
                default_account = accounts.newClause(\
                    SMTPAccount.q.default_account == True)
                if default_account.count() > 0:
                    return default_account
                else:
                    return accounts
        return None

class SendMailMessageHandler(MailHandler):
    def __init__(self):
        MailHandler.__init__(self)
        self.__logger = logging.getLogger(\
            "jmc.jabber.component.SendMailMessageHandler")

    def send_mail_result(self, message, lang_class, to_email):
        return [Message(from_jid=message.get_to(),
                        to_jid=message.get_from(),
                        subject=lang_class.send_mail_ok_subject,
                        body=lang_class.send_mail_ok_body % (to_email))]

    def handle(self, message, lang_class, accounts):
        to_node = message.get_to().node
        to_email = to_node.replace('%', '@', 1)
        accounts[0].send_email(to_email,
                               message.get_subject(),
                               message.get_body())
        return self.send_mail_result(message, lang_class, to_email)

class RootSendMailMessageHandler(SendMailMessageHandler):
    def __init__(self):
        SendMailMessageHandler.__init__(self)
        self.to_regexp = re.compile("^\s*(to|TO)\s*:\s*(?P<to_email>.*)")
        self.__logger = logging.getLogger(\
            "jmc.jabber.component.RootSendMailMessageHandler")

    def filter(self, message, lang_class):
        name = message.get_to().node
        bare_from_jid = unicode(message.get_from().bare())
        accounts = Account.select(\
            AND(Account.q.name == name,
                Account.q.user_jid == bare_from_jid))
        if accounts.count() != 1:
            self.__logger.error("Account " + name + " for user " + \
                                    bare_from_jid + " must be uniq")
        return accounts

    def handle(self, message, lang_class, accounts):
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
            accounts[0].send_email(to_email, message.get_subject(),
                                   "\n".join(message_body))
            return self.send_mail_result(message, lang_class, to_email)
        else:
            return [Message(from_jid=message.get_to(),
                            to_jid=message.get_from(),
                            stanza_type="error",
                            subject=lang_class.send_mail_error_no_to_header_subject,
                            body=lang_class.send_mail_error_no_to_header_body)]

class MailSubscribeHandler(DefaultSubscribeHandler, MailHandler):
    """Use DefaultSubscribeHandler handle method and MailHandler filter"""

    def __init__(self):
        DefaultSubscribeHandler.__init__(self)
        MailHandler.__init__(self)

    def filter(self, stanza, lang_class):
        return MailHandler.filter(self, stanza, lang_class)

    def handle(self, stanza, lang_class, accounts):
        return DefaultSubscribeHandler.handle(self, stanza, lang_class, accounts)

class MailUnsubscribeHandler(DefaultUnsubscribeHandler, MailHandler):
    """Use DefaultUnsubscribeHandler handle method and MailHandler filter"""

    def __init__(self):
        DefaultUnsubscribeHandler.__init__(self)
        MailHandler.__init__(self)

    def filter(self, stanza, lang_class):
        return MailHandler.filter(self, stanza, lang_class)

    def handle(self, stanza, lang_class, accounts):
        return DefaultUnsubscribeHandler.handle(self, stanza, lang_class, accounts)

class MailFeederHandler(FeederHandler):
    def filter(self, stanza, lang_class):
        """Return only email account type to check mail from
        """
        accounts = MailAccount.select(orderBy="user_jid")
        return accounts
