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

from pyxmpp.jid import JID

from sqlobject.sqlbuilder import AND

import jcl.jabber as jabber
import jcl.model as model
from jcl.model import account
from jcl.model.account import Account, User, PresenceAccount
from jcl.jabber.disco import  \
     AccountTypeDiscoGetInfoHandler, AccountDiscoGetInfoHandler
from jcl.jabber.feeder import FeederComponent, Feeder, MessageSender, \
    HeadlineSender, FeederHandler
from jcl.jabber.command import CommandRootDiscoGetInfoHandler
from jcl.jabber.component import AccountManager

from jmc.jabber.disco import MailRootDiscoGetInfoHandler, \
     IMAPAccountDiscoGetItemsHandler, MailAccountTypeDiscoGetInfoHandler, \
     IMAPAccountDiscoGetInfoHandler
from jmc.jabber.message import SendMailMessageHandler, \
     RootSendMailMessageHandler
from jmc.jabber.presence import MailSubscribeHandler, \
     MailUnsubscribeHandler, MailPresenceHandler
from jmc.model.account import MailAccount, IMAPAccount, POP3Account, \
    SMTPAccount
from jmc.lang import Lang
from jmc.jabber.command import MailCommandManager

class MailAccountManager(AccountManager):
    def account_get_register(self, info_query,
                             name,
                             from_jid,
                             account_type,
                             lang_class):
        """Handle get_register on an IMAP account.
        Return a preinitialized form.
        account_type contains 'account_type + imap_dir'"""
        splitted_node = account_type.split("/")
        splitted_node_len = len(splitted_node)
        if splitted_node_len == 1 or \
            splitted_node[0] != "IMAP":
            return AccountManager.account_get_register(self,
                                                       info_query,
                                                       name, from_jid,
                                                       account_type,
                                                       lang_class)
        else:
            info_query = info_query.make_result_response()
            model.db_connect()
            imap_dir = "/".join(splitted_node[1:])
            bare_from_jid = from_jid.bare()
            _account = account.get_account_filter(\
                AND(AND(User.q.jid == unicode(bare_from_jid),
                        Account.q.userID == User.q.id),
                    IMAPAccount.q.mailbox == imap_dir),
                account_class=IMAPAccount)
            query = info_query.new_query("jabber:iq:register")
            if _account is not None:
                result = self.generate_registration_form_init(lang_class,
                                                              _account)
            else:
                _account = account.get_account(bare_from_jid, name,
                                               IMAPAccount)
                if _account is not None:
                    result = self.generate_registration_form_init(lang_class,
                                                                  _account)
                    result["name"].value = None
                    result["name"].type = "text-single"
                else:
                    result = self.generate_registration_form(\
                        lang_class,
                        IMAPAccount,
                        bare_from_jid)
                result["mailbox"].value = imap_dir
            result.as_xml(query)
            return [info_query]

class MailComponent(FeederComponent):
    """Jabber Mail Component main implementation"""

    def __init__(self,
                 jid,
                 secret,
                 server,
                 port,
                 config,
                 config_file,
                 lang=Lang(),
                 account_manager_class=MailAccountManager,
                 command_manager_class=MailCommandManager):
        """Use FeederComponent behavior and setup feeder and sender
        attributes.
        """
        FeederComponent.__init__(self,
                                 jid,
                                 secret,
                                 server,
                                 port,
                                 config,
                                 config_file,
                                 lang=lang,
                                 account_manager_class=account_manager_class,
                                 command_manager_class=command_manager_class)
        self.handler = MailFeederHandler(MailFeeder(self), MailSender(self))
        self.account_manager.account_classes = (IMAPAccount,
                                                POP3Account,
                                                SMTPAccount)
        self.msg_handlers += [[SendMailMessageHandler(self),
                               RootSendMailMessageHandler(self)]]
        self.presence_subscribe_handlers += [[MailSubscribeHandler(self)]]
        self.presence_unsubscribe_handlers += [[MailUnsubscribeHandler(self)]]
        self.presence_available_handlers += [[MailPresenceHandler(self)]]
        self.presence_unavailable_handlers += [[MailPresenceHandler(self)]]
        self.disco_get_items_handlers[0] += [IMAPAccountDiscoGetItemsHandler(self)]
        jabber.replace_handlers(self.disco_get_info_handlers,
                                CommandRootDiscoGetInfoHandler,
                                MailRootDiscoGetInfoHandler(self))
        jabber.replace_handlers(self.disco_get_info_handlers,
                                AccountTypeDiscoGetInfoHandler,
                                MailAccountTypeDiscoGetInfoHandler(self))
        jabber.replace_handlers(self.disco_get_info_handlers,
                                AccountDiscoGetInfoHandler,
                                IMAPAccountDiscoGetInfoHandler(self))

    def check_email_accounts(self, accounts, lang_class=None):
        if lang_class is None:
            lang_class = self.lang.get_default_lang_class()
        self.handler.handle(None, lang_class, accounts)

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
                            result.append((email_from,
                                           default_lang_class.new_mail_subject\
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
                            result.append((None,
                                           default_lang_class.new_digest_subject\
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

class MailSender(HeadlineSender):
    """Send emails messages to jabber users"""

    def send(self, to_account, data):
        """Call MessageSender send method"""
        MessageSender.send(self, to_account, data)
        
    def create_message(self, to_account, data):
        """Send given emails (in data) as Jabber messages"""
        email_from, subject, body = data
        if to_account.action == MailAccount.RETRIEVE:
            message = MessageSender.create_message(self, to_account,
                                                   (subject, body))
            msg_node = message.get_node()
            addresses_node = msg_node.newChild(None, "addresses", None)
            address_ns = addresses_node.newNs("http://jabber.org/protocol/address", None)
            addresses_node.setNs(address_ns)
            replyto_address_node = addresses_node.newChild(address_ns, "address", None)
            replyto_address_node.setProp("type", "replyto")
            replyto_jid = email_from.replace('@', '%', 1) + "@" \
                          + unicode(JID(to_account.jid).domain)
            replyto_address_node.setProp("jid", replyto_jid)
        elif to_account.action == MailAccount.DIGEST:
            message = HeadlineSender.create_message(self, to_account,
                                                    (subject, body))
        else:
            message = None
        return message

class MailFeederHandler(FeederHandler):
    def filter(self, stanza, lang_class):
        """Return only email account type to check mail from
        """
        accounts = account.get_all_accounts(account_class=MailAccount)
        return accounts
